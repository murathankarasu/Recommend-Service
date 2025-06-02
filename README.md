# Lorien

This project features an empathy-driven algorithm that recommends content and ads based on the emotional patterns detected in user interactions.

## Features

- Emotion-based content recommendations
- Smart ad placement
- Analysis of user emotion patterns
- Firebase integration
- RESTful API

## Installation

1. Install the requirements:
```bash
pip install -r src/requirements.txt
```

2. Set up environment variables:
- Copy `.env.example` to `.env`
- Add your Firebase credentials in base64 format to the `FIREBASE_CREDENTIALS` variable

3. Start the application:
```bash
cd src
python app.py
```

## API Endpoints

### GET /api/recommendations/{user_id}
Returns personalized content and ad recommendations for the user.

### POST /api/track_interaction
Records user interactions.

Sample request:
```json
{
    "userId": "user123",
    "postId": "post456",
    "interactionType": "like",
    "emotion": "Joy",
    "confidence": 0.9
}
```

---

# Detailed Explanation of Algorithms and Functions

This section provides a detailed explanation of all main algorithms and helper modules of the recommendation system. The purpose, parameters, operation, and sample flows of each function are described in detail.

## 1. Main Flow: Providing Recommendations to the User

### `GET /api/recommendations/<user_id>`
This endpoint returns personalized content and ad recommendations for a user. The flow is as follows:

1. **Retrieve User Interactions:**
   - The user's past interactions are fetched with `firebase.get_user_interactions(user_id)`.
   - If there are no interactions, the cold start algorithm is triggered.

2. **Retrieve Content Pool:**
   - All content is fetched with `firebase_post.get_all_posts()`.

3. **Emotion Pattern Analysis:**
   - The user's emotional tendencies are extracted with `emotion_analyzer.analyze_pattern(user_interactions, user_id)`.
   - Result: A ratio between 0-1 for each emotion.

4. **Filtering Recently Shown Content:**
   - Recently shown content is determined with `get_recent_shown_post_ids(user_interactions)`.

5. **Personalized Content Mix:**
   - A content mix is created based on the user's emotion pattern and history with `content_recommender.get_content_mix(...)`.

6. **Adding Ads:**
   - Ads are inserted into appropriate places with `ad_manager.insert_ads(content_mix, user_id)`.

7. **A/B Testing and Logging:**
   - The recommendation and parameters are logged with `log_recommendation_event(...)`.

8. **Returning the Response:**
   - The result is returned with recommendations and the emotion pattern.

---

## 2. Cold Start Algorithm

### `get_cold_start_content(all_contents, emotion_categories, limit)`
Creates a recommendation list consisting of diverse and popular content for users with no interactions.

- **At least 1 content from each emotion** is added (if available).
- Remaining slots are filled based on popularity (like + comment + view score).
- The result is shuffled and limited to the specified number of content.

**Parameters:**
- `all_contents`: List of all content (dict).
- `emotion_categories`: List of emotion categories.
- `limit`: Number of content to return.

**Sample Flow:**
1. Select a random content from each emotion.
2. Fill remaining slots with popular content.
3. Shuffle and return the results.

---

## 3. Emotion Pattern Analysis

### `analyze_pattern(user_interactions, user_id)`
Analyzes which emotions the user responds to most based on past interactions.

- Each interaction's emotion is weighted.
- As a result, a ratio between 0-1 is obtained for each emotion.
- These ratios are used in the recommendation algorithm to rank content.

**Parameters:**
- `user_interactions`: List of user interactions.
- `user_id`: User ID.

**Example:**
- If the user selected "Joy" in 6 out of 10 interactions and "Love" in 4:
  - `{"Joy": 0.6, "Love": 0.4, ...}`

### Always-Up-to-Date Emotion Pattern
The user's emotion pattern is recalculated and updated on **every** feed request, ensuring that recommendations always reflect the user's most recent interactions and emotional state.

---

## 4. Content Mix and Ranking

### `get_content_mix(contents, emotion_pattern, limit, shown_post_ids)`
Creates a new content mix based on the user's emotion pattern and previously seen content.

- Previously shown content is excluded.
- Content is weighted according to the user's dominant emotions.
- A small randomness is added for content with the same score (`shuffle_same_score`).
- The result is limited to the specified number of content.

