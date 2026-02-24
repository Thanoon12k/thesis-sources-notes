"""
citations.py — IEEE and APA citation formatting and parsing utilities.
"""

import re


# IEEE reference types
REF_TYPES = [
    "article",
    "conference",
    "book",
    "thesis",
    "report",
    "standard",
    "website",
    "patent",
    "manual",
    "other",
]

CITATION_STYLES = ["IEEE", "APA"]


def format_ieee(ref_dict):
    """
    Format a reference dictionary into IEEE citation string.
    Returns something like:
        [1] A. Author and B. Author, "Title," Source, year.
    """
    num = ref_dict.get("ref_number", "?")
    authors = ref_dict.get("authors", "").strip()
    title = ref_dict.get("title", "").strip()
    source = ref_dict.get("source", "").strip()
    year = ref_dict.get("year", "").strip()
    doi_url = ref_dict.get("doi_url", "").strip()
    ref_type = ref_dict.get("ref_type", "article")

    parts = [f"[{num}]"]

    if authors:
        parts.append(f" {authors},")

    if title:
        parts.append(f' "{title},"')

    if source:
        if ref_type in ("book", "thesis", "manual"):
            parts.append(f" *{source}*,")
        else:
            parts.append(f" {source},")

    if year:
        parts.append(f" {year}.")

    if doi_url:
        if doi_url.startswith("http"):
            parts.append(f" [Online]. Available: {doi_url}")
        else:
            parts.append(f" doi: {doi_url}")

    result = "".join(parts)
    result = re.sub(r",\s*\.", ".", result)
    result = re.sub(r",\s*,", ",", result)
    return result.strip()


def format_apa(ref_dict):
    """
    Format a reference dictionary into APA 7th edition citation string.
    Returns something like:
        Author, A. B., & Author, C. D. (2020). Title. Source. https://doi.org/...
    """
    authors = ref_dict.get("authors", "").strip()
    title = ref_dict.get("title", "").strip()
    source = ref_dict.get("source", "").strip()
    year = ref_dict.get("year", "").strip()
    doi_url = ref_dict.get("doi_url", "").strip()

    parts = []

    if authors:
        parts.append(f"{authors}")

    if year:
        parts.append(f" ({year}).")
    else:
        parts.append(" (n.d.).")

    if title:
        parts.append(f" {title}.")

    if source:
        parts.append(f" *{source}*.")

    if doi_url:
        if doi_url.startswith("http"):
            parts.append(f" {doi_url}")
        else:
            parts.append(f" https://doi.org/{doi_url}")

    result = "".join(parts)
    return result.strip()


def format_citation(ref_dict, style="IEEE"):
    """Format a reference in the given citation style."""
    if style == "APA":
        return format_apa(ref_dict)
    return format_ieee(ref_dict)


def parse_reference(text):
    """
    Best-effort parse of a citation string (IEEE or APA) into a dict.
    Falls back to storing the entire text as the title if parsing fails.
    """
    text = text.strip()
    if not text:
        return {
            "ref_number": None, "authors": "", "title": "",
            "source": "", "year": "", "doi_url": "", "ref_type": "article",
        }

    # Try IEEE format first: starts with [N]
    if re.match(r"\[\d+\]", text):
        return _parse_ieee(text)

    # Try APA format: has (year) pattern
    if re.search(r"\(\d{4}\)", text):
        return _parse_apa(text)

    # Fallback: store raw text as title
    year_match = re.search(r"\b((?:19|20)\d{2})\b", text)
    url_match = re.search(r"(https?://\S+)", text)
    return {
        "ref_number": None,
        "authors": "",
        "title": text[:200],
        "source": "",
        "year": year_match.group(1) if year_match else "",
        "doi_url": url_match.group(1) if url_match else "",
        "ref_type": "article",
    }


def _parse_ieee(text):
    """Parse IEEE-style [N] Author, "Title," Source, Year."""
    result = {
        "ref_number": None, "authors": "", "title": "",
        "source": "", "year": "", "doi_url": "", "ref_type": "article",
    }

    # Extract [N]
    num_match = re.match(r"\[(\d+)\]\s*", text)
    if num_match:
        result["ref_number"] = int(num_match.group(1))
        text = text[num_match.end():]

    # Extract URL / DOI
    url_match = re.search(r"(?:Available:\s*|doi:\s*)(https?://\S+|10\.\S+)", text)
    if url_match:
        result["doi_url"] = url_match.group(1)
        text = text[:url_match.start()].strip().rstrip(".")

    # Extract title in quotes
    title_match = re.search(r'"([^"]+)"', text)
    if title_match:
        result["title"] = title_match.group(1).rstrip(",").strip()
        before_title = text[:title_match.start()].strip().rstrip(",").strip()
        after_title = text[title_match.end():].strip().lstrip(",").strip()
    else:
        before_title = ""
        after_title = text

    if before_title:
        result["authors"] = before_title.strip()

    year_match = re.search(r"\b((?:19|20)\d{2})\b", after_title)
    if year_match:
        result["year"] = year_match.group(1)
        after_title = (after_title[:year_match.start()] + after_title[year_match.end():]).strip()

    source = after_title.strip().strip(".,*").strip()
    if source:
        result["source"] = source

    # If nothing was parsed into title, use the whole text
    if not result["title"] and not result["authors"]:
        result["title"] = text[:200]

    return result


def _parse_apa(text):
    """Parse APA-style: Author (Year). Title. Source. URL"""
    result = {
        "ref_number": None, "authors": "", "title": "",
        "source": "", "year": "", "doi_url": "", "ref_type": "article",
    }

    # Extract URL
    url_match = re.search(r"(https?://\S+)", text)
    if url_match:
        result["doi_url"] = url_match.group(1).rstrip(".")
        text = text[:url_match.start()].strip()

    # Extract (year)
    year_match = re.search(r"\((\d{4})\)", text)
    if year_match:
        result["year"] = year_match.group(1)
        before_year = text[:year_match.start()].strip().rstrip(",").strip()
        after_year = text[year_match.end():].strip().lstrip(".").strip()
    else:
        before_year = ""
        after_year = text

    if before_year:
        result["authors"] = before_year

    # After year: Title. Source.
    parts = [p.strip() for p in after_year.split(".") if p.strip()]
    if len(parts) >= 2:
        result["title"] = parts[0]
        result["source"] = parts[1].strip("*").strip()
    elif len(parts) == 1:
        result["title"] = parts[0]

    if not result["title"] and not result["authors"]:
        result["title"] = text[:200]

    return result


# Keep backward compatibility
def parse_ieee(text):
    """Backward compatible: parse any citation format."""
    return parse_reference(text)


def format_ieee_inline(ref_number):
    """Format an inline citation like [1] or [1, 2] or [1]-[3]."""
    if isinstance(ref_number, (list, tuple)):
        if len(ref_number) == 1:
            return f"[{ref_number[0]}]"
        nums = sorted(ref_number)
        if nums == list(range(nums[0], nums[-1] + 1)):
            return f"[{nums[0]}]-[{nums[-1]}]"
        return "[" + ", ".join(str(n) for n in nums) + "]"
    return f"[{ref_number}]"


def copy_to_clipboard(root, text):
    """Copy text to system clipboard using tkinter."""
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
