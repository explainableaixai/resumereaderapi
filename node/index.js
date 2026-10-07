'use strict';
const https = require('https');
const fs = require('fs');
const path = require('path');

const VERSION = '1.0.0';
const HOST = 'www.resumereaderapi.com';

const STATUS_TEXT = {
  400: 'Missing or invalid input',
  401: 'Invalid API key',
  402: 'Insufficient credits, nothing was billed',
  413: 'Document beyond 20 pages, about 30,000 tokens or 10 MB, nothing was billed',
  422: 'File could not be read as a resume',
  429: 'Rate limit exceeded, 30 requests per 60 seconds per IP',
};

class ResumeReaderError extends Error {
  constructor(status, message, body) {
    super(`[${status}] ${message}`);
    this.name = 'ResumeReaderError';
    this.status = status;
    this.body = body;
  }
}

function post(endpoint, payload, timeout) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const req = https.request({
      host: HOST,
      path: `/api/${endpoint}`,
      method: 'POST',
      timeout,
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'User-Agent': `resumereaderapi-node/${VERSION} (+https://www.resumereaderapi.com)`,
      },
    }, (res) => {
      let data = '';
      res.setEncoding('utf8');
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        let json;
        try { json = JSON.parse(data); } catch (e) {
          return reject(new ResumeReaderError(res.statusCode, 'Response was not JSON', data));
        }
        // HTTP status is always 200, the application status lives in the body
        if (typeof json.status === 'number' && json.status !== 200) {
          return reject(new ResumeReaderError(json.status, STATUS_TEXT[json.status] || json.message || 'API error', json));
        }
        resolve(json);
      });
    });
    req.on('timeout', () => req.destroy(new ResumeReaderError(0, 'Request timed out')));
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

class ResumeReader {
  constructor(apiKey, options = {}) {
    if (!apiKey) throw new Error('An API key is required');
    this.apiKey = apiKey;
    this.timeout = options.timeout || 120000;
    this.schemaVersion = options.schemaVersion || 2;
  }

  _parse(source, options) {
    const payload = { api_key: this.apiKey, schema_version: this.schemaVersion, ...source };
    if (options.fieldNames) payload.field_names = options.fieldNames;
    if (options.excludeSensitive) payload.exclude_sensitive = true;
    if (options.anonymize) payload.anonymize = true;
    if (options.maxPages) payload.max_pages = options.maxPages;
    if (options.sections) payload.sections = options.sections;
    if (options.language) payload.language = options.language;
    return post('parse.php', payload, this.timeout);
  }

  /** Parse resume text. */
  parseText(text, options = {}) { return this._parse({ text }, options); }

  /** Parse a local file (PDF, DOCX, TXT, RTF, HTML, ODT, XLSX/XLS, PNG, JPG). */
  async parseFile(filePath, options = {}) {
    const data = await fs.promises.readFile(filePath);
    return this._parse({ file_base64: data.toString('base64'), filename: path.basename(filePath) }, options);
  }

  /** Parse a resume the API fetches from an https URL. */
  parseUrl(fileUrl, options = {}) { return this._parse({ file_url: fileUrl }, options); }

  /** Normalize job titles, skills or locations, batched in groups of 100. */
  normalizeTitles(titles) { return this._normalize('normalize_title.php', 'titles', titles); }
  normalizeSkills(skills) { return this._normalize('normalize_skills.php', 'skills', skills); }
  normalizeLocations(locations) { return this._normalize('normalize_locations.php', 'locations', locations); }

  async _normalize(endpoint, key, items) {
    const list = Array.isArray(items) ? items : [items];
    const results = [];
    let used = 0;
    let remaining;
    for (let i = 0; i < list.length; i += 100) {
      const res = await post(endpoint, { api_key: this.apiKey, [key]: list.slice(i, i + 100) }, this.timeout);
      results.push(...(res.results || []));
      used += res.credits_used || 0;
      remaining = res.remaining_credits;
    }
    return { results, credits_used: used, remaining_credits: remaining };
  }
}

module.exports = ResumeReader;
module.exports.ResumeReader = ResumeReader;
module.exports.ResumeReaderError = ResumeReaderError;