**Parameters:**
- `contents`: All content.
- `emotion_pattern`: User's emotion pattern.
- `limit`: Number of content to return.
- `shown_post_ids`: IDs of previously shown content.

---

## 5. Helper Modules

### `user_history_utils.py`
- Returns the IDs of the most recently shown content to the user.
- Used to prevent repeated content.

### `shuffle_utils.py`
- Shuffles content with the same score among themselves.
- Prevents the recommendation list from being monotonous.

### `date_utils.py`
- Safely parses different timestamp formats and normalizes to UTC.
- Reduces the risk of errors in date operations.

### `ab_test_logger.py`
- Logs A/B tests and parameters used in the recommendation algorithm.
- Used in the analysis of results.

### `cold_start_utils.py`
- Creates a recommendation mix for cold start (new user).
- Ensures a balance of emotion diversity and popularity.

---

## 6. Ad Placement

### `ad_manager.insert_ads(content_mix, user_id)`
- Adds ads to the content mix according to the user's emotion pattern and interests.
- Ads are placed at certain intervals and according to priority order.
- Each ad's target emotions and priority are taken into account.

---

## 7. Recording User Interaction

### `POST /api/track_interaction`
- When a user interacts with content (like, comment, emotion selection, etc.), this endpoint is called.
- The interaction is recorded in Firebase.
- Content interaction statistics are updated.

**Parameters:**
- `userId`: User ID
- `postId`: Content ID
- `interactionType`: Type of interaction (like, comment, view, emotion, etc.)
- `emotion`: Emotion selected by the user
- `confidence`: Emotion detection confidence score

---

## 8. A/B Test Logic

- Users can be assigned to different algorithm/parameter variants randomly or by certain rules.
- For each recommendation request, which variant was used and the results are logged.
- The results are analyzed to determine the best performing algorithm/parameters.

---

## 9. Algorithm Flow (Summary)

1. A recommendation request is received from the user.
2. User interactions and content pool are fetched.
3. If there are no interactions, the cold start algorithm runs.
4. If there are, the emotion pattern is analyzed and a content mix is created.
5. Ads are added to appropriate places.
6. The result and parameters are logged.
7. The recommendation list and emotion pattern are returned as the API response.

---

## 10. Notes for Developers

- Each function and module is written to be easily testable and independent.
- Helper modules can be used independently in other projects.
- The entire code is compatible with Python 3.8+.
- Environment variables must be set correctly for Firebase integration.

---

## 11. Dynamic Emotion Pattern and Stretching Mechanism

The recommendation system continuously updates and personalizes itself according to the user's interactions. This process consists of two main flows:

### a) Personalization (As Interactions Occur)
- As the user interacts with content in the recommended feed (like, comment, emotion), these interactions are analyzed.
- With each new interaction, the user's **emotion pattern** is recalculated.
- For example, if the user likes "Joy" content more, the "Joy" ratio increases; if they never interact with "Anger" content, the "Anger" ratio decreases.
- In subsequent feeds, recommendations are weighted according to this updated emotion pattern and become increasingly personalized.

### b) Stretching (If No Interaction Occurs)
- If the user gives **no meaningful interaction** (like, comment, emotion) to the recommended feed, the system automatically activates the stretching logic.
- In stretching logic:
  - The dominant emotion ratio is pulled to 50%.
  - The remaining 50% is equally shared among all other emotions.
- Thus, when the user is uninterested, the system automatically increases diversity and avoids monotony.
- When the user starts interacting again, the system returns to the personalized pattern.

**In summary:**
- As the user interacts, the percentages change and the recommendation system becomes smarter and more personal.
- If the user is uninterested, the system automatically increases diversity.

---

## 12. Normalization of Emotion Distribution and the Problem of Getting Stuck on a Single Emotion

As the number of users increases, some users may constantly respond to a single emotion (e.g., "Joy"), which can negatively affect the diversity and personalization quality of the recommendation system. The following mechanisms are implemented in the project to solve this problem:

### 1. Weighted Average and Update
- The user's emotion distribution history is updated with a weighted average. That is, new interactions may have less or more weight than old ones.
- Thus, even if there is an excessive response to a single emotion, the distribution is softened over time.

