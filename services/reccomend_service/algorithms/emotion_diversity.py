from typing import List, Dict
from collections import defaultdict
import random

def ensure_emotion_diversity(
    recommendations: List[Dict],
    all_contents: List[Dict],
    min_per_emotion: int = 1
) -> List[Dict]:
    """
    Her duygudan en az 'min_per_emotion' içerik olmasını garanti eder.
    Eksik duygular için öneri listesinde olmayan içeriklerden ekleme yapar.
    """
    emotion_to_contents = defaultdict(list)
    for c in recommendations:
        emotion = c.get('emotion')
        if emotion:
            emotion_to_contents[emotion].append(c)
    # Tüm duyguları belirle (hem önerilerde hem all_contents'ta olanlar)
    all_emotions = set([c.get('emotion') for c in all_contents if c.get('emotion')])
    for emotion in all_emotions:
        eksik = min_per_emotion - len(emotion_to_contents[emotion])
        if eksik > 0:
            # Eksikse, öneri listesinde olmayanlardan ekle
            candidates = [c for c in all_contents if c.get('emotion') == emotion and c not in recommendations]
            if candidates:
                to_add = random.sample(candidates, min(eksik, len(candidates)))
                # Rastgele yerlere ekle
                for add in to_add:
                    idx = random.randint(0, len(recommendations))
                    recommendations.insert(idx, add)
    return recommendations

# Örnek kullanım:
if __name__ == "__main__":
    recs = [
        {'id': 1, 'emotion': 'Neşe (Joy)'},
        {'id': 2, 'emotion': 'Aşk (Love)'},
        {'id': 3, 'emotion': 'Neşe (Joy)'}
    ]
    allc = recs + [
        {'id': 4, 'emotion': 'Korku (Fear)'},
        {'id': 5, 'emotion': 'Şaşkınlık (Surprise)'}
    ]
    print(ensure_emotion_diversity(recs, allc, min_per_emotion=1)) 