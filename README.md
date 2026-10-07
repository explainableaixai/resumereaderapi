# Resume Reader API: clients and schema notes

Open client code for [Resume Reader API](https://www.resumereaderapi.com), a service that converts resumes into structured JSON. This repository keeps the Node.js and Python clients together with notes on the response schema.

Other languages are in separate repositories named `resumereaderapi-go`, `resumereaderapi-dart` and `resumereaderapi-rust`.

## In one sentence

You send a CV in nearly any format and receive a 114 field candidate record where unknown values are empty, never made up.

## Repository map

| Folder | Contents |
|---|---|
| `node/` | the npm package |
| `python/` | the PyPI package |
| `examples/` | scripts for common jobs |
| `schema/` | one page of schema notes |

## Schema sections

The v2 record has these top level groups:

- `contact`: name, emails, phones, address, profile links, sensitive identity fields
- `profile`: summary, objective, desired role, availability, notice period
- `career`: current position, total and management experience, seniority, progression, tenure, gaps
- `work_experience[]`: title, normalized title, company, dates, achievements, technologies
- `education[]`: degree, field, institution, years, grade
- `skills`: technical, tools, soft, detailed with years and level
- plus an `esco` block that aligns occupation and skills to the European ESCO taxonomy, references, military service and security clearance

If a section has no evidence in the document its value is `null` or `[]`.

## Why people parse resumes

The point of parsing is to get from a pile of files to something sortable. Once candidates are rows, you can filter by experience, group by seniority, and spot employment gaps in one query.

Some places this pays off right away:

- agencies searching their own back catalogue
- internal talent teams listing skills by department, as in [internal mobility](https://www.resumereaderapi.com/use-cases/internal-mobility.php)
- staffing firms matching temps to shifts, described for [staffing agencies](https://www.resumereaderapi.com/use-cases/staffing-agencies.php)
- vendors adding a parsing step to their product

## Normalization on its own

You do not have to parse a resume to use the normalizers. Feed lists of titles, skills or locations straight in.

| Endpoint | Input | Output |
|---|---|---|
| `normalize_title.php` | raw titles | canonical title, seniority, job function |
| `normalize_skills.php` | raw skills | canonical skill, one of 14 types |
| `normalize_locations.php` | raw places | city, region, country code, metro area, remote flag |

Each item costs a tenth of a credit. Real input and output pairs are collected on the [skills examples](https://www.resumereaderapi.com/normalization/skills-examples.php) page.

## Raw HTTP

```bash
curl -X POST https://www.resumereaderapi.com/api/parse.php \
  -H 'Content-Type: application/json' \
  -d '{"api_key":"YOUR_KEY","schema_version":2,"text":"Laura Bennett, Senior Data Analyst, Manchester ..."}'
```

## Credits

| Operation | Credits |
|---|---|
| parse up to 10 pages | 1 |
| parse 11 to 20 pages | 2 |
| normalize one item | 0.1 |

## Responsible handling

- Sensitive fields appear only when the document states them.
- `exclude_sensitive` removes them entirely.
- `anonymize` replaces names and contacts with placeholders.
- Documents are processed in memory and not retained.

<!--expanded-->
## How the clients are organised

This repository exists so that the clients and the notes about the schema live in one place that is easy to read and to copy from. The Node.js package sits in `node/` and the Python package in `python/`. Both are small on purpose. Each exposes the same operations under the naming conventions of its language: three ways to parse and three normalizers.

Both clients default to schema version 2, send the key in the JSON body, read the status field from the response body, and throw a typed error when the status is not 200. They also split long normalization lists into batches of 100 and add up the credits used. If you want to port the approach to another language, those four behaviours are the whole job.

## The examples folder

`examples/` holds scripts that match everyday jobs.

- `parse_folder.js` parses every PDF in a folder with a pause that respects the rate limit.
- `titles.py` normalizes a handful of job titles and prints the canonical form, the seniority and the function.
- `normalize.sh` calls the skill normalizer with curl, which is handy for checking a key.

Read them before you write your own. They show the options in use and the error handling that matters.

## Understanding the credits

Credits are the only meter. A resume of up to ten pages costs one credit. A longer document of up to twenty pages costs two. The check happens before processing, so a call with too few credits is refused and nothing is billed. Each normalized item costs a tenth of a credit, so a batch of a hundred titles costs ten credits.

Every response reports `credits_used` and `remaining_credits`. Log both. A simple graph of remaining credits against time shows your burn rate and tells you when to move to a bigger plan. For ordinary resumes, the number of credits equals the number of parsed resumes, so planning is easy.

## Schema notes in practice

The `schema/NOTES.md` file lists the top level keys and the enumerations worth hard coding. Some further observations from real use:

- Dates in work history use `YYYY-MM`, and a current job has `end_date` of `present`. Parse them with that in mind.
- The seniority level on the career block runs from junior to executive, while the normalized title seniority runs from intern to owner. They are different scales, so do not mix them in one column.
- The `esco` block can be null when the alignment is uncertain. Codes are never guessed.
- Employment gaps are listed as periods with a start, an end and a number of months.
- The `references` array and a few identity fields are marked sensitive and are skipped when you set `exclude_sensitive`.

## Designing a blind review process

A blind review process needs more than a flag. Decide who sees which version. Produce the anonymized copy for reviewers using `anonymize` and `exclude_sensitive`, keep the original in a restricted store, and keep a mapping between the two that only a coordinator can read. Document the process, because the credibility of a blind review rests on being able to show the data flow.

## Where candidate data goes next

Parsed data usually flows into an applicant tracking system, a search index and a reporting database. Each of those has different needs. The tracking system wants a short profile and a link to the original file. The index wants text fields and canonical values. The reporting database wants numbers and categories. Write one mapping function per destination, so a change in one system does not ripple into the others.

## Related services from the same company

Hiring is one of several problems this company works on with structured data. For teams that advertise roles, [audience data for agencies](https://www.cookielessaudiences.com/industries/agencies.php) describes how an agency can plan media by the audience a site reaches. For readers who want to know who is behind the services, the page [about Acquisition Universe](https://www.acquisitionuniverse.com/about.php) describes the sister product that screens the web for acquisition targets and the company behind it, Alpha Quantum.

## Testing the clients

Both clients have tests that run offline. The Node client has a smoke test in the package scripts, and the Python client can be exercised with a stub session. For integration tests with a real key, use a small fixed set of resumes and compare a few stable fields, such as the name and the number of jobs, rather than the whole object. Whole object comparisons break whenever the schema gains a field.

<!--extra-->
## Quick checklist for contributors

Run the tests before you open a pull request. Add a test for every behaviour you change. Keep `node/` free of runtime dependencies and `python/` limited to `requests`. Update the README tables when a method changes, and never commit keys or real resumes. The sample data in the examples is invented.

One more tip for the examples: run them against a sandbox account first, and print the credit fields after every call. Watching `remaining_credits` fall by exactly one per resume, and by a tenth per normalized item, is the quickest way to confirm that you understand the billing.

<!--further-->
## Further reading

The occupation and skills framework behind the `esco` block is documented on the [ESCO portal](https://esco.ec.europa.eu/en). The principles that govern storing candidate data in Europe are summarised on the [European Commission data protection pages](https://commission.europa.eu/law/law-topic/data-protection_en), and the [EEOC](https://www.eeoc.gov/) publishes guidance on fair employment practices in the United States. Read the second and third before you design ranking rules on top of parsed data.

## Frequently asked

**Can I parse a resume in a language other than English?** Yes. Many languages work. Add a `language` hint for best results.

**Can I use the clients in a browser?** No. Keep the key on a server.

**What happens to the files I send?** They are processed in memory for the request and are not retained.

**Where do I see my usage?** In every response, through the credit fields, and in your account.

## Contributing and license

Pull requests for the clients are welcome. Keep `node/` free of runtime dependencies and `python/` limited to `requests`. The code is MIT licensed. Questions go to info@alpha-quantum.com.

## Contributing

Pull requests are welcome for the clients. Keep `node/` dependency free and `python/` limited to `requests`.

## Contact

info@alpha-quantum.com. MIT license.