### 2. Stretching Mechanism (Feed Stretching)
- If a user does not give meaningful interaction to the recommended content for a long time (e.g., never likes/comments/selects emotion), the system automatically activates the "stretching" logic.
- During stretching:
  - The user's dominant emotion ratio is pulled to 50%.
  - The remaining 50% is equally distributed among all other emotions.
- Thus, the system prevents getting stuck on a single emotion and increases diversity.

### 3. Emotion Diversity Requirement
- Functions that guarantee at least one content from each emotion in the recommendation list are used.
- This is especially activated during cold start and content mix creation.

### 4. Detection of Getting Stuck on a Single Emotion
- It is detected whether the user is stuck on a single emotion in their last N interactions.
- For example, if a user has selected "Joy" in 8 out of their last 10 interactions, the system detects this and acts to increase recommendation diversity.

### 5. Time-Updated Distribution
- Users' emotion distributions are continuously updated over time and with new interactions.
- The weight of old interactions decreases, and new interactions become more effective (e.g., with weighted average or decay mechanism).

**In summary:**
- Getting stuck on a single emotion is detected by the system and recommendation diversity is automatically increased.
- Emotion distribution is normalized: with stretching, weighted average, and diversity requirement.
- Even as the number of users increases, the quality and diversity of recommendations are preserved.

---

## 13. Additional Features and Other Architectural Details

### User Behavior Analysis and Profile Factors
The system considers not only emotional interactions but also the user's interests, demographic information, behavioral patterns, and social connections. These factors affect the profile score in the recommendation algorithm and enable more personalized recommendations.

### Emotion Transition Matrix and Transition Analysis
Users' tendencies to transition from one emotion to another are modeled with the `EMOTION_TRANSITION_MATRIX` in the system. This matrix helps the recommendation algorithm predict possible mood changes and provide content diversity accordingly.

### Time-Based Weighting and Recency
The time factor is important in user interactions. Interactions from the last 24 hours, last 7 days, and older are considered with different weights. Thus, the system becomes more sensitive to the user's current mood.

### Content Quality and Engagement Metrics
Content to be recommended is scored not only by emotion but also by engagement rate, content freshness, author reputation, and content length. This prevents low-quality or old content from being recommended.

### Ad Optimization and Emotion-Based Targeting
Ads are placed according to the user's emotion pattern and interests. Each ad has target emotions and priority scores. In addition, the frequency and placement of ads are optimized.

### Confidence Score and Emotion Analysis Reliability
During emotion detection, a confidence score is assigned to the model's prediction. The system considers predictions with low confidence scores as less effective and takes this score into account in the recommendation algorithm.

### A/B Testing and Parameter Tracking
The system can test different algorithm and parameter variants live. For each recommendation request, which variant was used and the results are logged. Thus, the best performing structure can be automatically detected.

### Error Handling and Logging
All main functions have error catching and logging mechanisms. Thus, errors in the system can be easily detected and quickly intervened.

### Developer-Friendly Architecture
Thanks to the modular structure of the code, new algorithms or metrics can be easily added. Helper modules are designed independently so that they can be used in other projects as well.

---

For any contributions, suggestions, or bug reports, please open an issue or send a pull request.

## Railway Deployment

1. Install the Railway CLI
2. Set environment variables from the Railway dashboard:
   - `FIREBASE_CREDENTIALS`
   - `PORT` (Railway will set automatically)
3. Deploy:
```bash
railway up
```

## 14. Analysis and Optimization of Ads According to Emotional State

The system analyzes the emotional impact of ads on users. When a user interacts with an ad (e.g., click, view), the current emotional state and the emotion category targeted by the ad are recorded. This data is used to understand in which emotional states ads are more effective and to optimize ad placement.

- **Emotion-Performance Correlation:** The display and interaction rates of ads in different emotional states are analyzed.
- **Dynamic Ad Placement:** The user's current emotion pattern directly affects the frequency and type of ads.
- **Ad Interaction Score:** For each ad, separate interaction scores are kept for different emotions, and these scores are considered in the recommendation algorithm.

---

## 15. Scalability and Performance

