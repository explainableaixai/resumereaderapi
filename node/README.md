# resumereaderapi for Node.js

Turn a resume into clean JSON. Send text, a file on disk or a link, and receive a candidate object with 114 fields: contact details, work history, education, skills, career analytics and more. The same client normalizes job titles, skills and locations.

No runtime dependencies. Node 14 or newer. Types included.

## Install

```bash
npm install resumereaderapi
```

Get a key from a plan on the [resume parsing API](https://www.resumereaderapi.com/api-v2.php) site. One credit parses one resume of up to ten pages.

## Parse a file

```js
const ResumeReader = require('resumereaderapi');

const rr = new ResumeReader(process.env.RESUME_KEY);
const { resume } = await rr.parseFile('./candidates/laura.pdf');

console.log(resume.contact.full_name);
console.log(resume.career.seniority_level, resume.career.total_experience_years);
console.log(resume.work_experience.map((w) => `${w.title} @ ${w.company}`));
```

The client sends `schema_version: 2` by default, so you get the full 114 field object. Pass `{ schemaVersion: 1 }` to the constructor for the compact legacy shape.

## Three ways to hand over a resume

| Method | Input |
|---|---|
| `parseText(text, opts)` | plain UTF-8 text |
| `parseFile(path, opts)` | PDF, DOCX, TXT, RTF, HTML, ODT, XLSX, XLS, PNG, JPG, scanned PDF |
| `parseUrl(url, opts)` | an https link the service downloads for you |

Files up to 10 MB are accepted. Scans go through character recognition automatically.

## Options

```js
await rr.parseFile(path, {
  fieldNames: 'fr',          // French JSON keys
  excludeSensitive: true,    // leave GDPR sensitive fields out entirely
  anonymize: true,           // placeholders for names, emails, phones
  maxPages: 5,
  sections: ['contact', 'skills'],
  language: 'de',
});
```

Combine `excludeSensitive` with `anonymize` for a screening flow that contains no direct identifiers.

## Normalizers

```js
const titles = await rr.normalizeTitles(['Sr. SWE II', 'Growth Ninja']);
// titles.results[0] -> { normalized_title: 'Senior Software Engineer', seniority_level: 'senior', job_function: 'engineering', ... }

const skills = await rr.normalizeSkills(['JS', 'Python 3.11', 'K8s']);
const places = await rr.normalizeLocations(['NYC', 'München', 'Remote (Germany)']);
```

Lists longer than 100 are split into batches for you and the credit total is summed. Each item costs a tenth of a credit. Read more on [job title normalization](https://www.resumereaderapi.com/normalization/job-titles.php), including the seniority list.

## Errors

The HTTP status is always 200. The client reads `status` from the body and throws `ResumeReaderError`.

| Status | Cause |
|---|---|
| 400 | no input, bad file, or a batch over 100 |
| 401 | wrong key |
| 402 | not enough credits, nothing billed |
| 413 | over 20 pages, about 30,000 tokens or 10 MB |
| 422 | no readable text in the file |
| 429 | 30 requests per 60 seconds per IP |

```js
try {
  await rr.parseFile(file);
} catch (e) {
  if (e.status === 429) await new Promise((r) => setTimeout(r, 2000));
  else if (e.status === 422) console.warn('unreadable file', file);
  else throw e;
}
```

## Example: parse a whole folder

```js
const fs = require('fs/promises');
const path = require('path');

const dir = './inbox';
const files = (await fs.readdir(dir)).filter((f) => /\.(pdf|docx)$/i.test(f));

for (const f of files) {
  try {
    const { resume } = await rr.parseFile(path.join(dir, f));
    await fs.writeFile(`./out/${f}.json`, JSON.stringify(resume, null, 2));
  } catch (e) {
    console.error(f, e.message);
  }
}
```

Mind the rate limit: add a short pause if you run more than about 30 files a minute from one IP.

## Example: shortlist by experience

```js
const { resume } = await rr.parseText(cvText);
const ok = resume.career.total_experience_years >= 5
  && resume.skills.technical.includes('SQL')
  && !resume.career.employment_gaps.length;
```

Missing facts come back as `null` or `[]`, never invented, so checks like these stay honest.

## FAQ

### Is anything stored?
Documents are processed in memory for the request and are not retained.

### How many languages work?
Resumes in many languages parse. Add `language` as a hint for non-English files.

### What does a long document cost?
Up to 10 pages is one credit; 11 to 20 pages is two.

### Where is the pricing?
On the [plans page](https://www.resumereaderapi.com/pricing.php).

MIT license. info@alpha-quantum.com
