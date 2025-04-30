import json
from datetime import datetime, timezone
from google.cloud import firestore
from google.oauth2 import service_account

def create_mock_emotion_interaction(
    confidence: float,
    content_id: str,
    emotion: str,
    timestamp: str,
    interaction_type: str,
    user_id: str
) -> dict:
    return {
        "confidence": confidence,
        "content_id": content_id,
        "emotion": emotion,
        "timestamp": timestamp,
        "interactionType": interaction_type,
        "user_id": user_id
    }

def save_interaction_to_firestore(interaction: dict):
    credentials = service_account.Credentials.from_service_account_file(
        "/Users/murathankarasu/PycharmProjects/Recommendation-Service/src/config/lorien-app-tr-firebase-adminsdk.json"
    )
    db = firestore.Client(credentials=credentials, project="lorien-app-tr")
    doc_ref = db.collection("userEmotionInteractions").document()
    doc_ref.set(interaction)
    print(f"Etkileşim Firestore'a kaydedildi! (doc id: {doc_ref.id})")

if __name__ == "__main__":
    mock_data = create_mock_emotion_interaction(
        confidence=0.9697472962223538,
        content_id="joy_post_16",
        emotion="Neşe (Joy)",
        timestamp=datetime.now(timezone.utc).isoformat(),
        interaction_type="dislike",
        user_id="isRKPOpG4zVFmULHJjrsvY8t1Nb2"
    )

    # Firestore'a kaydet
    save_interaction_to_firestore(mock_data)

    # Konsola yazdır
    print(json.dumps(mock_data, ensure_ascii=False, indent=2))

    # Dosyaya da kaydedebilirsin
    with open("mock_emotion_interaction.json", "w", encoding="utf-8") as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)