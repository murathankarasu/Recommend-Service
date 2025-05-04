import firebase_admin
from firebase_admin import credentials, firestore
import logging
import traceback
from typing import List, Dict, Any
from datetime import datetime
import os

class FirebaseBase:
    def __init__(self):
        """Firebase servisini başlatır"""
        try:
            print("Firebase servisi başlatılıyor...")
            
            # Firebase Admin SDK sertifika dosyasının yolunu belirle
            cert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'config', 'lorien-app-tr-firebase-adminsdk.json')
            
            # Sadece bir kez initialize et
            if not firebase_admin._apps:
                cred = credentials.Certificate(cert_path)
                firebase_admin.initialize_app(cred)
            
            # Firestore istemcisini oluştur
            self.db = firestore.client()
            
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            
            print("Firebase servisi başarıyla başlatıldı")
            
        except Exception as e:
            print(f"Firebase başlatılırken hata oluştu: {str(e)}")
            print("Hata detayı:")
            print(traceback.format_exc())
            raise Exception(f"Firebase başlatılırken hata oluştu: {str(e)}")

    def get_collection(self, collection_name: str) -> List[Dict[str, Any]]:
        """Belirtilen koleksiyondaki tüm belgeleri getirir"""
        try:
            docs = self.db.collection(collection_name).stream()
            documents = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            return documents
        except Exception as e:
            self.logger.error(f"Koleksiyon getirme hatası: {str(e)}")
            return []

    def add_document(self, collection_name: str, data: Dict[str, Any]) -> str:
        """Koleksiyona yeni belge ekler ve belge ID'sini döndürür."""
        try:
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(data)
            return doc_ref.id
        except Exception as e:
            print(f"Belge eklenirken hata: {str(e)}")
            return None

    def delete_document(self, collection_name: str, doc_id: str) -> None:
        """Belgeyi siler."""
        try:
            self.db.collection(collection_name).document(doc_id).delete()
        except Exception as e:
            print(f"Belge silinirken hata: {str(e)}")

    def delete_collection(self, collection_name: str) -> None:
        """Koleksiyondaki tüm belgeleri siler."""
        try:
            docs = self.db.collection(collection_name).stream()
            for doc in docs:
                doc.reference.delete()
        except Exception as e:
            print(f"Koleksiyon silinirken hata: {str(e)}")

    def get_paginated_data(self, collection_name: str, filters: Dict = None, 
                           order_by: str = None, limit: int = 20, 
                           start_after: str = None) -> List[Dict]:
        """Sayfalama ile veri getir"""
        try:
            query = self.db.collection(collection_name)
            
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)
            
            if order_by:
                query = query.order_by(order_by)
            
            if start_after:
                last_doc = self.db.collection(collection_name).document(start_after).get()
                query = query.start_after(last_doc)
            
            docs = query.limit(limit).stream()
            documents = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                documents.append(doc_data)
            
            return documents
        except Exception as e:
            raise Exception(f"Sayfalı veri getirme hatası: {str(e)}") 