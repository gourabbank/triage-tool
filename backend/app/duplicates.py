from difflib import SequenceMatcher
from typing import Optional
from . import models

SIMILARITY_THRESHOLD = 0.72

def find_duplicate(raw_text: str, existing: list[models.Request]) -> Optional[str]:
    best_id, best_ratio = None, 0.0
    for candidate in existing[:200]:
        ratio = SequenceMatcher(None, raw_text.lower(), candidate.raw_text.lower()).ratio()
        if ratio > best_ratio:
            best_ratio, best_id = ratio, candidate.id
    return best_id if best_ratio >= SIMILARITY_THRESHOLD else None