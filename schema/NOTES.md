# Schema v2 notes

The v2 response is a strict superset of v1. Every key is always present. A value without evidence in the document is `null` for scalars and objects and `[]` for arrays.

## Top level keys

`contact`, `profile`, `career`, `work_experience`, `education`, `skills`, `esco`, `military_service`, `security_clearance` and `meta`.

## Sensitive fields

Nine fields are marked sensitive: date of birth, nationality, gender, marital status, photo present, work permit, desired salary, references and security clearance. They are filled only when the document states them. Send `exclude_sensitive: true` to skip them, `anonymize: true` to replace values with placeholders.

## Enumerations worth hard-coding

- `career.seniority_level`: junior, mid, senior, lead, executive
- `career.career_progression`: ascending, stable, varied
- `work_experience[].employment_type`: permanent, temporary, contract, interim, freelance, internship, apprenticeship, part_time, unknown
- normalized title `seniority_level`: intern, junior, mid, senior, lead, manager, director, vp, c_level, owner
- normalized skill `skill_type`: programming_language, framework, database, cloud, devops_tool, software, methodology, soft_skill, language_human, design_tool, analytics, security, hardware, other

## Dates

Work history dates use YYYY-MM. `end_date` is `present` for a current role.