The system is designed to be scalable against increasing numbers of users and content.
- **Batch Operations and Asynchronous Structure:** Asynchronous functions and batch data processing methods are used to prevent performance loss when working with large datasets.
- **Cache and Optimization:** Caching mechanisms are applied for frequently used data and calculations.

---

## License

Lori

## 16. Handling Dislike Interactions and Gradual Emotion Suppression

When a user gives a **dislike** interaction to a content with a specific emotion, the system dynamically reduces the weight of that emotion in the user's emotion pattern:

- **First Dislike:**
  - If the emotion's ratio in the pattern is above 50%, it is immediately reduced to 50%.
- **Subsequent Dislikes:**
  - If the emotion's ratio is already below 50%, each new dislike further reduces the ratio by 2.5% (i.e., `ratio = ratio * 0.975`).
- This ensures that repeated dislikes do not instantly zero out the emotion, but gradually decrease its influence in recommendations.
- The pattern is always normalized after these adjustments.

**Example:**
- Initial: `{"Joy": 0.7, "Love": 0.2, ...}`
- After first dislike on Joy: `{"Joy": 0.5, ...}`
- After another dislike on Joy: `{"Joy": 0.4875, ...}`
- And so on, with each dislike causing a softer reduction.

This mechanism prevents a single emotion from dominating the feed and allows the system to adapt to the user's negative feedback in a controlled, gradual way.

## 17. No Interaction (Stretching) Mechanism

If the user does **not interact** with any content in the feed (no like, dislike, comment, vs.), the system automatically activates a stretching mechanism to increase diversity:

- The dominant emotion's ratio in the pattern is pulled down to 50%.
- The remaining 50% is distributed equally among all other emotions.
- This prevents the system from getting stuck on a single emotion and ensures the user is exposed to a wider variety of emotional content.
- As soon as the user starts interacting again, the pattern returns to being dynamically updated based on their new interactions.

**Example:**
- Before: `{"Joy": 0.8, "Love": 0.1, "Sadness": 0.1, ...}`
- After no interaction: `{"Joy": 0.5, "Love": 0.1, "Sadness": 0.1, ...}` (the rest is distributed equally)

This mechanism helps keep the recommendations fresh and engaging, even for passive or indecisive users.

## 18. Feed Content Uniqueness and Repeat Handling

The recommendation algorithm prioritizes showing content that the user has **not seen before** in each feed request:

- **Primary Goal:** Always fill the feed with as many new (unseen) posts as possible.
- **If there are not enough new posts:** The remaining slots are filled with previously shown posts (repeats), but only as much as needed to reach the feed limit (e.g., 20 posts).
- **Diversity:** The algorithm still ensures at least one post from each emotion if available, and applies emotion pattern and diversity rules.
- **Result:** Users are exposed to fresh content as much as possible, and only see repeats when the content pool is insufficient.

**Example:**
- If there are 15 new posts and 5 repeats needed, the feed will contain 15 new + 5 repeated posts.
- If there are 20 or more new posts, the feed will contain only new posts.

This mechanism keeps the user experience fresh and prevents monotony, while guaranteeing the feed is always fully populated.

### Feed Reset When No Unseen Content Remains
If there are no unseen (previously unshown) posts left for the user, the system does **not** fall back to the cold start algorithm. Instead, the user's feed history (`userShownFeeds`) is automatically cleared, and the feed is regenerated from scratch using the user's current emotion pattern. This ensures that the user always receives recommendations aligned with their latest emotional tendencies, even after exhausting all available content.

## 19. Automatic Feed History Reset for Scalability

To keep the backend scalable and cost-effective for social media use cases, the system automatically resets the user's feed history if there is no feed request for a certain period (e.g., 10 minutes):

- **Mechanism:**
  - On each feed request, the user's last feed activity timestamp is updated.
  - If a new feed request arrives after more than 10 minutes of inactivity, all previous feed history (shown post IDs) is deleted.
  - The next feed is generated as if the user is starting fresh (no shown post IDs).
- **Benefits:**
  - Prevents the backend database from growing indefinitely with old feed history.
  - Reduces storage costs and keeps the system performant.
  - Ensures that users who return after a long break get a fresh feed experience.

**Example:**
- User requests a feed, sees 20 posts, and then leaves the app.
- If the user returns after 15 minutes, their previous feed history is cleared and a new feed is generated from scratch.

