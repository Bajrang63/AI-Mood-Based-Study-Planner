"""
ml_model.py — AI/ML Core Module
================================
This file contains the Decision Tree model for predicting study intensity.

HOW IT WORKS (for viva explanation):
--------------------------------------
1. We create synthetic training data based on expert knowledge about studying.
2. A Decision Tree classifier learns patterns from this data.
3. When a user submits mood, hours, focus → the model predicts intensity.
4. The model is saved to disk so it doesn't retrain every request.

INPUTS:
  - Mood      : Happy=0, Sad=1, Stressed=2, Energetic=3, Tired=4
  - Hours     : 1–8 (available study hours)
  - Focus     : 1–10 (self-rated focus level)

OUTPUT:
  - Intensity : Light / Moderate / Intense
"""

import os
import pickle
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Path to save/load the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'study_model.pkl')

# -------------------------------------------------------
# Mood encoding: text → number (for ML model)
# -------------------------------------------------------
MOOD_ENCODING = {
    'Happy': 0,
    'Sad': 1,
    'Stressed': 2,
    'Energetic': 3,
    'Tired': 4,
}

# -------------------------------------------------------
# Intensity labels: number → text
# -------------------------------------------------------
INTENSITY_LABELS = {
    0: 'Light',
    1: 'Moderate',
    2: 'Intense',
}


def generate_training_data():
    """
    Generate synthetic training data based on expert rules.
    
    LOGIC BEHIND DATA GENERATION:
    - High focus + many hours + energetic mood → Intense study
    - Low focus + few hours + tired/sad mood  → Light study
    - Everything in between                   → Moderate study
    
    This simulates what a study counselor would recommend.
    """
    np.random.seed(42)  # For reproducibility
    
    X = []  # Features: [mood_encoded, hours, focus]
    y = []  # Labels:   0=Light, 1=Moderate, 2=Intense
    
    # Generate 500 training samples
    for _ in range(500):
        mood_code = np.random.randint(0, 5)   # 0–4
        hours = np.random.randint(1, 9)        # 1–8
        focus = np.random.randint(1, 11)       # 1–10
        
        # Rule-based labeling (expert system converted to training data)
        score = 0
        
        # Mood contribution
        if mood_code == 3:   # Energetic
            score += 3
        elif mood_code == 0:  # Happy
            score += 2
        elif mood_code == 2:  # Stressed
            score += 1
        elif mood_code == 1:  # Sad
            score += 0
        elif mood_code == 4:  # Tired
            score -= 1
        
        # Hours contribution
        if hours >= 6:
            score += 3
        elif hours >= 4:
            score += 2
        elif hours >= 2:
            score += 1
        
        # Focus contribution
        if focus >= 8:
            score += 3
        elif focus >= 5:
            score += 2
        elif focus >= 3:
            score += 1
        
        # Add small random noise to make data more realistic
        score += np.random.randint(-1, 2)
        
        # Convert score to intensity label
        if score <= 3:
            intensity = 0   # Light
        elif score <= 6:
            intensity = 1   # Moderate
        else:
            intensity = 2   # Intense
        
        X.append([mood_code, hours, focus])
        y.append(intensity)
    
    return np.array(X), np.array(y)


def train_model():
    """
    Train the Decision Tree model and save it to disk.
    
    Returns:
        model    : Trained DecisionTreeClassifier
        accuracy : Test accuracy as percentage string
    """
    print("🔄 Training Decision Tree Model...")
    
    # Step 1: Generate training data
    X, y = generate_training_data()
    
    # Step 2: Split into train/test sets (80/20 split)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Step 3: Create and train the Decision Tree
    # max_depth=5 prevents overfitting
    model = DecisionTreeClassifier(
        max_depth=5,
        random_state=42,
        criterion='gini'  # Gini impurity for splitting
    )
    model.fit(X_train, y_train)
    
    # Step 4: Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Step 5: Save the trained model to disk
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"✅ Model trained! Accuracy: {accuracy * 100:.2f}%")
    print(f"💾 Model saved to: {MODEL_PATH}")
    
    return model, f"{accuracy * 100:.2f}%"


def load_model():
    """
    Load the pre-trained model from disk.
    If model doesn't exist, train a new one.
    
    Returns:
        Trained DecisionTreeClassifier
    """
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        return model
    else:
        # Train and return a new model
        model, _ = train_model()
        return model


