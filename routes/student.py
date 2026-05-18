from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Student, Admin, QuizScore, Prediction
import json

student_bp = Blueprint('student', __name__)

# ── DASHBOARD ─────────────────────────────────
@student_bp.route('/dashboard')
@login_required
def dashboard():
    # Redirect admin to admin dashboard
    if isinstance(current_user._get_current_object(), Admin):
        return redirect(url_for('admin.dashboard'))
    quiz_score = QuizScore.query.filter_by(student_id=current_user.id).first()
    prediction = Prediction.query.filter_by(student_id=current_user.id)\
                    .order_by(Prediction.predicted_at.desc()).first()

    recommendations = []
    if prediction and prediction.recommendations:
        try:
            recommendations = json.loads(prediction.recommendations)
        except Exception:
            recommendations = []

    chart_data = None
    if quiz_score:
        chart_data = {
            'aptitude':      quiz_score.aptitude_score,
            'technical':     quiz_score.technical_score,
            'communication': quiz_score.communication_score,
        }

    return render_template('dashboard.html',
        student=current_user,
        quiz_score=quiz_score,
        prediction=prediction,
        recommendations=recommendations,
        chart_data=json.dumps(chart_data) if chart_data else None
    )


# ── PROFILE SETUP ─────────────────────────────
@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            current_user.department     = request.form.get('department', '').strip()
            current_user.cgpa           = float(request.form.get('cgpa', 0))
            current_user.attendance     = float(request.form.get('attendance', 0))
            current_user.internships    = int(request.form.get('internships', 0))
            current_user.projects       = int(request.form.get('projects', 0))
            current_user.certifications = int(request.form.get('certifications', 0))

            # Validate ranges
            if not (0.0 <= current_user.cgpa <= 10.0):
                flash('CGPA must be between 0 and 10.', 'danger')
                return render_template('profile.html', student=current_user)

            if not (0.0 <= current_user.attendance <= 100.0):
                flash('Attendance must be between 0 and 100.', 'danger')
                return render_template('profile.html', student=current_user)

            current_user.profile_complete = True
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student.dashboard'))

        except ValueError:
            flash('Please enter valid numeric values.', 'danger')

    return render_template('profile.html', student=current_user)


# ── API: Student stats for charts ─────────────
@student_bp.route('/api/student-stats')
@login_required
def student_stats():
    quiz_score = QuizScore.query.filter_by(student_id=current_user.id).first()
    prediction = Prediction.query.filter_by(student_id=current_user.id)\
                    .order_by(Prediction.predicted_at.desc()).first()

    return jsonify({
        'cgpa':           current_user.cgpa or 0,
        'attendance':     current_user.attendance or 0,
        'internships':    current_user.internships or 0,
        'projects':       current_user.projects or 0,
        'certifications': current_user.certifications or 0,
        'aptitude':       quiz_score.aptitude_score if quiz_score else 0,
        'technical':      quiz_score.technical_score if quiz_score else 0,
        'communication':  quiz_score.communication_score if quiz_score else 0,
        'readiness':      prediction.readiness_percentage if prediction else 0,
    })