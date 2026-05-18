from flask import Flask
from flask_login import LoginManager
from models import db, Student, Admin
from flask_wtf.csrf import CSRFProtect
from config import config
import os

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from routes.auth    import auth_bp
    from routes.student import student_bp
    from routes.quiz    import quiz_bp
    from routes.predict import predict_bp
    from routes.admin   import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Create all tables
    with app.app_context():
        db.create_all()
        _seed_questions(app)
        _seed_admin(app)

    return app


@login_manager.user_loader
def load_user(user_id):
    if str(user_id).startswith('admin-'):
        return Admin.query.get(int(user_id.split('-')[1]))
    return Student.query.get(int(user_id))


def _seed_admin(app):
    """Create default admin if not exists."""
    with app.app_context():
        if not Admin.query.filter_by(email='admin@placement.com').first():
            admin = Admin(username='admin', email='admin@placement.com')
            admin.set_password('Admin@1234')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: admin@placement.com / Admin@1234")


def _seed_questions(app):
    """Seed quiz questions if table is empty."""
    from models import QuizQuestion
    with app.app_context():
        if QuizQuestion.query.count() > 0:
            return

        questions = [
            # ── APTITUDE ──────────────────────────────────────
            QuizQuestion(category='aptitude', difficulty='easy',
                question_text='If a train travels 60 km in 1 hour, how far will it travel in 2.5 hours?',
                option_a='120 km', option_b='150 km', option_c='180 km', option_d='90 km',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='easy',
                question_text='What is 15% of 200?',
                option_a='25', option_b='30', option_c='35', option_d='20',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='medium',
                question_text='A shopkeeper sells an item for Rs.540 at a 20% profit. What is the cost price?',
                option_a='Rs.400', option_b='Rs.450', option_c='Rs.420', option_d='Rs.480',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='medium',
                question_text='Find the next number in the series: 2, 6, 12, 20, 30, ?',
                option_a='40', option_b='42', option_c='44', option_d='46',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='medium',
                question_text='Two pipes A and B can fill a tank in 10 and 15 hours. How long together?',
                option_a='5 hours', option_b='6 hours', option_c='7 hours', option_d='8 hours',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='hard',
                question_text='A can do a work in 15 days, B in 20 days. They work together for 4 days, then A leaves. How many more days for B to finish?',
                option_a='10 days', option_b='8 days', option_c='12 days', option_d='9 days',
                correct_answer='A'),
            QuizQuestion(category='aptitude', difficulty='medium',
                question_text='If ROAD is coded as URDG, how is SWAN coded?',
                option_a='VXDQ', option_b='VZDQ', option_c='VZCQ', option_d='UZDQ',
                correct_answer='B'),
            QuizQuestion(category='aptitude', difficulty='easy',
                question_text='Which number is the odd one out: 2, 3, 5, 7, 9, 11?',
                option_a='2', option_b='3', option_c='9', option_d='11',
                correct_answer='C'),
            QuizQuestion(category='aptitude', difficulty='medium',
                question_text='The ratio of ages of A and B is 3:5. After 10 years it will be 5:7. Find A\'s current age.',
                option_a='15', option_b='20', option_c='25', option_d='10',
                correct_answer='A'),
            QuizQuestion(category='aptitude', difficulty='hard',
                question_text='A sum of money doubles itself in 8 years at simple interest. Find the rate percent per annum.',
                option_a='10%', option_b='12%', option_c='12.5%', option_d='15%',
                correct_answer='C'),

            # ── TECHNICAL ─────────────────────────────────────
            QuizQuestion(category='technical', difficulty='easy',
                question_text='What is the output of: print(type(10/2)) in Python 3?',
                option_a="<class 'int'>", option_b="<class 'float'>", option_c="<class 'double'>", option_d='Error',
                correct_answer='B'),
            QuizQuestion(category='technical', difficulty='easy',
                question_text='Which SQL keyword is used to retrieve unique records?',
                option_a='UNIQUE', option_b='DISTINCT', option_c='DIFFERENT', option_d='SEPARATE',
                correct_answer='B'),
            QuizQuestion(category='technical', difficulty='medium',
                question_text='What does the "self" keyword represent in Python class methods?',
                option_a='A static variable', option_b='The class itself', option_c='The current instance', option_d='A global variable',
                correct_answer='C'),
            QuizQuestion(category='technical', difficulty='medium',
                question_text='What is the time complexity of binary search?',
                option_a='O(n)', option_b='O(n²)', option_c='O(log n)', option_d='O(1)',
                correct_answer='C'),
            QuizQuestion(category='technical', difficulty='easy',
                question_text='Which HTML tag is used to create a hyperlink?',
                option_a='<link>', option_b='<a>', option_c='<href>', option_d='<url>',
                correct_answer='B'),
            QuizQuestion(category='technical', difficulty='medium',
                question_text='What does SQL JOIN do?',
                option_a='Deletes duplicate rows', option_b='Combines rows from two or more tables', option_c='Sorts records', option_d='Creates a new table',
                correct_answer='B'),
            QuizQuestion(category='technical', difficulty='hard',
                question_text='What is a decorator in Python?',
                option_a='A design pattern', option_b='A function that takes another function and extends its behavior', option_c='A type of class', option_d='A module',
                correct_answer='B'),
            QuizQuestion(category='technical', difficulty='medium',
                question_text='What is the difference between a list and a tuple in Python?',
                option_a='Lists are faster', option_b='Tuples use less memory', option_c='Lists are mutable, tuples are immutable', option_d='There is no difference',
                correct_answer='C'),
            QuizQuestion(category='technical', difficulty='easy',
                question_text='Which CSS property is used to change the text color?',
                option_a='font-color', option_b='text-color', option_c='color', option_d='foreground',
                correct_answer='C'),
            QuizQuestion(category='technical', difficulty='hard',
                question_text='What is normalization in databases?',
                option_a='Encrypting data', option_b='Removing redundancy and ensuring data integrity', option_c='Speeding up queries', option_d='Indexing tables',
                correct_answer='B'),

            # ── COMMUNICATION ─────────────────────────────────
            QuizQuestion(category='communication', difficulty='easy',
                question_text='Choose the correct sentence:',
                option_a='She don\'t know the answer.', option_b='She doesn\'t knows the answer.', option_c='She doesn\'t know the answer.', option_d='She not know the answer.',
                correct_answer='C'),
            QuizQuestion(category='communication', difficulty='easy',
                question_text='Select the synonym of "Eloquent":',
                option_a='Silent', option_b='Fluent and persuasive', option_c='Confused', option_d='Aggressive',
                correct_answer='B'),
            QuizQuestion(category='communication', difficulty='medium',
                question_text='Identify the error: "The team are playing their best game."',
                option_a='team should be teams', option_b='are should be is', option_c='their should be its', option_d='No error',
                correct_answer='D'),
            QuizQuestion(category='communication', difficulty='medium',
                question_text='Fill in the blank: "He is good __ mathematics."',
                option_a='in', option_b='at', option_c='on', option_d='for',
                correct_answer='B'),
            QuizQuestion(category='communication', difficulty='easy',
                question_text='What is the antonym of "Verbose"?',
                option_a='Talkative', option_b='Concise', option_c='Loud', option_d='Fluent',
                correct_answer='B'),
            QuizQuestion(category='communication', difficulty='medium',
                question_text='Which is the most professional way to begin a formal email?',
                option_a='Hey there,', option_b='Yo,', option_c='Dear Sir/Madam,', option_d='Sup,',
                correct_answer='C'),
            QuizQuestion(category='communication', difficulty='hard',
                question_text='Identify the correct passive voice: "They completed the project."',
                option_a='The project is completed by them.', option_b='The project was completed by them.', option_c='The project has been complete by them.', option_d='The project completed by them.',
                correct_answer='B'),
            QuizQuestion(category='communication', difficulty='medium',
                question_text='Choose the correct form: "Neither of the students __ prepared."',
                option_a='were', option_b='are', option_c='was', option_d='have been',
                correct_answer='C'),
            QuizQuestion(category='communication', difficulty='easy',
                question_text='What does "CC" mean in email communication?',
                option_a='Carbon Copy', option_b='Copied Content', option_c='Confidential Copy', option_d='Confirmed Contact',
                correct_answer='A'),
            QuizQuestion(category='communication', difficulty='hard',
                question_text='Which sentence uses the subjunctive mood correctly?',
                option_a='If I was rich, I would travel.', option_b='If I were rich, I would travel.', option_c='If I am rich, I will travel.', option_d='If I be rich, I would travel.',
                correct_answer='B'),
        ]

        db.session.bulk_save_objects(questions)
        db.session.commit()
        print(f"✅ Seeded {len(questions)} quiz questions.")


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True)