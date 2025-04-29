"""
cold_start_utils.py
Yeni kullanıcılar için soğuk başlangıç öneri fonksiyonları.
"""
from typing import List, Dict, Any
import random

def get_cold_start_content(all_contents: List[Dict[str, Any]], emotion_categories: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """
    Hiç etkileşimi olmayan kullanıcıya, popüler ve çeşitli içeriklerden karışım sunar.
    """
    # Her duygudan en az 1 içerik ekle
    selected = []
    for emotion in emotion_categories:
        candidates = [c for c in all_contents if c.get('emotion') == emotion]
        if candidates:
            selected.append(random.choice(candidates))
    # Kalan slotları rastgele popüler içeriklerle doldur
    remaining = limit - len(selected)
    if remaining > 0:
        # Popülerlik için likes+comments+views toplamı kullanılabilir
        def get_comments_count(c):
            if 'commentsCount' in c:
                return c.get('commentsCount', 0)
            elif isinstance(c.get('comments', None), list):
                return len(c.get('comments', []))
            else:
                return 0
        sorted_contents = sorted(
            all_contents,
            key=lambda c: (
                c.get('likes', 0) +
                get_comments_count(c) +
                c.get('views', 0)
            ),
            reverse=True
        )
        for c in sorted_contents:
            if c not in selected:
                selected.append(c)
            if len(selected) >= limit:
                break
    random.shuffle(selected)
    return selected[:limit]

# Örnek kullanım:
if __name__ == "__main__":
    allc = [
        {'id': i, 'emotion': e, 'likes': random.randint(0,100), 'comments': random.randint(0,20), 'views': random.randint(0,1000)}
        for i, e in enumerate(['Neşe (Joy)', 'Üzüntü (Sadness)', 'Aşk (Love)', 'Korku (Fear)', 'Şaşkınlık (Surprise)']*5)
    ]
    print(get_cold_start_content(allc, ['Neşe (Joy)', 'Üzüntü (Sadness)', 'Aşk (Love)', 'Korku (Fear)', 'Şaşkınlık (Surprise)'], 10)) 