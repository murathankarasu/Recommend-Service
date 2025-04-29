"""
date_utils.py
Farklı timestamp formatlarını güvenli şekilde parse eden ve UTC'ye normalize eden yardımcı fonksiyonlar.
"""
from datetime import datetime, timezone
from typing import Optional, Any
import logging

def parse_timestamp(ts: Any) -> Optional[datetime]:
    """
    Farklı formatlardaki timestamp'leri güvenli şekilde datetime objesine çevirir ve UTC'ye normalizer.
    Hatalıysa None döner.
    """
    if not ts:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None
    if isinstance(ts, str):
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%B %d, %Y at %I:%M:%S %p UTC",
            "%Y-%m-%d"
        ]:
            try:
                dt = datetime.strptime(ts, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
    return None

# Örnek kullanım:
if __name__ == "__main__":
    print(parse_timestamp("2024-05-01T12:00:00.000Z"))
    print(parse_timestamp(1714550400))  # unix timestamp
    print(parse_timestamp(datetime.now())) 