import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from resumereaderapi import ResumeReader

rr = ResumeReader(os.environ["RESUME_KEY"])
for r in rr.normalize_titles(["Sr. SWE II", "Growth Ninja", "VP Sales EMEA"])["results"]:
    print(r["input"], "->", r["normalized_title"], r["seniority_level"], r["job_function"])
