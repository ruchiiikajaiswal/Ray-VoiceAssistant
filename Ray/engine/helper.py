# Helper utilities for the voice assistant
import re

def extract_yt_term(query: str) -> str:
    """Extract YouTube search term from query."""
    return re.sub(r"play|on youtube", "", query, flags=re.I).strip()