This mechanism is especially useful for high-traffic social media apps to keep server resources under control.

## 20. Feed History Size Limit

To further optimize backend performance and cost, the system enforces a maximum feed history limit per user (default: 100 feeds):

- **If a user's feed history exceeds 100 records, the oldest records are automatically deleted.**
- This ensures that even highly active users do not cause unbounded growth in the backend database.
- The limit can be adjusted as needed for different scalability requirements.

This approach keeps the system efficient and cost-effective for all user activity levels.

---

## 21. Story-Driven Feed Flow, Emotion Transitions & Striking Ad Placement (NEW)

### Personalized Story Flow & Emotion Journey
Our recommendation engine now crafts each user's feed as a unique emotional journey—a story tailored to their habits and emotional transitions. Instead of a random or static list, the feed is dynamically sequenced to reflect the user's most common and impactful emotion transitions, creating a narrative arc that feels natural and engaging.

- **Emotion Transition Analysis:**
  - The system analyzes the user's recent interactions to build a personalized emotion transition matrix (e.g., how often does the user move from "Sadness" to "Joy"?).
  - The feed is then ordered to reflect these transitions, maximizing emotional resonance and engagement.

- **Story-Like Sequencing:**
  - Content is arranged to follow the user's typical emotional journey, with smooth or dramatic transitions (e.g., "Sadness → Hope → Joy").
  - This approach increases session time and user satisfaction by making the feed feel like a meaningful, evolving experience rather than a random scroll.

### Striking Ad Placement at the Emotional Peak
Ads are no longer just inserted at fixed intervals—they are now strategically placed at the most emotionally striking moments in the user's story flow.

- **Peak Moment Detection:**
  - The system identifies the most impactful emotion transition in the feed (e.g., a rare or high-contrast shift such as "Fear → Love" or "Sadness → Joy").
  - This is determined by analyzing the user's emotion pattern and the feed's emotional arc, focusing on transitions with the greatest emotional delta or positive/negative polarity change.

- **Ad Insertion at the Climax:**
  - The top-performing ad is inserted immediately after this peak transition, ensuring maximum attention and emotional relevance.
  - This method leverages the user's heightened emotional state, dramatically increasing ad recall and click-through rates.

### Data-Driven Story Analytics for Marketing
- **Every user's story flow and emotion transitions are stored in Firebase for analytics.**
- Marketers and product teams can:
  - Track which emotional journeys are most common or most effective for engagement.
  - Analyze how ad performance correlates with specific emotional peaks or transitions.
  - Design campaigns that align with the user's natural emotional flow, not against it.

### Why This Matters
- **Unmatched Personalization:** Every feed is a unique, evolving story, not just a list.
- **Emotional Resonance:** Users feel understood and engaged, leading to longer sessions and higher satisfaction.
- **Ad Effectiveness:** Ads appear at the most memorable, emotionally charged moments, maximizing impact and ROI.
- **Actionable Insights:** The system provides rich analytics on user emotion journeys and ad performance, enabling smarter marketing and product decisions.

**This is not just recommendation—it's emotional storytelling at scale.**

## 12. Gelişmiş Reklam Yerleştirme ve Performans Takibi

### a) Keyword Tabanlı Reklam Seçimi
- Reklamlar, içerik keywordleri ile eşleştirilerek seçilir
- Jaccard benzerliği kullanılarak keyword uygunluğu hesaplanır
- Duygu uygunluğu ve keyword uygunluğu birlikte değerlendirilir
- Ağırlıklar:
  - Duygu uygunluğu: %30
  - Keyword uygunluğu: %30
  - Performans metrikleri: %40

### b) Performans Metrikleri
- Son 30 günlük reklam performans verileri takip edilir:
  - CTR (Click-Through Rate)
  - Duygu değişim oranları
  - Toplam gösterim sayısı
  - Toplam tıklama sayısı
  - Duygu değişim skorları

