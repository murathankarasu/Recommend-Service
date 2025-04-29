"""
ab_test_logger.py
A/B test ve algoritma parametre loglama yardımcı modülü.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("ab_test_logger")

# Basit dosya loglama (gelişmiş sistemlerde veritabanı veya harici log servisi kullanılabilir)
LOG_FILE = "ab_test_logs.txt"


def log_recommendation_event(user_id: str, recommended_posts: List[Any], params: Dict[str, Any]):
    """
    Kullanıcıya hangi parametrelerle hangi içeriklerin gösterildiğini loglar.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "shown_post_ids": recommended_posts,
        "params": params
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(log_entry) + "\n")

# Örnek kullanım:
if __name__ == "__main__":
    log_recommendation_event(
        user_id="user_123",
        recommended_posts=["post_1", "post_2"],
        params={"repeat_ratio": 0.2, "diversity": True}
    ) 