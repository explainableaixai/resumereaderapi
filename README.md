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

## Contributing

Pull requests are welcome for the clients. Keep `node/` dependency free and `python/` limited to `requests`.

## Contact

info@alpha-quantum.com. MIT license.