### c) Yüksek Performanslı Reklamlar
- Toplam skoru 0.7'den yüksek ve CTR'si %2'den yüksek reklamlar "yüksek performanslı" olarak işaretlenir
- Bu reklamlar arasından rastgele seçim yapılır (çeşitlilik için)
- Performans skoru hesaplama:
  ```python
  performance_score = (
      ctr * AD_PERFORMANCE_WEIGHTS['ctr'] +
      emotion_change_score * AD_PERFORMANCE_WEIGHTS['emotion_change']
  )
  ```

### d) Metrik Toplama Noktaları
1. Reklam Gösterimi:
   ```json
   {
       "ad_id": "reklam123",
       "user_id": "kullanici456",
       "emotion_before": "Neşe (Joy)",
       "emotion_after": "Neşe (Joy)"
   }
   ```

2. Reklam Tıklaması:
   ```json
   {
       "ad_id": "reklam123",
       "user_id": "kullanici456",
       "emotion_before": "Neşe (Joy)",
       "emotion_after": "Aşk (Love)"
   }
   ```

3. Duygu Değişimi:
   ```json
   {
       "ad_id": "reklam123",
       "user_id": "kullanici456",
       "emotion_before": "Neşe (Joy)",
       "emotion_after": "Aşk (Love)"
   }
   ```

### e) API Endpoints

#### Reklam Gösterimi
```http
POST /api/track_ad_impression
Content-Type: application/json

{
    "ad_id": "reklam123",
    "user_id": "kullanici456",
    "emotion_before": "Neşe (Joy)",
    "emotion_after": "Neşe (Joy)"
}
```

#### Reklam Tıklaması
```http
POST /api/track_ad_click
Content-Type: application/json

{
    "ad_id": "reklam123",
    "user_id": "kullanici456",
    "emotion_before": "Neşe (Joy)",
    "emotion_after": "Aşk (Love)"
}
```

### f) Performans Ağırlıkları
```python
AD_PERFORMANCE_WEIGHTS = {
    'emotion': 0.3,        # Duygu uygunluğu
    'keyword': 0.3,        # Keyword uygunluğu
    'performance': 0.4,    # Performans metrikleri
    'ctr': 0.6,           # CTR ağırlığı
    'emotion_change': 0.4  # Duygu değişimi ağırlığı
}
```

### g) Önemli Notlar
- Metrikler Firebase'de `adMetrics` koleksiyonunda saklanır
- Son 30 günlük veriler kullanılır
- Yüksek performanslı reklamlar önceliklendirilir
- Sistem sürekli öğrenerek daha iyi reklam seçimleri yapar
- Ağırlıklar `config.py` dosyasından ayarlanabilir

## 13. Additional Features and Other Architectural Details

### User Behavior Analysis and Profile Factors
The system considers not only emotional interactions but also the user's interests, demographic information, behavioral patterns, and social connections. These factors affect the profile score in the recommendation algorithm and enable more personalized recommendations.

### Emotion Transition Matrix and Transition Analysis
Users' tendencies to transition from one emotion to another are modeled with the `EMOTION_TRANSITION_MATRIX` in the system. This matrix helps the recommendation algorithm predict possible mood changes and provide content diversity accordingly.

### Time-Based Weighting and Recency
The time factor is important in user interactions. Interactions from the last 24 hours, last 7 days, and older are considered with different weights. Thus, the system becomes more sensitive to the user's current mood.

### Content Quality and Engagement Metrics
Content to be recommended is scored not only by emotion but also by engagement rate, content freshness, author reputation, and content length. This prevents low-quality or old content from being recommended.

### Ad Optimization and Emotion-Based Targeting
Ads are placed according to the user's emotion pattern and interests. Each ad has target emotions and priority scores. In addition, the frequency and placement of ads are optimized.

### Confidence Score and Emotion Analysis Reliability
During emotion detection, a confidence score is assigned to the model's prediction. The system considers predictions with low confidence scores as less effective and takes this score into account in the recommendation algorithm.

### A/B Testing and Parameter Tracking
The system can test different algorithm and parameter variants live. For each recommendation request, which variant was used and the results are logged. Thus, the best performing structure can be automatically detected.

### Error Handling and Logging
All main functions have error catching and logging mechanisms. Thus, errors in the system can be easily detected and quickly intervened.

### Developer-Friendly Architecture
Thanks to the modular structure of the code, new algorithms or metrics can be easily added. Helper modules are designed independently so that they can be used in other projects as well.

---

