from services.firebase_service import FirebaseService
from datetime import datetime, timedelta
import random
from config.config import EMOTION_CATEGORIES, COLLECTION_POSTS
import asyncio

async def create_ad_posts():
    firebase = FirebaseService()
    
    # Reklam postları için örnek veriler
    ad_contents = {
        "Aşk (Love)": [
            "Sevginin gücüyle daha güçlüyüz! 💖",
            "Aşk her şeyi değiştirir... ❤️",
            "Sevgi dolu bir dünya için... 💕"
        ],
        "Korku (Fear)": [
            "Güvenliğiniz bizim önceliğimiz! 🔒",
            "Korkularınızı yenmek için yanınızdayız... 🛡️",
            "Güvenli bir gelecek için... 🏰"
        ],
        "Neşe (Joy)": [
            "Mutluluk paylaştıkça çoğalır! 🎉",
            "Hayatı güzelleştirmek için... 🌈",
            "Gülümsemek için bir neden daha... 😊"
        ],
        "Öfke (Anger)": [
            "Öfkenizi kontrol edin, hayatınızı değiştirin! 💪",
            "Sakin kalmak için yanınızdayız... 🧘",
            "Öfkeyi güce dönüştürün... ⚡"
        ],
        "Üzüntü (Sadness)": [
            "Yalnız değilsiniz, yanınızdayız... 🤝",
            "Üzüntülerinizi paylaşın, hafifleyin... 🕊️",
            "Daha iyi günler için... 🌅"
        ],
        "Şaşkınlık (Surprise)": [
            "Beklenmedik anlar için hazır mısınız? 🎁",
            "Sürprizlerle dolu bir dünya... ✨",
            "Hayatın sürprizlerini kaçırmayın... 🎭"
        ]
    }
    
    # Kullanıcı bilgileri
    users = [
        {"userId": "2Tg5z2v2HmN8Q4RFK5R487sw4zA2", "username": "mehmet"},
        {"userId": "FA98sImRUncS2URa2iUPNxbkZ5v2", "username": "ali"},
        {"userId": "zobdGHSCu7ePF92V5Okx8wA5u113", "username": "aslı"},
        {"userId": "HSdI7KhAgORAqSjZngKzWS3FtLn1", "username": "zeynep"},
        {"userId": "CXlrie41X2QaJupDffb4diGPMNt2", "username": "ayşe"}
    ]
    
    # İlgi alanları
    interests = [
        ["Yemek", "Spor"],
        ["Moda", "Yaşam"],
        ["Sanat", "Bilim"],
        ["Çevre", "Ekonomi"],
        ["Felsefe", "Psikoloji"],
        ["Sağlık", "Moda"],
        ["Bilim", "Film"],
        ["Güzellik", "Moda"]
    ]
    
    # 10 reklam postu oluştur
    for i in range(10):
        # Rastgele duygu seç
        emotion_id, emotion_name = random.choice(list(EMOTION_CATEGORIES.items()))
        
        # Post verilerini oluştur
        post_data = {
            "comments": [],
            "commentsCount": random.randint(0, 10),
            "content": random.choice(ad_contents[emotion_name]),
            "created_at": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%B %d, %Y at %I:%M:%S %p UTC"),
            "emotion": emotion_name,
            "emotionAnalysis": {
                "confidence": round(random.uniform(0.7, 0.95), 2),
                "emotion": emotion_name,
                "timestamp": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%B %d, %Y at %I:%M:%S %p UTC")
            },
            "interests": random.choice(interests),
            "likes": random.randint(10, 100),
            "tags": [emotion_name, "advertisement"],
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%B %d, %Y at %I:%M:%S %p UTC"),
            "userId": random.choice(users)["userId"],
            "username": random.choice(users)["username"],
            "is_ad": True,
            "ad_metadata": {
                "campaign_id": f"campaign_{i+1}",
                "advertiser_id": f"advertiser_{i+1}",
                "target_emotions": [emotion_name],
                "priority": random.uniform(0.5, 1.0)
            }
        }
        
        # Firebase'e kaydet
        await firebase.add_document(COLLECTION_POSTS, post_data)
        print(f"Reklam postu oluşturuldu: {post_data['content']}")

if __name__ == "__main__":
    asyncio.run(create_ad_posts()) 