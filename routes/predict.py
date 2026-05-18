from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, QuizScore, Prediction
import joblib
import numpy as np
import json
import os

predict_bp = Blueprint('predict', __name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'model', 'model.pkl')


def _load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _generate_recommendations(data: dict, readiness: float) -> list:
    """Rule-based + threshold recommendations."""
    recs = []

    if data['cgpa'] < 7.0:
        recs.append({'icon': '📚', 'title': 'Improve your CGPA',
            'desc': 'Focus on core subjects. Target CGPA above 7.5 for better placement chances.'})
    if data['attendance'] < 75:
        recs.append({'icon': '🎯', 'title': 'Increase Attendance',
            'desc': 'Maintain at least 75% attendance. Employers value discipline and consistency.'})
    if data['aptitude'] < 60:
        recs.append({'icon': '🧮', 'title': 'Practice Aptitude Questions',
            'desc': 'Solve 20+ aptitude questions daily. Use platforms like IndiaBix or PrepInsta.'})
    if data['technical'] < 60:
        recs.append({'icon': '💻', 'title': 'Strengthen Technical Skills',
            'desc': 'Practice Python, SQL, and DSA. Try LeetCode easy problems and HackerRank.'})
    if data['communication'] < 60:
        recs.append({'icon': '🗣️', 'title': 'Improve Communication Skills',
            'desc': 'Practice spoken English daily. Join group discussions or use apps like ELSA.'})
    if data['internships'] == 0:
        recs.append({'icon': '🏢', 'title': 'Get Internship Experience',
            'desc': 'Apply for internships on LinkedIn, Internshala, or your college portal.'})
    if data['projects'] < 2:
        recs.append({'icon': '🛠️', 'title': 'Build More Projects',
            'desc': 'Build 2-3 projects using Python/Web tech. Host them on GitHub.'})
    if data['certifications'] < 2:
        recs.append({'icon': '🏅', 'title': 'Earn Certifications',
            'desc': 'Get certified on Coursera, NPTEL, or Google. Aim for at least 2 certifications.'})

    if not recs:
        recs.append({'icon': '🌟', 'title': 'Keep it up!',
            'desc': 'You are well prepared. Focus on mock interviews and company-specific prep.'})

    return recs


# ── PREDICT ───────────────────────────────────
@predict_bp.route('/predict')
@login_required
def predict():
    if not current_user.profile_complete:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('student.profile'))

    quiz_score = QuizScore.query.filter_by(student_id=current_user.id).first()
    if not quiz_score or not (quiz_score.aptitude_taken and
                               quiz_score.technical_taken and
                               quiz_score.communication_taken):
        flash('Please complete all three quizzes before getting a prediction.', 'warning')
        return redirect(url_for('quiz.quiz_home'))

    # Build feature vector
    data = {
        'cgpa':           current_user.cgpa or 0,
        'attendance':     current_user.attendance or 0,
        'aptitude':       quiz_score.aptitude_score,
        'technical':      quiz_score.technical_score,
        'communication':  quiz_score.communication_score,
        'internships':    current_user.internships or 0,
        'projects':       current_user.projects or 0,
        'certifications': current_user.certifications or 0,
    }

    features = np.array([[
        data['cgpa'],
        data['attendance'],
        data['aptitude'],
        data['technical'],
        data['communication'],
        data['internships'],
        data['projects'],
        data['certifications'],
    ]])

    model = _load_model()

    if model:
        try:
            prob          = model.predict_proba(features)[0]
            placed_prob   = float(round(float(prob[1]) * 100, 2))
            result_label  = 'Likely Placed' if placed_prob >= 60 else 'Needs Improvement'
            confidence    = float(round(float(max(prob)) * 100, 2))
        except Exception as e:
            placed_prob, result_label, confidence = _fallback_score(data)
    else:
        placed_prob, result_label, confidence = _fallback_score(data)

    recommendations = _generate_recommendations(data, placed_prob)

    # Save prediction
    pred = Prediction(
        student_id           = current_user.id,
        readiness_percentage = placed_prob,
        placement_result     = result_label,
        confidence_score     = confidence,
        recommendations      = json.dumps(recommendations)
    )
    db.session.add(pred)
    db.session.commit()

    return render_template('result.html',
        prediction=pred,
        recommendations=recommendations,
        data=data
    )


def _fallback_score(data):
    """Weighted heuristic score if model.pkl not found."""
    score = (
        data['cgpa']          / 10.0  * 25 +
        data['attendance']    / 100.0 * 15 +
        data['aptitude']      / 100.0 * 20 +
        data['technical']     / 100.0 * 20 +
        data['communication'] / 100.0 * 10 +
        min(data['internships'], 3)    / 3.0 * 5 +
        min(data['projects'], 5)       / 5.0 * 3 +
        min(data['certifications'], 5) / 5.0 * 2
    )
    label = 'Likely Placed' if score >= 60 else 'Needs Improvement'
    return round(score, 2), label, round(score, 2)