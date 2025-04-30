import asyncio
import random
import os
import sys
from datetime import datetime, timedelta

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(project_root)

from services.firebase_service import FirebaseService
from config import EMOTION_CATEGORIES

# Kullanıcı bilgileri
USERS = [
    {"id": "zobdGHSCu7ePF92V5Okx8wA5u113", "username": "aslı"},
    {"id": "2Tg5z2v2HmN8Q4RFK5R487sw4zA2", "username": "mehmet"},
    {"id": "CXlrie41X2QaJupDffb4diGPMNt2", "username": "ayşe"},
    {"id": "FA98sImRUncS2URa2iUPNxbkZ5v2", "username": "ali"},
    {"id": "HSdI7KhAgORAqSjZngKzWS3FtLn1", "username": "zeynep"}
]

# İlgi alanları
INTERESTS = [
    ["Sanat", "Bilim", "Film", "Müzik"],
    ["Spor", "Teknoloji", "Yemek", "Seyahat"],
    ["Edebiyat", "Tarih", "Felsefe", "Psikoloji"],
    ["Moda", "Güzellik", "Sağlık", "Yaşam"],
    ["Ekonomi", "Politika", "Eğitim", "Çevre"]
]

# Post içerikleri (duygu bazlı)
POST_CONTENTS = {
    'Üzüntü (Sadness)': [
        "Feeling deeply sad today... 😔",
        "Missing someone special... 💔",
        "Sometimes life feels heavy... 😢",
        "Lost in melancholy... 🌧️",
        "The weight of sadness is overwhelming... 🕊️"
    ],
    'Neşe (Joy)': [
        "Feeling absolutely joyful today! 🎉",
        "Can't stop smiling! 🌟",
        "Life is full of wonderful moments! 🌈",
        "Dancing with happiness! 💃",
        "Pure joy and happiness! ✨"
    ],
    'Aşk (Love)': [
        "Love is in the air! ❤️",
        "My heart is full of love... 💝",
        "Feeling deeply connected... 💑",
        "Love makes everything beautiful! 🌹",
        "Grateful for this loving moment... 💕"
    ],
    'Öfke (Anger)': [
        "This situation is infuriating! 😠",
        "Can't contain my anger anymore! ⚡",
        "Absolutely furious right now! 💢",
        "This crossed all lines! 🔥",
        "Need to cool down... 😤"
    ],
    'Korku (Fear)': [
        "Feeling really anxious... 😰",
        "Fear is creeping in... 🌫️",
        "Can't shake this frightening feeling... 😨",
        "Terrified of what's coming... ⚡",
        "This uncertainty is scary... 🕷️"
    ],
    'Şaşkınlık (Surprise)': [
        "I can't believe what just happened! 😮",
        "This is completely unexpected! 🤯",
        "What a shocking turn of events! 😲",
        "Totally caught off guard! 💫",
        "Mind = blown! 🤔"
    ]
}

# Duygu kategorileri eşleştirmesi
EMOTION_MAPPING = {
    0: "Üzüntü (Sadness)",
    1: "Neşe (Joy)",
    2: "Aşk (Love)",
    3: "Öfke (Anger)",
    4: "Korku (Fear)",
    5: "Şaşkınlık (Surprise)"
}

def get_random_timestamp():
    # Son bir ay içinde rastgele bir tarih oluştur
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    random_date = start_date + timedelta(
        seconds=random.randint(0, int((end_date - start_date).total_seconds()))
    )
    return random_date.strftime("%B %d, %Y at %I:%M:%S %p UTC%z")

async def generate_posts():
    firebase_service = FirebaseService()
    
    # Her duygu için 20 post oluştur
    for emotion_id, emotion in EMOTION_MAPPING.items():
        for _ in range(20):
            # Rastgele bir kullanıcı seç
            user = random.choice(USERS)
            
            # Post verilerini hazırla
            post_data = {
                "userId": user["id"],
                "username": user["username"],
                "content": random.choice(POST_CONTENTS[emotion]),
                "emotion": emotion,
                "emotionAnalysis": {
                    "emotion": emotion,
                    "confidence": random.uniform(0.7, 0.95),
                    "timestamp": get_random_timestamp()
                },
                "interests": random.sample(INTERESTS[USERS.index(user)], 2),
                "likes": random.randint(0, 100),
                "commentsCount": random.randint(0, 20),
                "comments": [],
                "tags": [emotion],
                "timestamp": get_random_timestamp()
            }
            
            # Postu Firebase'e ekle
            await firebase_service.add_post(post_data)
            print(f"Post added: {emotion} - {user['username']}")

if __name__ == "__main__":
    asyncio.run(generate_posts()) 