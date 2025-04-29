import random
from typing import List, Dict

def inject_random_emotion_content(
    recommendations: List[Dict],
    all_contents: List[Dict],
    pattern: Dict[str, float],
    ratio: float = 0.1,
    max_ratio: float = 0.2
) -> List[Dict]:
    """
    Pattern'de en düşük orana sahip ve/veya hiç deneyimlenmemiş duygulardan rastgele içerik ekler.
    Toplamda feed'in max_ratio'sunu geçmez. Diğer duyguların oranı korunur.
    """
    if not all_contents or not pattern:
        return recommendations
    # Hiç deneyimlenmemiş duyguları bul
    all_emotions = set([c.get('emotion') for c in all_contents if c.get('emotion')])
    experienced_emotions = set([e for e, v in pattern.items() if v > 0])
    unexperienced_emotions = all_emotions - experienced_emotions
    # En düşük orana sahip duygular
    min_val = min(pattern.values())
    min_emotions = [e for e, v in pattern.items() if v == min_val]
    # Hedef duygular: hem hiç yaşanmamışlar hem de en düşük orana sahip olanlar
    target_emotions = set(min_emotions) | unexperienced_emotions
    # Aday içerikler
    candidates = [c for c in all_contents if c.get('emotion') in target_emotions and c not in recommendations]
    if not candidates:
        return recommendations
    # Eklenebilecek maksimum içerik sayısı (max_ratio ile sınırlı)
    max_inject = int(len(recommendations) * max_ratio)
    n_inject = min(max_inject, max(1, int(len(recommendations) * ratio)), len(candidates))
    injects = random.sample(candidates, n_inject)
    # Rastgele yerlere dengeli dağıt
    step = max(1, len(recommendations) // (n_inject + 1))
    idxs = [(i + 1) * step for i in range(n_inject)]
    for inj, idx in zip(injects, idxs):
        insert_idx = min(idx, len(recommendations))
        recommendations.insert(insert_idx, inj)
    return recommendations

# Örnek kullanım:
if __name__ == "__main__":
    recs = [
        {'id': 1, 'emotion': 'Neşe (Joy)'},
        {'id': 2, 'emotion': 'Aşk (Love)'}
    ]
    allc = recs + [
        {'id': 3, 'emotion': 'Korku (Fear)'},
        {'id': 4, 'emotion': 'Korku (Fear)'},
        {'id': 5, 'emotion': 'Şaşkınlık (Surprise)'}
    ]
    pattern = {'Neşe (Joy)': 0.7, 'Aşk (Love)': 0.2, 'Korku (Fear)': 0.1, 'Şaşkınlık (Surprise)': 0.0}
    print(inject_random_emotion_content(recs, allc, pattern, 0.2, 0.3)) 