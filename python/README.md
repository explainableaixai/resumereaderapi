# resumereaderapi (Python)

Resume parser client for Python. Hand it a PDF, a DOCX, a scan or raw text and get structured candidate data back as a dictionary.

Needs `requests`. Python 3.7 and later.

```bash
pip install resumereaderapi
```

## Why use a hosted resume parser

Writing regular expressions for CVs is a trap. Layouts vary, languages vary, and half the documents are scans. A hosted resume parser gives you one stable shape no matter what the candidate uploaded.

The service behind this package is the [resume parser](https://www.resumereaderapi.com/) from Alpha Quantum. It returns 114 fields and marks missing facts as `None` instead of guessing.

## Parse in three lines

```python
from resumereaderapi import ResumeReader

rr = ResumeReader("YOUR_API_KEY")
data = rr.parse_file("cv.pdf")

print(data["resume"]["contact"]["emails"])
print(data["remaining_credits"])
```

## Calls

```python
rr.parse_text(text, field_names=None, exclude_sensitive=False, anonymize=False,
              max_pages=None, sections=None, language=None)
rr.parse_file(path, ...same options...)
rr.parse_url(https_url, ...same options...)

rr.normalize_titles(["Sr. SWE II"])
rr.normalize_skills(["K8s", "JS"])
rr.normalize_locations(["NYC"])
```

Normalizer methods batch in groups of 100 and return `{"results": [...], "credits_used": float, "remaining_credits": float}`.

## Skill normalization in practice

Candidates write the same skill ten ways. `JS`, `Javascript` and `java script` should be one filter value.

```python
raw = ["JS", "Javascript", "Python 3.11", "py", "MS Excel", "n/a"]
out = rr.normalize_skills(raw)
for item in out["results"]:
    print(item["input"], "->", item["normalized_skill"], item["skill_type"])
```

Junk entries such as "n/a" come back with `normalized_skill` set to `None`. See the [skill normalization](https://www.resumereaderapi.com/normalization/skills.php) page for fifty real examples.

## Anonymize before a human sees the CV

```python
data = rr.parse_file(
    "cv.docx",
    anonymize=True,
    exclude_sensitive=True,
)
```

Names, contact values and sensitive fields become placeholders such as `[NAME]` and `[EMAIL]`. This is the base of a blind review process, covered under [CV anonymization](https://www.resumereaderapi.com/use-cases/cv-anonymization.php).

## Handle errors

```python
from resumereaderapi import ResumeReaderError

try:
    rr.parse_file(path)
except ResumeReaderError as exc:
    if exc.status == 402:
        print("buy more credits")
    elif exc.status in (413, 422):
        print("bad document:", exc)
    else:
        raise
```

## Example: into a DataFrame

```python
import pandas as pd
from pathlib import Path

rows = []
for p in Path("cvs").glob("*.pdf"):
    r = rr.parse_file(str(p))["resume"]
    rows.append({
        "name": r["contact"]["full_name"],
        "city": r["contact"]["address"]["city"],
        "title": (r["career"]["current_position"] or {}).get("title"),
        "years": r["career"]["total_experience_years"],
        "skills": ", ".join(r["skills"]["technical"]),
    })

pd.DataFrame(rows).to_csv("candidates.csv", index=False)
```

## Example: Flask upload endpoint

```python
from flask import Flask, request, jsonify
import tempfile, os

app = Flask(__name__)

@app.post("/parse")
def parse():
    f = request.files["cv"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.filename)[1]) as tmp:
        f.save(tmp.name)
    try:
        return jsonify(rr.parse_file(tmp.name)["resume"])
    finally:
        os.unlink(tmp.name)
```

<!--expanded-->
## A Python workflow from folder to table

Most people meet resume parsing as a pile of files in a folder. The job is to turn the pile into a table you can sort and join. Python is well suited to it because the pieces are standard: `pathlib` to find files, a thread pool to parallelize calls, and `pandas` to hold the result.

Start by deciding the columns you care about. A recruiting database usually wants a name, a contact method, a location, a current title, a seniority level, years of experience and a list of skills. The parser returns far more than that, so write a small function that selects and flattens what you need, and keep the complete JSON next to it for later.

```python
from pathlib import Path
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from resumereaderapi import ResumeReader, ResumeReaderError

rr = ResumeReader("YOUR_API_KEY")

def row(path: Path):
    try:
        out = rr.parse_file(str(path))
    except ResumeReaderError as exc:
        return {"file": path.name, "error": exc.status}
    r = out["resume"]
    pos = r["career"]["current_position"] or {}
    return {
        "file": path.name,
        "name": r["contact"]["full_name"],
        "email": (r["contact"]["emails"] or [None])[0],
        "city": r["contact"]["address"]["city"],
        "title": pos.get("title"),
        "seniority": r["career"]["seniority_level"],
        "years": r["career"]["total_experience_years"],
        "skills": "|".join(r["skills"]["technical"]),
        "raw": json.dumps(r),
    }

files = sorted(Path("inbox").glob("*.pdf"))
with ThreadPoolExecutor(max_workers=3) as pool:
    table = pd.DataFrame(pool.map(row, files))
table.to_parquet("candidates.parquet")
```

Three workers is deliberate. The service allows 30 requests per 60 seconds per IP, so a small pool with a pause is safer than a large one that triggers a 429.

## Choosing options

The options change the shape of what you get, so decide them once and write them down.

- **`field_names="fr"`** renames the keys to French for teams that want French schemas. Values keep the language of the resume.
- **`exclude_sensitive=True`** skips the nine sensitive fields completely.
- **`anonymize=True`** replaces contact values and sensitive values with placeholders such as `[NAME]` and `[EMAIL]`.
- **`sections=[...]`** limits extraction to the sections you list, which is useful when you only need contact details.
- **`max_pages`** controls how many pages are processed.
- **`language`** is a hint for non English documents.

If you plan to compare candidates, anonymize the copy that reviewers see and keep the unmasked copy in a restricted store. That arrangement supports blind review without losing the ability to contact a shortlisted person.

## Normalizing after the fact

Parsing gives you the candidate's own words. Normalization gives you a common vocabulary. Run it on columns, not on single values, to keep the cost low and the batches full. Each item costs a tenth of a credit, and batches of up to 100 are handled in one call.

```python
titles = table["title"].dropna().unique().tolist()
mapped = rr.normalize_titles(titles)["results"]
lookup = {m["input"]: m for m in mapped}

table["canonical_title"] = table["title"].map(lambda t: lookup.get(t, {}).get("normalized_title"))
table["function"] = table["title"].map(lambda t: lookup.get(t, {}).get("job_function"))
```

The same pattern works for skills and locations. Deduplicate before sending. Ten thousand candidates may share only two thousand distinct job titles, and you pay for the distinct values only.

The title normalizer returns a canonical title, a seniority level from intern through owner, and a job function such as engineering, sales or finance. The skill normalizer classifies each skill into one of fourteen types, and the location normalizer returns a city, a region, a country and an ISO country code, plus a metro area and a remote flag when they apply. The [skill normalization page](https://www.resumereaderapi.com/normalization/skills.php) shows the alias handling and the type list in detail.

## Data quality checks

Run a few checks after every batch. They take minutes to write and save hours later.

1. The share of rows with an error status. A rise suggests a change in your inputs, such as a new scanner producing unreadable files.
2. The share with an empty email. A jump suggests that contact blocks are not being found in a new template.
3. The distribution of `seniority`. If it shifts sharply, look at the source of your files before you blame the parser.
4. The number of duplicate emails. Duplicates are usually real people who applied twice, and they are a useful signal for deduplication.

## Related reading

Resume data often meets other datasets. A marketing team may want to understand where to advertise open roles, and the [guide to purchase intent segments](https://www.cookielessaudiences.com/features/purchase-intent-data.php) describes a coded, cookie free way to describe what the readers of a site are likely to want. A corporate development team that evaluates staffing businesses can read how to [map a whole thesis universe](https://www.acquisitionuniverse.com/use-cases/thesis-universe-mapping.php) for a vertical.

<!--extra-->
## A final practical tip

Save the raw JSON of every parse next to your flattened table. Flattening is a decision, and decisions change. With the raw record, adding a new column is a re-read of stored data. Without it, adding a column means paying for the parse again.

<!--further-->
## Further reading and practical notes

The [Python documentation](https://docs.python.org/3/) covers `concurrent.futures`, `pathlib` and `base64`, which the examples above use. For the legal side of handling candidate data in Europe, the [European Commission pages on data protection](https://commission.europa.eu/law/law-topic/data-protection_en) set out the principles that apply to a recruiting database: lawful basis, purpose limitation, minimisation and storage limits.

Those principles translate into code in a few concrete ways. Store only the fields you need for the purpose you stated. Keep the original file and the parsed record under the same retention rule. Record when each record was created, so deletion jobs can find it. And make deletion real, which means removing the parsed JSON from every table and backup that holds it, not only from the main one.

When you design the pipeline, think about the failure that hurts most. It is rarely a crash. It is a silent mismatch, for example a parser that returns the wrong person's email because a template put a reference's contact details at the top. Protect against it by sampling. Every week, pull twenty parsed records at random and read them next to their source files. Twenty records take half an hour, and they catch problems that metrics cannot see.

## Frequently needed tweaks

**I only need emails.** Use `sections=["contact"]` to limit extraction.

**I need to re-parse with different options.** Keep the original files. Parsing is cheap compared with losing the source.

**I need to prove what I stored.** Store the raw JSON and the date. Do not edit it in place.

**I have a mix of languages.** Pass `language` when you know it. The parser also handles mixed content, but a hint helps.

## Notes on reliability

The published test suite for the service runs against the live endpoints before every release, including every documented error path, so the status codes in this README are the ones you will actually see. Treat them as part of the contract and write code against them.

## Questions

**What file types?** PDF, DOCX, TXT, RTF, HTML, ODT, spreadsheets and images including scanned PDFs.

**Is there a limit per call?** 10 MB, 20 pages and about 30,000 tokens.

**Does it work in French?** Pass `field_names="fr"` for French keys. Values keep the language of the resume.

MIT license. Contact: info@alpha-quantum.com
