from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ──────────────────────────────────────────────
# STUDENT MODEL
# ──────────────────────────────────────────────
class Student(UserMixin, db.Model):
    __tablename__ = 'students'

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    department    = db.Column(db.String(100))
    cgpa          = db.Column(db.Float)
    attendance    = db.Column(db.Float)
    internships   = db.Column(db.Integer, default=0)
    projects      = db.Column(db.Integer, default=0)
    certifications= db.Column(db.Integer, default=0)
    profile_complete = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    quiz_scores   = db.relationship('QuizScore', backref='student', lazy=True)
    predictions   = db.relationship('Prediction', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Student {self.email}>'


# ──────────────────────────────────────────────
# ADMIN MODEL
# ──────────────────────────────────────────────
class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Required by Flask-Login for mixed user types
    def get_id(self):
        return f"admin-{self.id}"


# ──────────────────────────────────────────────
# QUIZ SCORE MODEL
# ──────────────────────────────────────────────
class QuizScore(db.Model):
    __tablename__ = 'quiz_scores'

    id               = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    aptitude_score   = db.Column(db.Float, default=0)
    technical_score  = db.Column(db.Float, default=0)
    communication_score = db.Column(db.Float, default=0)
    aptitude_taken   = db.Column(db.Boolean, default=False)
    technical_taken  = db.Column(db.Boolean, default=False)
    communication_taken = db.Column(db.Boolean, default=False)
    taken_at         = db.Column(db.DateTime, default=datetime.utcnow)

    def total_score(self):
        return round((self.aptitude_score + self.technical_score + self.communication_score) / 3, 2)


# ──────────────────────────────────────────────
# PREDICTION MODEL
# ──────────────────────────────────────────────
class Prediction(db.Model):
    __tablename__ = 'predictions'

    id                   = db.Column(db.Integer, primary_key=True)
    student_id           = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    readiness_percentage = db.Column(db.Float)
    placement_result     = db.Column(db.String(20))   # "Likely" / "Unlikely"
    confidence_score     = db.Column(db.Float)
    recommendations      = db.Column(db.Text)          # JSON string
    predicted_at         = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────
# QUIZ QUESTION MODEL
# ──────────────────────────────────────────────
class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'

    id            = db.Column(db.Integer, primary_key=True)
    category      = db.Column(db.String(50), nullable=False)  # aptitude / technical / communication
    question_text = db.Column(db.Text, nullable=False)
    option_a      = db.Column(db.String(200), nullable=False)
    option_b      = db.Column(db.String(200), nullable=False)
    option_c      = db.Column(db.String(200), nullable=False)
    option_d      = db.Column(db.String(200), nullable=False)
    correct_answer= db.Column(db.String(1), nullable=False)    # 'A', 'B', 'C', or 'D'
    difficulty    = db.Column(db.String(10), default='medium') # easy / medium / hard