For any contributions, suggestions, or bug reports, please open an issue or send a pull request.

## Railway Deployment

1. Install the Railway CLI
2. Set environment variables from the Railway dashboard:
   - `FIREBASE_CREDENTIALS`
   - `PORT` (Railway will set automatically)
3. Deploy:
```bash
railway up
```

## 14. Analysis and Optimization of Ads According to Emotional State

The system analyzes the emotional impact of ads on users. When a user interacts with an ad (e.g., click, view), the current emotional state and the emotion category targeted by the ad are recorded. This data is used to understand in which emotional states ads are more effective and to optimize ad placement.

- **Emotion-Performance Correlation:** The display and interaction rates of ads in different emotional states are analyzed.
- **Dynamic Ad Placement:** The user's current emotion pattern directly affects the frequency and type of ads.
- **Ad Interaction Score:** For each ad, separate interaction scores are kept for different emotions, and these scores are considered in the recommendation algorithm.

---

## 15. Scalability and Performance

The system is designed to be scalable against increasing numbers of users and content.
- **Batch Operations and Asynchronous Structure:** Asynchronous functions and batch data processing methods are used to prevent performance loss when working with large datasets.
- **Cache and Optimization:** Caching mechanisms are applied for frequently used data and calculations.

---

## License

Lori

## 16. Handling Dislike Interactions and Gradual Emotion Suppression

When a user gives a **dislike** interaction to a content with a specific emotion, the system dynamically reduces the weight of that emotion in the user's emotion pattern:

- **First Dislike:**
  - If the emotion's ratio in the pattern is above 50%, it is immediately reduced to 50%.
- **Subsequent Dislikes:**
  - If the emotion's ratio is already below 50%, each new dislike further reduces the ratio by 2.5% (i.e., `ratio = ratio * 0.975`).
- This ensures that repeated dislikes do not instantly zero out the emotion, but gradually decrease its influence in recommendations.
- The pattern is always normalized after these adjustments.

**Example:**
- Initial: `{"Joy": 0.7, "Love": 0.2, ...}`
- After first dislike on Joy: `{"Joy": 0.5, ...}`
- After another dislike on Joy: `{"Joy": 0.4875, ...}`
- And so on, with each dislike causing a softer reduction.

This mechanism prevents a single emotion from dominating the feed and allows the system to adapt to the user's negative feedback in a controlled, gradual way.

## 17. No Interaction (Stretching) Mechanism

If the user does **not interact** with any content in the feed (no like, dislike, comment, vs.), the system automatically activates a stretching mechanism to increase diversity:

- The dominant emotion's ratio in the pattern is pulled down to 50%.
- The remaining 50% is distributed equally among all other emotions.
- This prevents the system from getting stuck on a single emotion and ensures the user is exposed to a wider variety of emotional content.
- As soon as the user starts interacting again, the pattern returns to being dynamically updated based on their new interactions.

**Example:**
- Before: `{"Joy": 0.8, "Love": 0.1, "Sadness": 0.1, ...}`
- After no interaction: `{"Joy": 0.5, "Love": 0.1, "Sadness": 0.1, ...}` (the rest is distributed equally)

This mechanism helps keep the recommendations fresh and engaging, even for passive or indecisive users.

## 18. Feed Content Uniqueness and Repeat Handling

The recommendation algorithm prioritizes showing content that the user has **not seen before** in each feed request:

- **Primary Goal:** Always fill the feed with as many new (unseen) posts as possible.
- **If there are not enough new posts:** The remaining slots are filled with previously shown posts (repeats), but only as much as needed to reach the feed limit (e.g., 20 posts).
- **Diversity:** The algorithm still ensures at least one post from each emotion if available, and applies emotion pattern and diversity rules.
- **Result:** Users are exposed to fresh content as much as possible, and only see repeats when the content pool is insufficient.

**Example:**
- If there are 15 new posts and 5 repeats needed, the feed will contain 15 new + 5 repeated posts.
- If there are 20 or more new posts, the feed will contain only new posts.

This mechanism keeps the user experience fresh and prevents monotony, while guaranteeing the feed is always fully populated.

