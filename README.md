# Emotion-Based Recommendation System

This project is an API service that provides content and ad recommendations based on users' emotional interactions.

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
