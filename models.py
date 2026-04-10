# models.py — Database Models for eLearning Platform
# Uses Flask-SQLAlchemy ORM with SQLite

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────────────────────────────────
# USER MODEL  (Students + Admins share this table, role distinguishes them)
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(10),  default='student')   # 'student' or 'admin'
    full_name  = db.Column(db.String(120), default='')
    bio        = db.Column(db.Text,        default='')
    avatar     = db.Column(db.String(200), default='default.png')
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)
    is_active  = db.Column(db.Boolean,     default=True)

    # Relationships
    enrollments  = db.relationship('Enrollment',  backref='student', lazy=True, cascade='all, delete')
    quiz_results = db.relationship('QuizResult',  backref='student', lazy=True, cascade='all, delete')
    ratings      = db.relationship('CourseRating',backref='student', lazy=True, cascade='all, delete')

    def set_password(self, raw_password):
        """Hash and store the password."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verify a password against its hash."""
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


# ─────────────────────────────────────────────
# COURSE MODEL
# ─────────────────────────────────────────────
class Course(db.Model):
    __tablename__ = 'courses'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        nullable=False)
    instructor  = db.Column(db.String(120), nullable=False)
    thumbnail   = db.Column(db.String(200), default='default_course.png')
    category    = db.Column(db.String(80),  default='General')
    level       = db.Column(db.String(30),  default='Beginner')  # Beginner/Intermediate/Advanced
    is_active   = db.Column(db.Boolean,     default=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships
    lessons     = db.relationship('Lesson',      backref='course', lazy=True, cascade='all, delete', order_by='Lesson.order')
    materials   = db.relationship('Material',    backref='course', lazy=True, cascade='all, delete')
    enrollments = db.relationship('Enrollment',  backref='course', lazy=True, cascade='all, delete')
    quizzes     = db.relationship('Quiz',        backref='course', lazy=True, cascade='all, delete')
    ratings     = db.relationship('CourseRating',backref='course', lazy=True, cascade='all, delete')

    def avg_rating(self):
        """Calculate average rating."""
        if not self.ratings:
            return 0
        return round(sum(r.rating for r in self.ratings) / len(self.ratings), 1)

    def total_students(self):
        return len(self.enrollments)

    def __repr__(self):
        return f'<Course {self.title}>'


# ─────────────────────────────────────────────
# LESSON MODEL
# ─────────────────────────────────────────────
class Lesson(db.Model):
    __tablename__ = 'lessons'

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        default='')
    video_url   = db.Column(db.String(300), default='')   # YouTube embed OR uploaded file path
    duration    = db.Column(db.String(20),  default='')   # e.g. "10:30"
    order       = db.Column(db.Integer,     default=1)
    is_preview  = db.Column(db.Boolean,     default=False)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships
    materials   = db.relationship('Material', backref='lesson', lazy=True, cascade='all, delete')
    progress    = db.relationship('LessonProgress', backref='lesson', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<Lesson {self.title}>'


# ─────────────────────────────────────────────
# MATERIAL (Downloadable Files)
# ─────────────────────────────────────────────
class Material(db.Model):
    __tablename__ = 'materials'

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'),  nullable=False)
    lesson_id   = db.Column(db.Integer, db.ForeignKey('lessons.id'),  nullable=True)
    title       = db.Column(db.String(200), nullable=False)
    file_path   = db.Column(db.String(300), nullable=False)
    file_type   = db.Column(db.String(20),  default='pdf')   # pdf, doc, zip, etc.
    file_size   = db.Column(db.String(20),  default='')
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<Material {self.title}>'


# ─────────────────────────────────────────────
# ENROLLMENT MODEL
# ─────────────────────────────────────────────
class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    course_id     = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed     = db.Column(db.Boolean,  default=False)
    completed_at  = db.Column(db.DateTime, nullable=True)
    certificate   = db.Column(db.String(200), default='')   # certificate file path

    def progress_percent(self):
        """Calculate % of lessons completed."""
        total_lessons = len(self.course.lessons)
        if total_lessons == 0:
            return 0
        completed = LessonProgress.query.filter_by(
            user_id=self.user_id,
            course_id=self.course_id,
            completed=True
        ).count()
        return int((completed / total_lessons) * 100)

    def __repr__(self):
        return f'<Enrollment user={self.user_id} course={self.course_id}>'


# ─────────────────────────────────────────────
# LESSON PROGRESS TRACKING
# ─────────────────────────────────────────────
class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    lesson_id   = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completed   = db.Column(db.Boolean,  default=False)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Progress user={self.user_id} lesson={self.lesson_id}>'


# ─────────────────────────────────────────────
# QUIZ MODEL
# ─────────────────────────────────────────────
class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id          = db.Column(db.Integer, primary_key=True)
    course_id   = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text,        default='')
    pass_score  = db.Column(db.Integer,     default=70)   # pass if >= 70%
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships
    questions   = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete')
    results     = db.relationship('QuizResult',   backref='quiz', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<Quiz {self.title}>'


# ─────────────────────────────────────────────
# QUIZ QUESTION MODEL
# ─────────────────────────────────────────────
class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'

    id             = db.Column(db.Integer, primary_key=True)
    quiz_id        = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question       = db.Column(db.Text,        nullable=False)
    option_a       = db.Column(db.String(300), nullable=False)
    option_b       = db.Column(db.String(300), nullable=False)
    option_c       = db.Column(db.String(300), nullable=False)
    option_d       = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.String(1),   nullable=False)   # 'a', 'b', 'c', or 'd'
    order          = db.Column(db.Integer,     default=1)

    def __repr__(self):
        return f'<Question {self.question[:40]}>'


# ─────────────────────────────────────────────
# QUIZ RESULT MODEL
# ─────────────────────────────────────────────
class QuizResult(db.Model):
    __tablename__ = 'quiz_results'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    quiz_id    = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score      = db.Column(db.Integer, default=0)   # correct answers count
    total      = db.Column(db.Integer, default=0)   # total questions
    percentage = db.Column(db.Float,   default=0.0)
    passed     = db.Column(db.Boolean, default=False)
    taken_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuizResult user={self.user_id} score={self.score}/{self.total}>'


# ─────────────────────────────────────────────
# COURSE RATING MODEL
# ─────────────────────────────────────────────
class CourseRating(db.Model):
    __tablename__ = 'course_ratings'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    course_id  = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    review     = db.Column(db.Text,    default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rating user={self.user_id} course={self.course_id} rating={self.rating}>'
