import os
from fastapi import Header, HTTPException

def require_reviewer(x_reviewer_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("REVIEWER_TOKEN")
    if not expected:
        return
    if x_reviewer_token != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid reviewer token")