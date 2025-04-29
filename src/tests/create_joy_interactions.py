import asyncio
import random
import sys
import os
from datetime import datetime, timedelta
import uuid

# src dizinini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.firebase_service import FirebaseService

async def create_joy_interactions():
    firebase = FirebaseService()
    user_id = "isRKPOpG4zVFmULHJjrsvY8t1Nb2"
    
    # 20 farklı post ID'si oluştur (UUID formatında)
    post_ids = [str(uuid.uuid4()).upper() for _ in range(20)]
    
    # Her post için etkileşim oluştur
    for post_id in post_ids:
        # Rastgele confidence değeri (0.85-0.97 arasında)
        confidence = random.uniform(0.85, 0.97)
        
        # Etkileşimi kaydet
        await firebase.add_interaction(
            user_id=user_id,
            content_id=post_id,
            interaction_type="like",
            emotion="Neşe (Joy)",
            confidence=confidence
        )
        print(f"Etkileşim kaydedildi: {post_id}")

if __name__ == "__main__":
    asyncio.run(create_joy_interactions()) 