from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, QuizQuestion, QuizScore
import random

quiz_bp = Blueprint('quiz', __name__)

QUIZ_QUESTION_COUNT = 10  # questions per quiz

def _get_or_create_score(student_id):
    score = QuizScore.query.filter_by(student_id=student_id).first()
    if not score:
        score = QuizScore(student_id=student_id)
        db.session.add(score)
        db.session.commit()
    return score


# ── QUIZ HOME ─────────────────────────────────
@quiz_bp.route('/quiz')
@login_required
def quiz_home():
    if not current_user.profile_complete:
        flash('Please complete your profile before taking quizzes.', 'warning')
        return redirect(url_for('student.profile'))

    score = _get_or_create_score(current_user.id)
    return render_template('quiz_home.html', score=score)


# ── APTITUDE QUIZ ─────────────────────────────
@quiz_bp.route('/quiz/aptitude', methods=['GET', 'POST'])
@login_required
def aptitude_quiz():
    score_record = _get_or_create_score(current_user.id)

    if request.method == 'POST':
        questions_data = request.form.get('questions_data')
        answers = {k: v for k, v in request.form.items() if k.startswith('q_')}

        correct = 0
        total   = 0
        results = []

        for key, selected in answers.items():
            q_id = int(key.split('_')[1])
            q    = QuizQuestion.query.get(q_id)
            if q:
                total += 1
                is_correct = selected.upper() == q.correct_answer.upper()
                if is_correct:
                    correct += 1
                results.append({
                    'question': q.question_text,
                    'selected': selected,
                    'correct':  q.correct_answer,
                    'is_correct': is_correct
                })

        score_val = round((correct / total) * 100, 2) if total > 0 else 0
        score_record.aptitude_score  = score_val
        score_record.aptitude_taken  = True
        db.session.commit()

        flash(f'Aptitude Quiz completed! Score: {score_val}/100', 'success')
        return render_template('quiz_result.html',
            quiz_type='Aptitude',
            score=score_val,
            correct=correct,
            total=total,
            results=results
        )

    questions = QuizQuestion.query.filter_by(category='aptitude').all()
    questions = random.sample(questions, min(QUIZ_QUESTION_COUNT, len(questions)))
    return render_template('quiz.html',
        quiz_type='Aptitude',
        questions=questions,
        timer=600  # 10 minutes
    )


# ── TECHNICAL QUIZ ────────────────────────────
@quiz_bp.route('/quiz/technical', methods=['GET', 'POST'])
@login_required
def technical_quiz():
    score_record = _get_or_create_score(current_user.id)

    if request.method == 'POST':
        answers = {k: v for k, v in request.form.items() if k.startswith('q_')}
        correct = 0
        total   = 0
        results = []

        for key, selected in answers.items():
            q_id = int(key.split('_')[1])
            q    = QuizQuestion.query.get(q_id)
            if q:
                total += 1
                is_correct = selected.upper() == q.correct_answer.upper()
                if is_correct:
                    correct += 1
                results.append({
                    'question': q.question_text,
                    'selected': selected,
                    'correct':  q.correct_answer,
                    'is_correct': is_correct
                })

        score_val = round((correct / total) * 100, 2) if total > 0 else 0
        score_record.technical_score  = score_val
        score_record.technical_taken  = True
        db.session.commit()

        flash(f'Technical Quiz completed! Score: {score_val}/100', 'success')
        return render_template('quiz_result.html',
            quiz_type='Technical',
            score=score_val,
            correct=correct,
            total=total,
            results=results
        )

    questions = QuizQuestion.query.filter_by(category='technical').all()
    questions = random.sample(questions, min(QUIZ_QUESTION_COUNT, len(questions)))
    return render_template('quiz.html',
        quiz_type='Technical',
        questions=questions,
        timer=600
    )


# ── COMMUNICATION QUIZ ────────────────────────
@quiz_bp.route('/quiz/communication', methods=['GET', 'POST'])
@login_required
def communication_quiz():
    score_record = _get_or_create_score(current_user.id)

    if request.method == 'POST':
        answers = {k: v for k, v in request.form.items() if k.startswith('q_')}
        correct = 0
        total   = 0
        results = []

        for key, selected in answers.items():
            q_id = int(key.split('_')[1])
            q    = QuizQuestion.query.get(q_id)
            if q:
                total += 1
                is_correct = selected.upper() == q.correct_answer.upper()
                if is_correct:
                    correct += 1
                results.append({
                    'question': q.question_text,
                    'selected': selected,
                    'correct':  q.correct_answer,
                    'is_correct': is_correct
                })

        score_val = round((correct / total) * 100, 2) if total > 0 else 0
        score_record.communication_score  = score_val
        score_record.communication_taken  = True
        db.session.commit()

        flash(f'Communication Quiz completed! Score: {score_val}/100', 'success')
        return render_template('quiz_result.html',
            quiz_type='Communication',
            score=score_val,
            correct=correct,
            total=total,
            results=results
        )

    questions = QuizQuestion.query.filter_by(category='communication').all()
    questions = random.sample(questions, min(QUIZ_QUESTION_COUNT, len(questions)))
    return render_template('quiz.html',
        quiz_type='Communication',
        questions=questions,
        timer=480
    )