"""
user_history_utils.py
Kullanıcının gösterilen içerik geçmişini yönetmek için yardımcı fonksiyonlar.
"""
from typing import List, Any

MAX_HISTORY = 200  # Kaç postId tutulacak (performans ve çeşitlilik için)

def get_recent_shown_post_ids(user_interactions: List[dict], max_history: int = MAX_HISTORY) -> List[Any]:
    """
    Kullanıcının geçmiş etkileşimlerinden en son gösterilen postId'leri toplar.
    Farklı veri kaynaklarında farklı anahtarlar olabileceği için esnek çalışır.
    """
    ids = [i.get('postId') or i.get('content_id') or i.get('id') for i in user_interactions if i.get('postId') or i.get('content_id') or i.get('id')]
    return ids[-max_history:]

# Örnek kullanım:
if __name__ == "__main__":
    interactions = [
        {'postId': f'post_{i}'} for i in range(250)
    ]
    print(get_recent_shown_post_ids(interactions))  # Son 200 postId'yi döndürür 