### Feed Reset When No Unseen Content Remains
If there are no unseen (previously unshown) posts left for the user, the system does **not** fall back to the cold start algorithm. Instead, the user's feed history (`userShownFeeds`) is automatically cleared, and the feed is regenerated from scratch using the user's current emotion pattern. This ensures that the user always receives recommendations aligned with their latest emotional tendencies, even after exhausting all available content.

## 19. Automatic Feed History Reset for Scalability

To keep the backend scalable and cost-effective for social media use cases, the system automatically resets the user's feed history if there is no feed request for a certain period (e.g., 10 minutes):

- **Mechanism:**
  - On each feed request, the user's last feed activity timestamp is updated.
  - If a new feed request arrives after more than 10 minutes of inactivity, all previous feed history (shown post IDs) is deleted.
  - The next feed is generated as if the user is starting fresh (no shown post IDs).
- **Benefits:**
  - Prevents the backend database from growing indefinitely with old feed history.
  - Reduces storage costs and keeps the system performant.
  - Ensures that users who return after a long break get a fresh feed experience.

**Example:**
- User requests a feed, sees 20 posts, and then leaves the app.
- If the user returns after 15 minutes, their previous feed history is cleared and a new feed is generated from scratch.

This mechanism is especially useful for high-traffic social media apps to keep server resources under control.

## 20. Feed History Size Limit

To further optimize backend performance and cost, the system enforces a maximum feed history limit per user (default: 100 feeds):

- **If a user's feed history exceeds 100 records, the oldest records are automatically deleted.**
- This ensures that even highly active users do not cause unbounded growth in the backend database.
- The limit can be adjusted as needed for different scalability requirements.

This approach keeps the system efficient and cost-effective for all user activity levels.

---

## 21. Story-Driven Feed Flow, Emotion Transitions & Striking Ad Placement (NEW)

### Personalized Story Flow & Emotion Journey
Our recommendation engine now crafts each user's feed as a unique emotional journey—a story tailored to their habits and emotional transitions. Instead of a random or static list, the feed is dynamically sequenced to reflect the user's most common and impactful emotion transitions, creating a narrative arc that feels natural and engaging.

- **Emotion Transition Analysis:**
  - The system analyzes the user's recent interactions to build a personalized emotion transition matrix (e.g., how often does the user move from "Sadness" to "Joy"?).
  - The feed is then ordered to reflect these transitions, maximizing emotional resonance and engagement.

- **Story-Like Sequencing:**
  - Content is arranged to follow the user's typical emotional journey, with smooth or dramatic transitions (e.g., "Sadness → Hope → Joy").
  - This approach increases session time and user satisfaction by making the feed feel like a meaningful, evolving experience rather than a random scroll.

### Striking Ad Placement at the Emotional Peak
Ads are no longer just inserted at fixed intervals—they are now strategically placed at the most emotionally striking moments in the user's story flow.

- **Peak Moment Detection:**
  - The system identifies the most impactful emotion transition in the feed (e.g., a rare or high-contrast shift such as "Fear → Love" or "Sadness → Joy").
  - This is determined by analyzing the user's emotion pattern and the feed's emotional arc, focusing on transitions with the greatest emotional delta or positive/negative polarity change.

- **Ad Insertion at the Climax:**
  - The top-performing ad is inserted immediately after this peak transition, ensuring maximum attention and emotional relevance.
  - This method leverages the user's heightened emotional state, dramatically increasing ad recall and click-through rates.

### Data-Driven Story Analytics for Marketing
- **Every user's story flow and emotion transitions are stored in Firebase for analytics.**
- Marketers and product teams can:
  - Track which emotional journeys are most common or most effective for engagement.
  - Analyze how ad performance correlates with specific emotional peaks or transitions.
  - Design campaigns that align with the user's natural emotional flow, not against it.

### Why This Matters
- **Unmatched Personalization:** Every feed is a unique, evolving story, not just a list.
- **Emotional Resonance:** Users feel understood and engaged, leading to longer sessions and higher satisfaction.
- **Ad Effectiveness:** Ads appear at the most memorable, emotionally charged moments, maximizing impact and ROI.
- **Actionable Insights:** The system provides rich analytics on user emotion journeys and ad performance, enabling smarter marketing and product decisions.

**This is not just recommendation—it's emotional storytelling at scale.**
