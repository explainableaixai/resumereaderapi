import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="resumereaderapi",
    version="1.0.1",
    description="Python client for the Resume Reader API: parse PDF, DOCX and scanned resumes into 114 structured JSON fields, and normalize job titles, skills and locations.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Alpha Quantum",
    author_email="info@alpha-quantum.com",
    url="https://www.resumereaderapi.com",
    project_urls={
        "Homepage": "https://www.resumereaderapi.com",
        "Documentation": "https://www.resumereaderapi.com/api-v2.php",
        "Source": "https://github.com/explainableaixai/resumereaderapi",
        "Mirror": "https://gitlab.com/url-classifications/resumereaderapi",
        "Pricing": "https://www.resumereaderapi.com/pricing.php",
    },
    license="MIT",
    packages=find_packages(exclude=("tests", "test")),
    python_requires=">=3.7",
    install_requires=["requests>=2.20.0"],
    keywords=["resume parser", "cv parser", "resume parsing api", "resume to json", "ats", "recruiting", "hr tech",
              "job title normalization", "skill normalization", "location normalization", "ocr", "cv anonymization"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
    ],
)
