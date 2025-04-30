from typing import List, Dict, Any
from collections import Counter
from datetime import datetime

def detect_emotion_loop(interactions: List[Dict], window: int = 10, threshold: float = 0.8) -> Dict[str, Any]:
    """
    Kullanıcının son N etkileşiminde tek bir duyguda sıkışıp kalıp kalmadığını tespit eder.
    Sıkışma varsa: hangi duygu, kaç etkileşimdir ve kaç gündür devam ediyor bilgisini de döndürür.
    Dönüş: {
        'loop': True/False,
        'emotion': <str|None>,
        'count': <int>,
        'days': <float>
    }
    """
    if not interactions:
        return {'loop': False, 'emotion': None, 'count': 0, 'days': 0}
    emotions = [i.get('emotion') for i in interactions if i.get('emotion')]
    if len(emotions) < window:
        return {'loop': False, 'emotion': None, 'count': 0, 'days': 0}
    recent = emotions[-window:]
    counts = Counter(recent)
    most_common_emotion, count = counts.most_common(1)[0]
    if count / window >= threshold:
        # Kaç etkileşimdir bu duygu üst üste geliyor?
        streak = 0
        for i in reversed(interactions):
            if i.get('emotion') == most_common_emotion:
                streak += 1
            else:
                break
        # İlk sıkışma etkileşiminden bu yana kaç gün geçti?
        first_streak_idx = len(interactions) - streak
        if 0 <= first_streak_idx < len(interactions):
            first_streak_time = interactions[first_streak_idx].get('timestamp')
            if first_streak_time:
                try:
                    if isinstance(first_streak_time, str):
                        dt = datetime.fromisoformat(first_streak_time)
                    else:
                        dt = first_streak_time
                    days = (datetime.now() - dt).total_seconds() / 86400
                except Exception:
                    days = 0
            else:
                days = 0
        else:
            days = 0
        return {'loop': True, 'emotion': most_common_emotion, 'count': streak, 'days': days}
    return {'loop': False, 'emotion': None, 'count': 0, 'days': 0}

# Örnek kullanım:
if __name__ == "__main__":
    from datetime import timedelta
    now = datetime.now()
    test_interactions = [
        {'emotion': 'Neşe (Joy)', 'timestamp': (now - timedelta(days=2)).isoformat()} for _ in range(8)
    ] + [
        {'emotion': 'Üzüntü (Sadness)', 'timestamp': (now - timedelta(days=1)).isoformat()},
        {'emotion': 'Neşe (Joy)', 'timestamp': now.isoformat()}
    ]
    print(detect_emotion_loop(test_interactions, window=10, threshold=0.7))  # {'loop': True, ...} 