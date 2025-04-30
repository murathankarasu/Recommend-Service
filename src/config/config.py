import os
from dotenv import load_dotenv
from pathlib import Path
import json
import random

# .env dosyasını yükle
load_dotenv()

# Model yolu (korunuyor ama kullanılmıyor)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'emotion_model.pkl')

# Batch boyutu (korunuyor)
BATCH_SIZE = 32

# Epoch sayısı (korunuyor)
EPOCHS = 10

# Öğrenme oranı (korunuyor)
LEARNING_RATE = 0.001

# Firebase yapılandırması
FIREBASE_PROJECT_ID = "lorien-app-tr"
FIREBASE_PROJECT_NUMBER = "647881910037"
FIREBASE_API_KEY = "AIzaSyAIt9DVrwndN-hI0atffVNQ8NvfOrsaAXI"  # Web API Key
FIREBASE_AUTH_DOMAIN = "lorien-app-tr.firebaseapp.com"
FIREBASE_DATABASE_URL = "https://lorien-app-tr-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_STORAGE_BUCKET = "lorien-app-tr.firebasestorage.app"
FIREBASE_MESSAGING_SENDER_ID = "647881910037"
FIREBASE_APP_ID = "1:647881910037:web:497f19126bd8ca4dbfeb1c"
FIREBASE_MEASUREMENT_ID = "G-6JNJPVTNQF"

# Firebase yapılandırma dictionary'si
FIREBASE_CONFIG = {
    "apiKey": FIREBASE_API_KEY,
    "authDomain": FIREBASE_AUTH_DOMAIN,
    "databaseURL": FIREBASE_DATABASE_URL,
    "projectId": FIREBASE_PROJECT_ID,
    "storageBucket": FIREBASE_STORAGE_BUCKET,
    "messagingSenderId": FIREBASE_MESSAGING_SENDER_ID,
    "appId": FIREBASE_APP_ID,
    "measurementId": FIREBASE_MEASUREMENT_ID
}

# Firebase koleksiyon isimleri
COLLECTION_USERS = 'users'
COLLECTION_POSTS = 'posts'
COLLECTION_USER_PATTERNS = 'userEmotionPatterns'
COLLECTION_ADS = 'ads'
COLLECTION_AD_METRICS = 'adMetrics'
COLLECTION_INTERACTIONS = 'userEmotionInteractions'
COLLECTION_POST_METRICS = 'postMetrics'
COLLECTION_USER_EMOTION_HISTORY = 'userEmotionHistory'

# API yapılandırması
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('PORT', 8000))  # Railway için PORT env variable'ını kullan

# Duygu kategorileri (güncellendi)
EMOTION_CATEGORIES = {
    0: "Üzüntü (Sadness)",
    1: "Neşe (Joy)",
    2: "Aşk (Love)",
    3: "Öfke (Anger)",
    4: "Korku (Fear)",
    5: "Şaşkınlık (Surprise)"
}

# Duygu kategorileri listesi (API için)
EMOTION_CATEGORIES_LIST = list(EMOTION_CATEGORIES.values())

# Cold start parametreleri
COLD_START_THRESHOLD = 20  # Minimum etkileşim sayısı
RANDOM_RECOMMENDATION_COUNT = 10  # Rastgele öneri sayısı

# Pattern analizi parametreleri
TIME_WINDOW = 24  # Saat cinsinden zaman penceresi
EMOTION_WEIGHT = 0.7  # Duygu ağırlığı
TIME_WEIGHT = 0.3  # Zaman ağırlığı

# Reklam etiketi yapılandırması
AD_TAG = 'advertise'
AD_METRIC_TYPES = ['impression', 'click', 'view']
AD_EMOTION_WEIGHTS = {
    "Üzüntü (Sadness)": 0.8,
    "Neşe (Joy)": 1.0,
    "Aşk (Love)": 0.9,
    "Öfke (Anger)": 0.6,
    "Korku (Fear)": 0.7,
    "Şaşkınlık (Surprise)": 0.8
}

# Reklam metrik hesaplama parametreleri
CTR_THRESHOLD = 0.02  # Minimum tıklama oranı
IMPRESSION_THRESHOLD = 100  # Minimum gösterim sayısı
EMOTION_SCORE_WEIGHT = 0.4  # Duygu skoru ağırlığı
INTERACTION_WEIGHT = 0.6  # Etkileşim ağırlığı

