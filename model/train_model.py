"""
Placement Readiness ML Model Training Pipeline
Run this script once before launching the Flask app:
    python model/train_model.py
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, roc_auc_score)
from sklearn.pipeline import Pipeline
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# ── CONFIG ────────────────────────────────────
DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'students.csv')
MODEL_OUT    = os.path.join(os.path.dirname(__file__), 'model.pkl')
RANDOM_STATE = 42

FEATURES = [
    'cgpa', 'attendance', 'aptitude_score', 'technical_score',
    'communication_score', 'internships', 'projects', 'certifications'
]
TARGET = 'placed'


# ── GENERATE SYNTHETIC DATASET (if CSV not found) ─
def generate_synthetic_data(n=1000):
    print("⚠️  No dataset found. Generating synthetic data...")
    np.random.seed(RANDOM_STATE)

    cgpa          = np.round(np.random.uniform(5.0, 10.0, n), 2)
    attendance    = np.round(np.random.uniform(50, 100, n), 2)
    aptitude      = np.round(np.random.uniform(20, 100, n), 2)
    technical     = np.round(np.random.uniform(20, 100, n), 2)
    communication = np.round(np.random.uniform(20, 100, n), 2)
    internships   = np.random.randint(0, 5, n)
    projects      = np.random.randint(0, 8, n)
    certifications= np.random.randint(0, 7, n)

    # Placement logic (weighted formula with noise)
    score = (
        (cgpa / 10)           * 0.25 +
        (attendance / 100)    * 0.10 +
        (aptitude / 100)      * 0.20 +
        (technical / 100)     * 0.20 +
        (communication / 100) * 0.10 +
        (np.minimum(internships, 3) / 3) * 0.07 +
        (np.minimum(projects, 5) / 5)    * 0.05 +
        (np.minimum(certifications, 5) / 5) * 0.03
    )

    noise = np.random.normal(0, 0.05, n)
    placed = ((score + noise) >= 0.60).astype(int)

    df = pd.DataFrame({
        'cgpa': cgpa, 'attendance': attendance,
        'aptitude_score': aptitude, 'technical_score': technical,
        'communication_score': communication,
        'internships': internships, 'projects': projects,
        'certifications': certifications, 'placed': placed
    })

    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"✅ Synthetic dataset saved: {DATASET_PATH}")
    print(f"   Placement rate: {placed.mean()*100:.1f}%")
    return df


# ── LOAD DATA ─────────────────────────────────
def load_data():
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH)
        print(f"✅ Dataset loaded: {len(df)} records")
        # Map string targets if present
        if df[TARGET].dtype == object:
            df[TARGET] = df[TARGET].map({'Placed': 1, 'Not Placed': 0,
                                          'Yes': 1, 'No': 0}).fillna(0).astype(int)
    else:
        df = generate_synthetic_data()

    return df


# ── PREPROCESS ────────────────────────────────
def preprocess(df):
    df = df[FEATURES + [TARGET]].dropna()

    # Clip to valid ranges
    df['cgpa']          = df['cgpa'].clip(0, 10)
    df['attendance']    = df['attendance'].clip(0, 100)
    df['aptitude_score']      = df['aptitude_score'].clip(0, 100)
    df['technical_score']     = df['technical_score'].clip(0, 100)
    df['communication_score'] = df['communication_score'].clip(0, 100)

    X = df[FEATURES]
    y = df[TARGET]
    return X, y


# ── TRAIN & EVALUATE ──────────────────────────
def train_and_evaluate(X_train, X_test, y_train, y_test):
    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=200, max_depth=10,
            min_samples_split=5, random_state=RANDOM_STATE, n_jobs=-1),
        'Gradient Boosting': GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.1,
            max_depth=4, random_state=RANDOM_STATE),
        'Logistic Regression': Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(random_state=RANDOM_STATE, max_iter=500))
        ]),
    }

    best_model  = None
    best_auc    = 0
    best_name   = ''

    print("\n📊 Model Comparison:")
    print("=" * 55)

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        cv  = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc').mean()

        print(f"\n{name}:")
        print(f"  Accuracy : {acc*100:.2f}%")
        print(f"  ROC-AUC  : {auc:.4f}")
        print(f"  CV AUC   : {cv:.4f}")

        if auc > best_auc:
            best_auc   = auc
            best_model = model
            best_name  = name

    print("\n" + "=" * 55)
    print(f"🏆 Best Model: {best_name} (AUC: {best_auc:.4f})")

    # Detailed report for best model
    y_pred_best = best_model.predict(X_test)
    print(f"\n📋 Classification Report ({best_name}):")
    print(classification_report(y_test, y_pred_best,
                                  target_names=['Not Placed', 'Placed']))

    # Feature importance (if applicable)
    if hasattr(best_model, 'feature_importances_'):
        fi = pd.Series(best_model.feature_importances_, index=FEATURES).sort_values(ascending=False)
        print("\n📌 Feature Importance:")
        for feat, imp in fi.items():
            bar = '█' * int(imp * 40)
            print(f"  {feat:<22} {imp:.4f}  {bar}")

    return best_model, best_name


# ── MAIN ──────────────────────────────────────
def main():
    print("🚀 Starting ML Training Pipeline...")
    print("=" * 55)

    df          = load_data()
    X, y        = preprocess(df)

    print(f"\n📦 Dataset: {len(X)} samples | "
          f"Features: {len(FEATURES)} | "
          f"Placement rate: {y.mean()*100:.1f}%")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    best_model, best_name = train_and_evaluate(
        X_train, X_test, y_train, y_test)

    # Save model
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(best_model, MODEL_OUT)
    print(f"\n✅ Model saved to: {MODEL_OUT}")
    print("\n🎉 Training complete! You can now run the Flask app.")


if __name__ == '__main__':
    main()