def predict_intensity(mood: str, hours: int, focus: int) -> dict:
    """
    Main prediction function — called from views.py.
    
    Args:
        mood  : String like 'Happy', 'Sad', 'Stressed', 'Energetic', 'Tired'
        hours : Integer 1–8 (available study hours)
        focus : Integer 1–10 (focus level)
    
    Returns:
        dict with keys:
          - intensity      : 'Light' / 'Moderate' / 'Intense'
          - confidence     : prediction confidence %
          - study_plan     : list of time blocks
          - tips           : list of study tips
    
    EXAMPLE:
        result = predict_intensity('Happy', 4, 7)
        # → {'intensity': 'Moderate', 'confidence': '85.00%', ...}
    """
    # Load the trained model
    model = load_model()
    
    # Encode the mood as a number
    mood_code = MOOD_ENCODING.get(mood, 0)
    
    # Create feature vector
    features = np.array([[mood_code, hours, focus]])
    
    # Get prediction
    prediction = model.predict(features)[0]
    
    # Get confidence (probability of the predicted class)
    probabilities = model.predict_proba(features)[0]
    confidence = max(probabilities) * 100
    
    # Get intensity label
    intensity = INTENSITY_LABELS[prediction]
    
    # Generate study plan based on intensity and hours
    study_plan = generate_study_plan(intensity, hours, mood)
    
    # Get study tips based on mood and intensity
    tips = get_study_tips(mood, intensity)
    
    return {
        'intensity': intensity,
        'confidence': f"{confidence:.1f}%",
        'study_plan': study_plan,
        'tips': tips,
        'mood': mood,
        'hours': hours,
        'focus': focus,
    }


def generate_study_plan(intensity: str, hours: int, mood: str) -> list:
    """
    Generate a time-blocked study plan based on intensity.
    
    Different intensities get different Pomodoro-style schedules:
    - Light   : 25 min study + 10 min break  (relaxed)
    - Moderate: 45 min study + 10 min break  (standard)
    - Intense : 60 min study +  5 min break  (deep work)
    """
    plan = []
    current_minute = 0
    session_num = 1
    total_minutes = hours * 60
    
    if intensity == 'Light':
        study_block = 25
        break_block = 10
        session_name = "Light Study Session"
    elif intensity == 'Moderate':
        study_block = 45
        break_block = 10
        session_name = "Focused Study Session"
    else:  # Intense
        study_block = 60
        break_block = 5
        session_name = "Deep Work Session"
    
    while current_minute < total_minutes:
        remaining = total_minutes - current_minute
        
        # Study block
        actual_study = min(study_block, remaining)
        start_h = current_minute // 60
        start_m = current_minute % 60
        end_minute = current_minute + actual_study
        end_h = end_minute // 60
        end_m = end_minute % 60
        
        plan.append({
            'type': 'study',
            'session': f"Session {session_num}: {session_name}",
            'time': f"{start_h:02d}:{start_m:02d} – {end_h:02d}:{end_m:02d}",
            'duration': f"{actual_study} min",
            'icon': '📚'
        })
        current_minute += actual_study
        
        if current_minute >= total_minutes:
            break
        
        # Break block
        remaining = total_minutes - current_minute
        actual_break = min(break_block, remaining)
        start_h = current_minute // 60
        start_m = current_minute % 60
        end_minute = current_minute + actual_break
        end_h = end_minute // 60
        end_m = end_minute % 60
        
        plan.append({
            'type': 'break',
            'session': "Break Time",
            'time': f"{start_h:02d}:{start_m:02d} – {end_h:02d}:{end_m:02d}",
            'duration': f"{actual_break} min",
            'icon': '☕'
        })
        current_minute += actual_break
        session_num += 1
    
    return plan


def get_study_tips(mood: str, intensity: str) -> list:
    """
    Return personalized study tips based on mood and intensity.
    """
    tips_map = {
        'Happy': [
            "🌟 Great mood! Use this energy to tackle your hardest topics first.",
            "📝 Try teaching concepts out loud — you'll retain them better.",
            "🎯 Set ambitious goals today; your positive mindset will carry you through.",
        ],
        'Sad': [
            "💙 It's okay to feel down. Start with easy, familiar topics to build momentum.",
            "🎵 Listen to calming instrumental music while you study.",
            "✅ Celebrate small wins — every page read is progress.",
        ],
        'Stressed': [
            "🧘 Take 5 deep breaths before starting. Stress can actually sharpen focus!",
            "📋 Make a prioritized list and tackle one task at a time.",
            "⏰ Use the Pomodoro technique — short focused bursts reduce overwhelm.",
        ],
        'Energetic': [
            "🚀 Channel this energy into your most challenging subjects!",
            "🏃 Consider standing or pacing while reviewing notes.",
            "💪 This is a great time for practice problems and active recall.",
        ],
        'Tired': [
            "😴 Take a 10-minute power nap before starting if possible.",
            "☕ Hydrate well — dehydration worsens fatigue.",
            "📖 Review previously learned material rather than tackling new content.",
        ],
    }
    
    intensity_tips = {
        'Light': "🌿 Today, focus on reviewing notes rather than learning new concepts.",
        'Moderate': "⚡ Balance new learning with practice — aim for one new concept per session.",
        'Intense': "🔥 You're in peak condition! Tackle your most complex and important topics.",
    }
    
    tips = tips_map.get(mood, [])
    tips.append(intensity_tips.get(intensity, ""))
    return tips


# -------------------------------------------------------
# AUTO-TRAIN: Train model when this file is first imported
# -------------------------------------------------------
if not os.path.exists(MODEL_PATH):
    train_model()
