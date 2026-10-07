"""Client for the Resume Reader API (https://www.resumereaderapi.com)."""
import base64
import os
from typing import Any, Dict, Iterable, List, Optional

import requests

__version__ = "1.0.0"
BASE = "https://www.resumereaderapi.com/api/"

STATUS_TEXT = {
    400: "Missing or invalid input",
    401: "Invalid API key",
    402: "Insufficient credits, nothing was billed",
    413: "Document beyond 20 pages, about 30,000 tokens or 10 MB, nothing was billed",
    422: "File could not be read as a resume",
    429: "Rate limit exceeded, 30 requests per 60 seconds per IP",
}


class ResumeReaderError(Exception):
    """The HTTP status is always 200, so errors come from the status field of the JSON body."""

    def __init__(self, status: int, message: str, body: Optional[dict] = None):
        super().__init__("[%s] %s" % (status, message))
        self.status = status
        self.body = body or {}


class ResumeReader:
    def __init__(self, api_key: str, schema_version: int = 2, timeout: float = 120.0,
                 session: Optional[requests.Session] = None):
        if not api_key:
            raise ValueError("An API key is required")
        self.api_key = api_key
        self.schema_version = schema_version
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = "resumereaderapi-python/%s (+https://www.resumereaderapi.com)" % __version__

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.post(BASE + endpoint, json=payload, timeout=self.timeout)
        try:
            body = resp.json()
        except ValueError:
            raise ResumeReaderError(resp.status_code, "Response was not JSON")
        status = body.get("status", 200) if isinstance(body, dict) else 200
        if status != 200:
            raise ResumeReaderError(status, STATUS_TEXT.get(status) or body.get("message", "API error"), body)
        return body

    def _parse(self, source: Dict[str, Any], field_names: Optional[str], exclude_sensitive: bool,
               anonymize: bool, max_pages: Optional[int], sections: Optional[List[str]],
               language: Optional[str]) -> Dict[str, Any]:
        payload = {"api_key": self.api_key, "schema_version": self.schema_version}
        payload.update(source)
        if field_names:
            payload["field_names"] = field_names
        if exclude_sensitive:
            payload["exclude_sensitive"] = True
        if anonymize:
            payload["anonymize"] = True
        if max_pages:
            payload["max_pages"] = max_pages
        if sections:
            payload["sections"] = sections
        if language:
            payload["language"] = language
        return self._post("parse.php", payload)

    def parse_text(self, text: str, field_names: Optional[str] = None, exclude_sensitive: bool = False,
                   anonymize: bool = False, max_pages: Optional[int] = None,
                   sections: Optional[List[str]] = None, language: Optional[str] = None) -> Dict[str, Any]:
        return self._parse({"text": text}, field_names, exclude_sensitive, anonymize, max_pages, sections, language)

    def parse_file(self, path: str, field_names: Optional[str] = None, exclude_sensitive: bool = False,
                   anonymize: bool = False, max_pages: Optional[int] = None,
                   sections: Optional[List[str]] = None, language: Optional[str] = None) -> Dict[str, Any]:
        with open(path, "rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("ascii")
        source = {"file_base64": encoded, "filename": os.path.basename(path)}
        return self._parse(source, field_names, exclude_sensitive, anonymize, max_pages, sections, language)

    def parse_url(self, file_url: str, field_names: Optional[str] = None, exclude_sensitive: bool = False,
                  anonymize: bool = False, max_pages: Optional[int] = None,
                  sections: Optional[List[str]] = None, language: Optional[str] = None) -> Dict[str, Any]:
        return self._parse({"file_url": file_url}, field_names, exclude_sensitive, anonymize, max_pages, sections, language)

    def _normalize(self, endpoint: str, key: str, items: Iterable[str]) -> Dict[str, Any]:
        values = [items] if isinstance(items, str) else list(items)
        results: List[Dict[str, Any]] = []
        used = 0.0
        remaining = None
        for i in range(0, len(values), 100):
            body = self._post(endpoint, {"api_key": self.api_key, key: values[i:i + 100]})
            results.extend(body.get("results", []))
            used += body.get("credits_used", 0)
            remaining = body.get("remaining_credits", remaining)
        return {"results": results, "credits_used": round(used, 4), "remaining_credits": remaining}

    def normalize_titles(self, titles: Iterable[str]) -> Dict[str, Any]:
        return self._normalize("normalize_title.php", "titles", titles)

    def normalize_skills(self, skills: Iterable[str]) -> Dict[str, Any]:
        return self._normalize("normalize_skills.php", "skills", skills)

    def normalize_locations(self, locations: Iterable[str]) -> Dict[str, Any]:
        return self._normalize("normalize_locations.php", "locations", locations)
