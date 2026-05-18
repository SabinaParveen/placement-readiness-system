from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from models import db, Student, QuizScore, Prediction, QuizQuestion, Admin
import csv
import io

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to restrict access to admins only."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not isinstance(current_user._get_current_object(), Admin):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── ADMIN DASHBOARD ───────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_students  = Student.query.count()
    total_predicted = Prediction.query.count()
    likely_placed   = Prediction.query.filter(
                        Prediction.placement_result == 'Likely Placed').count()

    students = db.session.query(Student, QuizScore, Prediction)\
        .outerjoin(QuizScore,  Student.id == QuizScore.student_id)\
        .outerjoin(Prediction, Student.id == Prediction.student_id)\
        .all()

    avg_readiness = db.session.query(
        db.func.avg(Prediction.readiness_percentage)).scalar() or 0

    return render_template('admin_dashboard.html',
        total_students=total_students,
        total_predicted=total_predicted,
        likely_placed=likely_placed,
        students=students,
        avg_readiness=round(avg_readiness, 2)
    )


# ── STUDENT DETAIL ────────────────────────────
@admin_bp.route('/student/<int:sid>')
@login_required
@admin_required
def student_detail(sid):
    student    = Student.query.get_or_404(sid)
    quiz_score = QuizScore.query.filter_by(student_id=sid).first()
    prediction = Prediction.query.filter_by(student_id=sid)\
                    .order_by(Prediction.predicted_at.desc()).first()
    return render_template('admin_student_detail.html',
        student=student,
        quiz_score=quiz_score,
        prediction=prediction
    )


# ── MANAGE QUESTIONS ──────────────────────────
@admin_bp.route('/questions')
@login_required
@admin_required
def questions():
    category = request.args.get('category', 'aptitude')
    qs = QuizQuestion.query.filter_by(category=category).all()
    return render_template('admin_questions.html', questions=qs, category=category)


@admin_bp.route('/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question():
    if request.method == 'POST':
        q = QuizQuestion(
            category      = request.form['category'],
            question_text = request.form['question_text'],
            option_a      = request.form['option_a'],
            option_b      = request.form['option_b'],
            option_c      = request.form['option_c'],
            option_d      = request.form['option_d'],
            correct_answer= request.form['correct_answer'].upper(),
            difficulty    = request.form.get('difficulty', 'medium')
        )
        db.session.add(q)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.questions', category=q.category))

    return render_template('admin_add_question.html')


@admin_bp.route('/questions/delete/<int:qid>', methods=['POST'])
@login_required
@admin_required
def delete_question(qid):
    q = QuizQuestion.query.get_or_404(qid)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin.questions'))


# ── DOWNLOAD REPORT ───────────────────────────
@admin_bp.route('/download-report')
@login_required
@admin_required
def download_report():
    students = db.session.query(Student, QuizScore, Prediction)\
        .outerjoin(QuizScore,  Student.id == QuizScore.student_id)\
        .outerjoin(Prediction, Student.id == Prediction.student_id)\
        .all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Name', 'Email', 'Department', 'CGPA', 'Attendance',
        'Internships', 'Projects', 'Certifications',
        'Aptitude', 'Technical', 'Communication',
        'Readiness %', 'Result'
    ])

    for s, q, p in students:
        writer.writerow([
            s.full_name, s.email, s.department or '-',
            s.cgpa or 0, s.attendance or 0,
            s.internships or 0, s.projects or 0, s.certifications or 0,
            q.aptitude_score if q else 0,
            q.technical_score if q else 0,
            q.communication_score if q else 0,
            p.readiness_percentage if p else 0,
            p.placement_result if p else 'Not Predicted'
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=placement_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response