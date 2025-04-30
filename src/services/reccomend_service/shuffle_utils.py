"""
shuffle_utils.py
Aynı skorlu içeriklerde küçük bir rastgelelik eklemek için yardımcı fonksiyon.
"""
import random
from typing import List, Tuple, Any

def shuffle_same_score(contents: List[Tuple[float, Any]]) -> List[Any]:
    """
    Skoru aynı olan içerikleri kendi aralarında karıştırır, diğerlerini sıralı bırakır.
    """
    if not contents:
        return []
    # Skora göre grupla
    from collections import defaultdict
    score_groups = defaultdict(list)
    for score, content in contents:
        score_groups[score].append(content)
    # Skorları büyükten küçüğe sırala
    sorted_scores = sorted(score_groups.keys(), reverse=True)
    result = []
    for score in sorted_scores:
        group = score_groups[score]
        random.shuffle(group)
        result.extend(group)
    return result

# Örnek kullanım:
if __name__ == "__main__":
    test = [(1.0, 'A'), (0.9, 'B'), (0.9, 'C'), (0.8, 'D')]
    print(shuffle_same_score(test)) 