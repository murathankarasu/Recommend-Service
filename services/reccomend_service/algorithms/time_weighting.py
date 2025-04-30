from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

def parse_timestamp(ts) -> Optional[datetime]:
    """
    Farklı formatlardaki timestamp'leri güvenli şekilde datetime objesine çevirir.
    Hatalıysa None döner.
    """
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, (int, float)):
        # Unix timestamp (saniye cinsinden)
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return None
    if isinstance(ts, str):
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO w/ ms + Z
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%B %d, %Y at %I:%M:%S %p UTC",  # Firebase
            "%Y-%m-%d"
        ]:
            try:
                return datetime.strptime(ts, fmt)
            except Exception:
                continue
        # Son çare: fromisoformat
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None
    return None

def time_weighted_emotion_pattern(
    interactions: List[Dict],
    base_pattern: Dict[str, float],
    weights: Dict[str, float] = None,
    intervals: Dict[str, int] = None
) -> Dict[str, float]:
    """
    Zaman aralıkları ve ağırlıkları parametre olarak alır.
    intervals: {'24h': 1, '7d': 7} gibi (gün cinsinden)
    weights: {'24h': 2.0, '7d': 1.5, 'older': 1.0}
    """
    now = datetime.now()
    if weights is None:
        weights = {'24h': 2.0, '7d': 1.5, 'older': 1.0}
    if intervals is None:
        intervals = {'24h': 1, '7d': 7}
    emotion_weights = defaultdict(float)
    total_weight = 0.0
    for interaction in interactions:
        emotion = interaction.get('emotion')
        timestamp = interaction.get('timestamp')
        if not emotion or not timestamp:
            continue
        dt = parse_timestamp(timestamp)
        if not dt:
            logging.warning(f"Geçersiz timestamp atlandı: {timestamp}")
            continue
        days_ago = (now - dt).days
        if days_ago < intervals['24h']:
            w = weights['24h']
        elif days_ago < intervals['7d']:
            w = weights['7d']
        else:
            w = weights['older']
        emotion_weights[emotion] += w
        total_weight += w
    if total_weight == 0:
        return base_pattern
    pattern = {e: emotion_weights[e] / total_weight for e in base_pattern.keys()}
    return pattern

# Örnek kullanım:
if __name__ == "__main__":
    test_interactions = [
        {'emotion': 'Neşe (Joy)', 'timestamp': datetime.now().isoformat()},
        {'emotion': 'Üzüntü (Sadness)', 'timestamp': (datetime.now() - timedelta(days=2)).isoformat()},
        {'emotion': 'Aşk (Love)', 'timestamp': (datetime.now() - timedelta(days=10)).isoformat()},
        {'emotion': 'Korku (Fear)', 'timestamp': '2023-12-01T12:00:00.000Z'},
        {'emotion': 'Şaşkınlık (Surprise)', 'timestamp': 1700000000},  # unix timestamp
        {'emotion': 'Öfke (Anger)', 'timestamp': 'Geçersiz tarih'}
    ]
    base = {'Neşe (Joy)': 0.5, 'Üzüntü (Sadness)': 0.3, 'Aşk (Love)': 0.1, 'Korku (Fear)': 0.05, 'Şaşkınlık (Surprise)': 0.05}
    print(time_weighted_emotion_pattern(test_interactions, base)) 