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

## Questions

**What file types?** PDF, DOCX, TXT, RTF, HTML, ODT, spreadsheets and images including scanned PDFs.

**Is there a limit per call?** 10 MB, 20 pages and about 30,000 tokens.

**Does it work in French?** Pass `field_names="fr"` for French keys. Values keep the language of the resume.

MIT license. Contact: info@alpha-quantum.com
