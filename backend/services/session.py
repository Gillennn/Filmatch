import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional

_sessions: Dict[str, dict] = {}


def _gen_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_session() -> dict:
    code = _gen_code()
    while code in _sessions:
        code = _gen_code()
    s = {
        "code": code,
        "created_at": datetime.now(),
        "mood": "",
        "users": {},
        "status": "waiting",
        "results": None,
    }
    _sessions[code] = s
    return s


def get_session(code: str) -> Optional[dict]:
    s = _sessions.get(code.upper())
    if not s:
        return None
    if datetime.now() - s["created_at"] > timedelta(hours=24):
        del _sessions[code.upper()]
        return None
    return s
