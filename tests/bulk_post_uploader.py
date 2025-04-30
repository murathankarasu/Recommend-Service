import random
from datetime import datetime, timedelta
from google.cloud import firestore
from google.oauth2 import service_account

EMOTIONS = [
    ("Üzüntü (Sadness)", "The weight of sadness is overwhelming... 🕊️"),
    ("Aşk (Love)", "My heart is full of love... 💝"),
    ("Neşe (Joy)", "Pure joy and happiness! ✨"),
    ("Korku (Fear)", "Can't shake this frightening feeling... 😨"),
    ("Öfke (Anger)", "Need to cool down... 😤"),
    ("Şaşkınlık (Surprise)", "Mind = blown! 🤔")
]

USER_IDS = [
    ("2Tg5z2v2HmN8Q4RFK5R487sw4zA2", "mehmet"),
    ("FA98sImRUncS2URa2iUPNxbkZ5v2", "ali"),
    ("CXlrie41X2QaJupDffb4diGPMNt2", "ayşe"),
    ("HSdI7KhAgORAqSjZngKzWS3FtLn1", "zeynep"),
    ("zobdGHSCu7ePF92V5Okx8wA5u113", "aslı")
]

INTERESTS = ["Yemek", "Spor", "Sanat", "Film", "Teknoloji", "Moda", "Tarih", "Psikoloji", "Felsefe", "Ekonomi", "Çevre", "Sağlık", "Güzellik", "Yaşam", "Müzik", "Politika", "Eğitim"]

TAGS = {
    "Üzüntü (Sadness)": ["Üzüntü (Sadness)"],
    "Aşk (Love)": ["Aşk (Love)"],
    "Neşe (Joy)": ["Neşe (Joy)"],
    "Korku (Fear)": ["Korku (Fear)"],
    "Öfke (Anger)": ["Öfke (Anger)"],
    "Şaşkınlık (Surprise)": ["Şaşkınlık (Surprise)"]
}

CREDENTIALS_PATH = "/Users/murathankarasu/PycharmProjects/Recommendation-Service/src/config/lorien-app-tr-firebase-adminsdk.json"

# Rastgele tarih üretici
def random_datetime():
    now = datetime.now()
    delta = timedelta(days=random.randint(0, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    dt = now - delta
    return dt.strftime("%B %d, %Y at %I:%M:%S %p UTC+3")

def random_comments():
    n = random.randint(0, 10)
    return [f"Comment {i+1}" for i in range(n)]

def random_interests():
    return random.sample(INTERESTS, k=random.randint(1, 3))

def upload_posts():
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    db = firestore.Client(credentials=credentials, project="lorien-app-tr")
    collection = db.collection("posts")
    total = 0
    for emotion, content_text in EMOTIONS:
        for i in range(100):
            user_id, username = random.choice(USER_IDS)
            post = {
                "comments": random_comments(),
                "commentsCount": random.randint(0, 20),
                "content": f"{content_text} (#{i+1})",
                "created_at": random_datetime(),
                "emotion": emotion,
                "emotionAnalysis": {
                    "confidence": round(random.uniform(0.7, 0.99), 10),
                    "emotion": emotion,
                    "timestamp": random_datetime()
                },
                "interests": random_interests(),
                "likes": random.randint(0, 100),
                "tags": TAGS[emotion],
                "timestamp": random_datetime(),
                "userId": user_id,
                "username": username
            }
            doc_ref = collection.document()
            doc_ref.set(post)
            total += 1
            if total % 50 == 0:
                print(f"{total} post yüklendi...")
    print(f"Toplam {total} post başarıyla yüklendi!")

if __name__ == "__main__":
    upload_posts() 