# Reklam yapılandırması
AD_CONFIG = {
    'frequency': random.randint(5, 7),  # Her 5-7 içerikte 1 reklam
    'content_ratio': 0.8,  # İçerik oranı
    'ad_ratio': 0.2  # Reklam oranı
}

# Reklam parametreleri
AD_FREQUENCY = 5  # Her 5 içerikte 1 reklam
AD_CONTENT_RATIO = 0.8  # İçerik oranı
AD_RATIO = 0.2  # Reklam oranı
AD_LEARNING_RATE = 0.05  # Reklam etkileşimleri için öğrenme oranı
MIN_AD_RELEVANCE = 0.3  # Minimum reklam uygunluk skoru

# Etkileşim ağırlıkları
INTERACTION_TYPE_WEIGHTS = {
    'like': 0.1,      # Beğeni: %10 ağırlık
    'comment': 0.15,  # Yorum: %15 ağırlık
    'create': 0.2,    # Paylaşım: %20 ağırlık
    'post': 0.2,      # Paylaşım: %20 ağırlık
    'ad_click': 0.1,  # Reklam tıklama: %10 ağırlık
    'ad_view': 0.05,  # Reklam görüntüleme: %5 ağırlık
    'ignore': -0.03,  # Göz ardı etme: -%3 ağırlık
    'dislike': -0.05  # Beğenmeme: -%5 ağırlık
}

# Zaman bazlı ağırlık azalması
TIME_DECAY_WEIGHTS = {
    '24h': 1.0,        # Son 24 saat: %100 ağırlık
    '7d': 0.5,         # Son 7 gün: %50 ağırlık
    'older': 0.25      # 7 günden eski: %25 ağırlık
}

# Günlük ağırlık azalması
DAILY_WEIGHT_DECAY = 0.05  # Her gün %5 azalma

# Duygu değişimi bonusları
EMOTION_CHANGE_BONUS = {
    'new_emotion': 0.15,  # Yeni duygu kategorisi: %15 bonus
    'old_emotion': -0.10  # Eski duygu kategorisi: %10 ceza
}

# Zıt duygu eşleştirmesi (güncellendi)
OPPOSITE_EMOTIONS = {
    "Üzüntü (Sadness)": ["Neşe (Joy)", "Aşk (Love)"],
    "Neşe (Joy)": ["Üzüntü (Sadness)", "Korku (Fear)"],
    "Aşk (Love)": ["Öfke (Anger)", "Korku (Fear)"],
    "Öfke (Anger)": ["Aşk (Love)", "Neşe (Joy)"],
    "Korku (Fear)": ["Neşe (Joy)", "Aşk (Love)"],
    "Şaşkınlık (Surprise)": ["Üzüntü (Sadness)", "Korku (Fear)"]
}

# Süreklilik kontrolü için pencere boyutu
CONTINUITY_WINDOW = 5  # Son 5 etkileşimde aynı duygu baskınsa

# Reklam metrikleri
AD_METRIC_WEIGHTS = {
    'impressions': 0.2,
    'clicks': 0.3,
    'ctr': 0.4,
    'emotion_changes': 0.1
}

# Reklam duygu etkisi (güncellendi)
AD_EMOTION_IMPACT = {
    "Üzüntü (Sadness)": 0.6,
    "Neşe (Joy)": 0.8,
    "Aşk (Love)": 0.9,
    "Öfke (Anger)": 0.4,
    "Korku (Fear)": 0.3,
    "Şaşkınlık (Surprise)": 0.5
}

# İçerik Kalite Metrikleri
CONTENT_QUALITY_METRICS = {
    'engagement_rate': 0.4,      # Etkileşim oranı
    'freshness': 0.3,           # İçeriğin yeniliği
    'user_reputation': 0.2,     # Kullanıcı itibarı
    'content_length': 0.1       # İçerik uzunluğu
}

