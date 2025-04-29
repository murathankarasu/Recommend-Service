from typing import List, Dict
from collections import Counter

def analyze_emotion_transition(interactions: List[Dict]) -> str:
    """
    Kullanıcının son etkileşimlerinde duygu geçişini analiz eder.
    En son iki farklı duyguyu bulur ve geçişi döndürür (örn: 'Neşe (Joy)' -> 'Üzüntü (Sadness)').
    Eğer geçiş yoksa None döner.
    """
    if not interactions or len(interactions) < 2:
        return None
    # Son etkileşimlerden duyguları sırayla al
    emotions = [i.get('emotion') for i in interactions if i.get('emotion')]
    if len(emotions) < 2:
        return None
    # Sondan başa farklı iki duyguyu bul
    last = emotions[-1]
    for prev in reversed(emotions[:-1]):
        if prev != last:
            return f"{prev} -> {last}"
    return None

# Örnek kullanım:
if __name__ == "__main__":
    test_interactions = [
        {'emotion': 'Neşe (Joy)'},
        {'emotion': 'Neşe (Joy)'},
        {'emotion': 'Üzüntü (Sadness)'},
    ]
    print(analyze_emotion_transition(test_interactions))  # Çıktı: Neşe (Joy) -> Üzüntü (Sadness) 