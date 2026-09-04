from src.crawling.structured_data_parser import parse_page
from src.discovery.extraction_utils import extract_company_candidate, extract_person_candidates

JSONLD_HTML = """
<html><head><title>About Us | Acme Corp</title>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Person", "name": "Olena Kovalenko",
 "jobTitle": "Co-Founder & CEO", "email": "mailto:olena@acme.com",
 "sameAs": ["https://linkedin.com/in/olenakovalenko"]}
</script>
<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Organization", "name": "Acme Corp", "url": "https://acme.com"}
</script>
</head><body><h1>Welcome to Acme</h1></body></html>
"""

HEADING_HTML = """
<html><head><title>Team | Beta LLC</title></head>
<body>
<h2>John Smith, Head of Marketing</h2>
<h2>Not A Valid Heading</h2>
<a href="https://linkedin.com/in/johnsmith">LinkedIn</a>
</body></html>
"""


def test_extract_person_from_jsonld():
    data = parse_page(JSONLD_HTML, "https://acme.com/about")
    people = extract_person_candidates(data, "https://acme.com/about")
    assert len(people) == 1
    assert people[0]["full_name"] == "Olena Kovalenko"
    assert people[0]["job_title"] == "Co-Founder & CEO"
    assert "https://linkedin.com/in/olenakovalenko" in people[0]["profile_links"]


def test_extract_company_from_jsonld():
    data = parse_page(JSONLD_HTML, "https://acme.com/about")
    company = extract_company_candidate(data, "https://acme.com/about")
    assert company is not None
    assert company["company_name"] == "Acme Corp"


def test_extract_person_from_heading_pattern():
    data = parse_page(HEADING_HTML, "https://beta.com/team")
    people = extract_person_candidates(data, "https://beta.com/team")
    names = [p["full_name"] for p in people]
    assert "John Smith" in names
    match = next(p for p in people if p["full_name"] == "John Smith")
    assert match["job_title"] == "Head of Marketing"


def test_extract_company_falls_back_to_title():
    data = parse_page(HEADING_HTML, "https://beta.com/team")
    company = extract_company_candidate(data, "https://beta.com/team")
    assert company is not None
    assert "Beta LLC" in company["company_name"] or "Team" in company["company_name"]