# Duygu Geçiş Matrisi (güncellendi)
EMOTION_TRANSITION_MATRIX = {
    "Üzüntü (Sadness)": {
        "Üzüntü (Sadness)": 0.6,
        "Neşe (Joy)": 0.1,
        "Aşk (Love)": 0.1,
        "Öfke (Anger)": 0.05,
        "Korku (Fear)": 0.1,
        "Şaşkınlık (Surprise)": 0.05
    },
    "Neşe (Joy)": {
        "Üzüntü (Sadness)": 0.1,
        "Neşe (Joy)": 0.6,
        "Aşk (Love)": 0.1,
        "Öfke (Anger)": 0.1,
        "Korku (Fear)": 0.05,
        "Şaşkınlık (Surprise)": 0.05
    },
    "Aşk (Love)": {
        "Üzüntü (Sadness)": 0.1,
        "Neşe (Joy)": 0.1,
        "Aşk (Love)": 0.6,
        "Öfke (Anger)": 0.05,
        "Korku (Fear)": 0.1,
        "Şaşkınlık (Surprise)": 0.05
    },
    "Öfke (Anger)": {
        "Üzüntü (Sadness)": 0.1,
        "Neşe (Joy)": 0.1,
        "Aşk (Love)": 0.05,
        "Öfke (Anger)": 0.6,
        "Korku (Fear)": 0.1,
        "Şaşkınlık (Surprise)": 0.05
    },
    "Korku (Fear)": {
        "Üzüntü (Sadness)": 0.1,
        "Neşe (Joy)": 0.1,
        "Aşk (Love)": 0.05,
        "Öfke (Anger)": 0.1,
        "Korku (Fear)": 0.6,
        "Şaşkınlık (Surprise)": 0.05
    },
    "Şaşkınlık (Surprise)": {
        "Üzüntü (Sadness)": 0.1,
        "Neşe (Joy)": 0.2,
        "Aşk (Love)": 0.1,
        "Öfke (Anger)": 0.1,
        "Korku (Fear)": 0.1,
        "Şaşkınlık (Surprise)": 0.4
    }
}

# Kullanıcı Profili Faktörleri
USER_PROFILE_FACTORS = {
    'interests': 0.3,           # İlgi alanları
    'demographics': 0.2,        # Demografik bilgiler
    'behavioral_patterns': 0.3, # Davranışsal desenler
    'social_connections': 0.2   # Sosyal bağlantılar
}

# Zaman Bazlı Optimizasyon
TIME_BASED_OPTIMIZATION = {
    'peak_hours': {
        'start': '09:00',
        'end': '22:00',
        'weight_multiplier': 1.2
    },
    'off_peak_hours': {
        'weight_multiplier': 0.8
    }
}

# İçerik Çeşitliliği Kontrolleri
DIVERSITY_CONTROLS = {
    'max_similar_content': 20,    # Ardışık benzer içerik sayısı (artık 20)
    'min_diversity_ratio': 0.3,  # Minimum çeşitlilik oranı
    'topic_rotation': 0.2        # Konu rotasyonu ağırlığı
}

# Etkileşim Kalite Metrikleri
INTERACTION_QUALITY_METRICS = {
    'duration': 0.3,            # Etkileşim süresi
    'depth': 0.4,              # Etkileşim derinliği
    'frequency': 0.2,          # Etkileşim sıklığı
    'recency': 0.1             # Etkileşim yeniliği
}

# Duygu Analizi Güven Skoru
EMOTION_ANALYSIS_CONFIDENCE = {
    'high_confidence_threshold': 0.8,
    'medium_confidence_threshold': 0.6,
    'low_confidence_threshold': 0.4
}

# Reklam Optimizasyonu
AD_OPTIMIZATION = {
    'relevance_threshold': 0.7,
    'frequency_cap': 3,         # Günlük maksimum reklam gösterimi
    'placement_strategy': {
        'beginning': 0.2,
        'middle': 0.6,
        'end': 0.2
    }
}

# Kullanıcı Davranış Analizi
BEHAVIOR_ANALYSIS = {
    'session_duration': 0.3,
    'scroll_depth': 0.2,
    'interaction_patterns': 0.3,
    'content_preferences': 0.2
}

# Sistem Performans Metrikleri
PERFORMANCE_METRICS = {
    'response_time_threshold': 0.5,  # Saniye
    'cache_hit_ratio': 0.8,
    'error_rate_threshold': 0.01,
    'scaling_factor': 1.2
} 