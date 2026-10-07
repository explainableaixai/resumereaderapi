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

<!--expanded-->
## What a parsed resume looks like

The value of a resume parser is not that it reads a PDF. It is that every resume, whatever its layout, comes out as the same shape. The v2 schema has 114 fields, and every key is always present. When a document has no evidence for a field, the value is `null` for scalars and objects and `[]` for arrays. Nothing is invented. That rule is what lets you write queries against the result without a defensive check on every line.

The record is organised into sections.

- **contact**: name, email addresses, phone numbers, a structured address, profile links, driving licences, and a handful of identity fields that are treated as sensitive.
- **profile**: summary, objective, desired role, availability, notice period, willingness to relocate or travel.
- **career**: current position, total experience in years, management experience, a seniority level, a progression label, average tenure and a list of employment gaps.
- **work_experience**: one entry per job with the title as written, a normalized title, company, industry, employment type, dates, duration in months, achievements and technologies.
- **education**: degree, field, institution, years, grade.
- **skills**: technical skills, tools, soft skills and a detailed list with years and level.
- **esco**: a best effort alignment of the occupation and the skills to the European ESCO taxonomy, left null when uncertain.

The computed career fields are worth a closer look. `average_tenure_months` and `employment_gaps` are not things a candidate writes down. They are derived from the dates, which means a recruiter can filter for stable careers or for recent gaps without reading a single document.

## Files, pages and limits

The service accepts more than eight kinds of input: PDF, DOCX, TXT, RTF, HTML, ODT, XLSX and XLS, plus images and scanned documents such as PNG, JPG and image only PDFs. Scans pass through character recognition automatically, so a photographed CV and a Word file arrive in the same shape.

The limits are simple.

| Limit | Value |
|---|---|
| File size | 10 MB |
| Pages per document | 20 |
| Size of one call | about 30,000 tokens |
| Rate | 30 requests per 60 seconds per IP |

One credit parses a resume of up to ten pages. A document of eleven to twenty pages costs two. A call that fails the caps or the credit check bills nothing. For ordinary resumes the number of credits equals the number of parsed resumes.

## Designing a reliable upload flow

A good upload flow assumes that some files will be bad. Put the checks in the right order.

1. Check the extension and size in the browser before upload.
2. Check them again on your server, because browsers can be bypassed.
3. Call the parser with a timeout and a cancellation path.
4. Map status codes to messages a candidate can act on. 422 means the file had no readable content, so ask for another format. 413 means the document is too long. 402 is your problem, not theirs, so alert your team and show a neutral message.
5. Store the original file and the parsed JSON together, so you can re-parse later if you change options.

Do not parse in the request that the candidate is waiting on if you can avoid it. Accept the upload, enqueue a job, and let the profile appear a few seconds later. Candidates forgive a short wait. They do not forgive an error page.

## Using the output for ranking

Parsed data supports fair, repeatable ranking. A few examples of filters you can write the day you have structured records:

- senior or lead seniority with at least five years of experience
- a named technology in the technical skills list
- no employment gap longer than six months in the last five years
- a location in a given country, using the address block
- a degree level at or above a threshold, using the numeric education level

Keep the filters visible. A hiring team should be able to see why a candidate was shortlisted. That visibility is easier when each rule reads a named field.

## Privacy by design

Nine fields carry special weight under data protection law, among them date of birth, gender, nationality, marital status, work permit and desired salary. They are extracted only when the document states them explicitly, never inferred from a name or a photo. Set `excludeSensitive` to skip them entirely, and set `anonymize` to replace identifiers with placeholders. Combined, the two options produce a record with no direct identifiers and no sensitive values.

Documents are processed in memory for the duration of the request. They are not retained. If you store the parsed JSON yourself, you become responsible for that data, so apply your retention policy to it. The European Commission publishes guidance on data protection principles that is a good starting point for the policy side; the link is in the further reading section below.

## How this fits with other data work

Resume data rarely lives alone. Candidate locations, titles and skills feed dashboards that also include market data, and the same teams sometimes work with audience data for employer branding campaigns. The [audience demographics for websites](https://www.cookielessaudiences.com/features/website-audience-demographics.php) guide shows how a different service describes who reads a page, which is a useful reference when you plan where to advertise open roles.

Corporate development teams that buy staffing and recruiting companies use a different kind of screening. The page on [acquisition sourcing for search funds](https://www.acquisitionuniverse.com/for/search-funds.php) explains how a buyer maps every independent company in a vertical, which is the same job a staffing investor faces when sizing an acquisition market.

## Troubleshooting

**Status 401 on every call.** The key is wrong. Copy it again from the dashboard and check for whitespace.

**Status 429.** You exceeded 30 requests in 60 seconds from one IP. Slow down, or spread work across workers with a shared limiter.

**Empty `skills` on a long document.** The document may have exceeded the page cap. Use `maxPages` to choose which pages count, or split the file.

**Dates look odd.** Work history dates use `YYYY-MM`, and a current role has `end_date` of `present`.

**Names appear as placeholders.** You set `anonymize`. Remove it if you need real values.

**Text only files lose structure.** A plain text CV has fewer layout cues. Prefer the original PDF or DOCX when you have it.

## Version notes

Version 1.0.0 targets schema version 2 by default. The older compact schema is still available through the constructor option. The client has no runtime dependencies, so upgrading is a matter of changing one line in your manifest.

<!--further-->
## Further reading

For the Node platform details the client relies on, the [Node.js documentation](https://nodejs.org/en) covers the HTTPS module and timeouts. For the occupation and skills framework behind the `esco` block of the response, the [European Skills, Competences, Qualifications and Occupations portal](https://esco.ec.europa.eu/en) explains the taxonomy and how its codes are structured.

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
