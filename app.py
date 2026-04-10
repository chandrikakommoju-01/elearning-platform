# app.py — Main Flask Application
# eLearning Platform — Student + Admin Portals
# Run: python app.py

import os, uuid
from datetime import datetime
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, session, send_from_directory, abort)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename
from models import (db, User, Course, Lesson, Material,
                    Enrollment, LessonProgress, Quiz, QuizQuestion,
                    QuizResult, CourseRating)

# ─────────────────────────────────────────────
# APP CONFIGURATION
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY']           = 'elearn-super-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elearning.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']        = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH']   = 500 * 1024 * 1024   # 500 MB max upload

ALLOWED_VIDEO  = {'mp4', 'webm', 'mov'}
ALLOWED_DOC    = {'pdf', 'doc', 'docx', 'pptx', 'xlsx', 'zip', 'txt'}
ALLOWED_IMAGE  = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Init extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view       = 'login'
login_manager.login_message    = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def save_file(file, subfolder, allowed_set):
    """Save an uploaded file and return the saved filename."""
    if file and allowed_file(file.filename, allowed_set):
        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        folder   = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        return filename
    return None


def admin_required(f):
    """Decorator: only admins can access this route."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────
@app.route('/')
def index():
    """Landing page — shows featured courses."""
    courses = Course.query.filter_by(is_active=True).order_by(Course.created_at.desc()).limit(6).all()
    total_students = User.query.filter_by(role='student').count()
    total_courses  = Course.query.filter_by(is_active=True).count()
    return render_template('index.html',
                           courses=courses,
                           total_students=total_students,
                           total_courses=total_courses)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student self-registration."""
    if current_user.is_authenticated:
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        username  = request.form.get('username',  '').strip()
        email     = request.form.get('email',     '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        password  = request.form.get('password',  '')
        confirm   = request.form.get('confirm',   '')

        # Validations
        if not all([username, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')

        user = User(username=username, email=email, full_name=full_name, role='student')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login for both students and admins."""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard') if current_user.is_admin() else url_for('student_dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            if user.is_admin():
                return redirect(next_page or url_for('admin_dashboard'))
            return redirect(next_page or url_for('student_dashboard'))
        flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# STUDENT PORTAL ROUTES
# ─────────────────────────────────────────────
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student home — enrolled courses + progress."""
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    available   = Course.query.filter_by(is_active=True).order_by(Course.created_at.desc()).limit(4).all()
    return render_template('student/dashboard.html',
                           enrollments=enrollments,
                           available=available)


@app.route('/student/courses')
@login_required
def student_courses():
    """Browse all available courses with search + filter."""
    search   = request.args.get('q', '')
    category = request.args.get('category', '')
    level    = request.args.get('level', '')

    query = Course.query.filter_by(is_active=True)
    if search:
        query = query.filter(Course.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)

    courses    = query.order_by(Course.created_at.desc()).all()
    categories = db.session.query(Course.category).distinct().all()
    enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()]

    return render_template('student/courses.html',
                           courses=courses,
                           categories=[c[0] for c in categories],
                           enrolled_ids=enrolled_ids,
                           search=search)


@app.route('/student/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    """Enroll student in a course."""
    course   = Course.query.get_or_404(course_id)
    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing:
        flash('You are already enrolled in this course.', 'info')
    else:
        enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Successfully enrolled in "{course.title}"!', 'success')
    return redirect(url_for('course_view', course_id=course_id))


@app.route('/student/course/<int:course_id>')
@login_required
def course_view(course_id):
    """View course content — lessons, materials, quiz."""
    course     = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    lesson_id  = request.args.get('lesson', None)

    # Get selected lesson (default: first)
    current_lesson = None
    if lesson_id:
        current_lesson = Lesson.query.get(int(lesson_id))
    elif course.lessons:
        current_lesson = course.lessons[0]

    # Get completed lesson IDs for this student
    completed_ids = [p.lesson_id for p in
                     LessonProgress.query.filter_by(user_id=current_user.id,
                                                    course_id=course_id,
                                                    completed=True).all()]

    # Rating by this student
    my_rating = CourseRating.query.filter_by(user_id=current_user.id, course_id=course_id).first()

    return render_template('student/course_view.html',
                           course=course,
                           enrollment=enrollment,
                           current_lesson=current_lesson,
                           completed_ids=completed_ids,
                           my_rating=my_rating)


@app.route('/student/complete_lesson/<int:lesson_id>')
@login_required
def complete_lesson(lesson_id):
    """Mark a lesson as completed."""
    lesson = Lesson.query.get_or_404(lesson_id)
    existing = LessonProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()
    if not existing:
        prog = LessonProgress(user_id=current_user.id,
                              course_id=lesson.course_id,
                              lesson_id=lesson_id,
                              completed=True)
        db.session.add(prog)
    else:
        existing.completed  = True
        existing.updated_at = datetime.utcnow()

    # Check if all lessons completed → mark course complete
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=lesson.course_id).first()
    if enrollment:
        total     = len(lesson.course.lessons)
        completed = LessonProgress.query.filter_by(
            user_id=current_user.id,
            course_id=lesson.course_id,
            completed=True
        ).count() + (0 if existing else 1)
        if total > 0 and completed >= total:
            enrollment.completed    = True
            enrollment.completed_at = datetime.utcnow()
            flash('🎉 Congratulations! You completed this course!', 'success')

    db.session.commit()
    return redirect(url_for('course_view', course_id=lesson.course_id, lesson=lesson_id))


@app.route('/student/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(quiz_id):
    """Student takes a quiz."""
    quiz = Quiz.query.get_or_404(quiz_id)

    # Check already taken
    existing = QuizResult.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    if existing:
        return redirect(url_for('quiz_result', result_id=existing.id))

    if request.method == 'POST':
        score = 0
        total = len(quiz.questions)
        for q in quiz.questions:
            answer = request.form.get(f'q_{q.id}', '')
            if answer.lower() == q.correct_answer.lower():
                score += 1

        percentage = round((score / total * 100), 1) if total > 0 else 0
        passed     = percentage >= quiz.pass_score

        result = QuizResult(
            user_id    = current_user.id,
            quiz_id    = quiz_id,
            score      = score,
            total      = total,
            percentage = percentage,
            passed     = passed
        )
        db.session.add(result)
        db.session.commit()
        flash(f'Quiz submitted! You scored {score}/{total} ({percentage}%).', 'success' if passed else 'warning')
        return redirect(url_for('quiz_result', result_id=result.id))

    return render_template('student/quiz.html', quiz=quiz)


@app.route('/student/quiz/result/<int:result_id>')
@login_required
def quiz_result(result_id):
    """Show quiz result to student."""
    result = QuizResult.query.get_or_404(result_id)
    if result.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    return render_template('student/quiz_result.html', result=result)


@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
def student_profile():
    """Update student profile."""
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '').strip()
        current_user.bio       = request.form.get('bio', '').strip()

        # Handle avatar upload
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            filename = save_file(avatar_file, 'avatars', ALLOWED_IMAGE)
            if filename:
                current_user.avatar = filename

        # Handle password change
        new_pass = request.form.get('new_password', '')
        if new_pass:
            if len(new_pass) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('student_profile'))
            current_user.set_password(new_pass)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))

    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    return render_template('student/profile.html', enrollments=enrollments)


@app.route('/student/rate/<int:course_id>', methods=['POST'])
@login_required
def rate_course(course_id):
    """Student submits a course rating."""
    rating_val = int(request.form.get('rating', 5))
    review     = request.form.get('review', '').strip()

    existing = CourseRating.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing:
        existing.rating = rating_val
        existing.review = review
    else:
        r = CourseRating(user_id=current_user.id, course_id=course_id,
                         rating=rating_val, review=review)
        db.session.add(r)
    db.session.commit()
    flash('Thank you for your rating!', 'success')
    return redirect(url_for('course_view', course_id=course_id))


@app.route('/download/<int:material_id>')
@login_required
def download_material(material_id):
    """Serve a downloadable file to enrolled student."""
    material   = Material.query.get_or_404(material_id)
    enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=material.course_id
    ).first()
    if not enrollment and not current_user.is_admin():
        abort(403)
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'materials')
    return send_from_directory(folder, material.file_path, as_attachment=True,
                               download_name=material.title)


# ─────────────────────────────────────────────
# ADMIN PORTAL ROUTES
# ─────────────────────────────────────────────
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin home with analytics overview."""
    total_students  = User.query.filter_by(role='student').count()
    total_courses   = Course.query.count()
    total_enrollments = Enrollment.query.count()
    total_quizzes   = Quiz.query.count()
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_courses  = Course.query.order_by(Course.created_at.desc()).limit(5).all()

    # Enrollment data per course (for chart)
    courses_data = db.session.query(
        Course.title,
        db.func.count(Enrollment.id).label('count')
    ).join(Enrollment, isouter=True).group_by(Course.id).limit(6).all()

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           total_quizzes=total_quizzes,
                           recent_students=recent_students,
                           recent_courses=recent_courses,
                           courses_data=courses_data)


@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    """List all courses."""
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('admin/courses.html', courses=courses)


@app.route('/admin/course/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    """Create a new course."""
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        instructor  = request.form.get('instructor', '').strip()
        category    = request.form.get('category', 'General')
        level       = request.form.get('level', 'Beginner')

        if not all([title, description, instructor]):
            flash('Title, description and instructor are required.', 'danger')
            return render_template('admin/add_course.html')

        thumbnail_file = request.files.get('thumbnail')
        thumbnail_name = save_file(thumbnail_file, 'thumbnails', ALLOWED_IMAGE) or 'default_course.png'

        course = Course(title=title, description=description,
                        instructor=instructor, category=category,
                        level=level, thumbnail=thumbnail_name)
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{title}" created successfully!', 'success')
        return redirect(url_for('admin_course_detail', course_id=course.id))

    return render_template('admin/add_course.html')


@app.route('/admin/course/<int:course_id>')
@login_required
@admin_required
def admin_course_detail(course_id):
    """Manage a specific course — lessons, materials, quizzes."""
    course = Course.query.get_or_404(course_id)
    return render_template('admin/course_detail.html', course=course)


@app.route('/admin/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit a course."""
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.title       = request.form.get('title', course.title).strip()
        course.description = request.form.get('description', course.description).strip()
        course.instructor  = request.form.get('instructor', course.instructor).strip()
        course.category    = request.form.get('category', course.category)
        course.level       = request.form.get('level', course.level)
        course.is_active   = bool(request.form.get('is_active'))

        thumb = request.files.get('thumbnail')
        if thumb and thumb.filename:
            filename = save_file(thumb, 'thumbnails', ALLOWED_IMAGE)
            if filename:
                course.thumbnail = filename

        db.session.commit()
        flash('Course updated!', 'success')
        return redirect(url_for('admin_course_detail', course_id=course_id))

    return render_template('admin/edit_course.html', course=course)


@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete a course (cascade deletes all related data)."""
    course = Course.query.get_or_404(course_id)
    title  = course.title
    db.session.delete(course)
    db.session.commit()
    flash(f'Course "{title}" deleted.', 'success')
    return redirect(url_for('admin_courses'))


@app.route('/admin/course/<int:course_id>/add_lesson', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson(course_id):
    """Add a video lesson to a course."""
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        video_url   = request.form.get('video_url', '').strip()  # YouTube URL
        duration    = request.form.get('duration', '').strip()
        order       = int(request.form.get('order', len(course.lessons) + 1))
        is_preview  = bool(request.form.get('is_preview'))

        # Handle video file upload (optional)
        video_file = request.files.get('video_file')
        if video_file and video_file.filename:
            saved = save_file(video_file, 'videos', ALLOWED_VIDEO)
            if saved:
                video_url = f'/static/uploads/videos/{saved}'

        lesson = Lesson(course_id=course_id, title=title, description=description,
                        video_url=video_url, duration=duration,
                        order=order, is_preview=is_preview)
        db.session.add(lesson)
        db.session.commit()

        # Handle material upload for this lesson
        mat_file  = request.files.get('material')
        mat_title = request.form.get('material_title', '').strip()
        if mat_file and mat_file.filename and mat_title:
            mat_saved = save_file(mat_file, 'materials', ALLOWED_DOC)
            if mat_saved:
                ext  = mat_file.filename.rsplit('.', 1)[1].lower()
                size = f"{round(mat_file.content_length / 1024, 1)} KB" if mat_file.content_length else ''
                mat  = Material(course_id=course_id, lesson_id=lesson.id,
                                title=mat_title, file_path=mat_saved,
                                file_type=ext, file_size=size)
                db.session.add(mat)
                db.session.commit()

        flash('Lesson added successfully!', 'success')
        return redirect(url_for('admin_course_detail', course_id=course_id))

    return render_template('admin/add_lesson.html', course=course)


@app.route('/admin/lesson/<int:lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    """Delete a lesson."""
    lesson    = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash('Lesson deleted.', 'success')
    return redirect(url_for('admin_course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/add_material', methods=['POST'])
@login_required
@admin_required
def add_material(course_id):
    """Upload a downloadable material to a course."""
    title    = request.form.get('title', '').strip()
    mat_file = request.files.get('file')
    if mat_file and mat_file.filename and title:
        saved = save_file(mat_file, 'materials', ALLOWED_DOC)
        if saved:
            ext = mat_file.filename.rsplit('.', 1)[1].lower()
            mat = Material(course_id=course_id, title=title,
                           file_path=saved, file_type=ext)
            db.session.add(mat)
            db.session.commit()
            flash('Material uploaded!', 'success')
    else:
        flash('Title and file are required.', 'danger')
    return redirect(url_for('admin_course_detail', course_id=course_id))


@app.route('/admin/material/<int:material_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_material(material_id):
    """Delete a material."""
    mat       = Material.query.get_or_404(material_id)
    course_id = mat.course_id
    db.session.delete(mat)
    db.session.commit()
    flash('Material deleted.', 'success')
    return redirect(url_for('admin_course_detail', course_id=course_id))


@app.route('/admin/course/<int:course_id>/add_quiz', methods=['GET', 'POST'])
@login_required
@admin_required
def add_quiz(course_id):
    """Create a quiz for a course."""
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        pass_score  = int(request.form.get('pass_score', 70))

        quiz = Quiz(course_id=course_id, title=title,
                    description=description, pass_score=pass_score)
        db.session.add(quiz)
        db.session.flush()  # get quiz.id before commit

        # Add questions dynamically
        questions_data = []
        i = 1
        while request.form.get(f'q_{i}'):
            questions_data.append({
                'q':       request.form.get(f'q_{i}'),
                'a':       request.form.get(f'a_{i}'),
                'b':       request.form.get(f'b_{i}'),
                'c':       request.form.get(f'c_{i}'),
                'd':       request.form.get(f'd_{i}'),
                'correct': request.form.get(f'correct_{i}'),
                'order':   i
            })
            i += 1

        for qd in questions_data:
            q = QuizQuestion(quiz_id=quiz.id,
                             question=qd['q'],
                             option_a=qd['a'], option_b=qd['b'],
                             option_c=qd['c'], option_d=qd['d'],
                             correct_answer=qd['correct'],
                             order=qd['order'])
            db.session.add(q)

        db.session.commit()
        flash(f'Quiz "{title}" created with {len(questions_data)} questions!', 'success')
        return redirect(url_for('admin_course_detail', course_id=course_id))

    return render_template('admin/add_quiz.html', course=course)


@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    """Delete a quiz."""
    quiz      = Quiz.query.get_or_404(quiz_id)
    course_id = quiz.course_id
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted.', 'success')
    return redirect(url_for('admin_course_detail', course_id=course_id))


@app.route('/admin/students')
@login_required
@admin_required
def admin_students():
    """View all students."""
    search   = request.args.get('q', '')
    query    = User.query.filter_by(role='student')
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    students = query.order_by(User.created_at.desc()).all()
    return render_template('admin/students.html', students=students, search=search)


@app.route('/admin/student/<int:student_id>')
@login_required
@admin_required
def admin_student_detail(student_id):
    """View a student's full detail."""
    student     = User.query.get_or_404(student_id)
    enrollments = Enrollment.query.filter_by(user_id=student_id).all()
    results     = QuizResult.query.filter_by(user_id=student_id).all()
    return render_template('admin/student_detail.html',
                           student=student,
                           enrollments=enrollments,
                           results=results)


@app.route('/admin/student/<int:student_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_student(student_id):
    """Activate / deactivate a student account."""
    student           = User.query.get_or_404(student_id)
    student.is_active = not student.is_active
    db.session.commit()
    status = 'activated' if student.is_active else 'deactivated'
    flash(f'Student {student.username} has been {status}.', 'success')
    return redirect(url_for('admin_students'))


# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# ─────────────────────────────────────────────
# DATABASE INIT + SEED
# ─────────────────────────────────────────────
def create_tables():
    """Create all tables and seed default admin + demo data."""
    with app.app_context():
        db.create_all()

        # Create admin if not exists
        if not User.query.filter_by(email='admin@elearn.com').first():
            admin = User(username='admin', email='admin@elearn.com',
                        full_name='Administrator', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # Create demo student
        if not User.query.filter_by(email='student@elearn.com').first():
            student = User(username='demo_student', email='student@elearn.com',
                          full_name='Demo Student', role='student')
            student.set_password('student123')
            db.session.add(student)
            db.session.flush()

            # Demo course
            if Course.query.count() == 0:
                course = Course(
                    title='Python for Beginners',
                    description='Learn Python programming from scratch. This comprehensive course covers all fundamentals.',
                    instructor='John Smith',
                    category='Programming',
                    level='Beginner',
                    thumbnail='default_course.png'
                )
                db.session.add(course)
                db.session.flush()

                # Demo lessons
                for i, (t, url) in enumerate([
                    ('Introduction to Python', 'https://www.youtube.com/embed/kqtD5dpn9C8'),
                    ('Variables & Data Types',  'https://www.youtube.com/embed/cQT33yu9pY8'),
                    ('Control Flow',            'https://www.youtube.com/embed/f4KOjWS_KZs'),
                ], 1):
                    lesson = Lesson(course_id=course.id, title=t, video_url=url, order=i)
                    db.session.add(lesson)
                db.session.flush()

                # Demo quiz
                quiz = Quiz(course_id=course.id, title='Python Basics Quiz', pass_score=60)
                db.session.add(quiz)
                db.session.flush()

                questions = [
                    ('What is Python?', 'A snake', 'A programming language', 'A database', 'An OS', 'b'),
                    ('Which is correct?', 'x == 5', 'x = = 5', 'x := 5', 'x => 5', 'a'),
                    ('Output of print(2**3)?', '6', '9', '8', '23', 'c'),
                ]
                for i, (q, a, b, c, d, correct) in enumerate(questions, 1):
                    qq = QuizQuestion(quiz_id=quiz.id, question=q,
                                      option_a=a, option_b=b,
                                      option_c=c, option_d=d,
                                      correct_answer=correct, order=i)
                    db.session.add(qq)

                # Enroll demo student
                enroll = Enrollment(user_id=student.id, course_id=course.id)
                db.session.add(enroll)

        db.session.commit()
        print("✅ Database ready. Admin: admin@elearn.com / admin123")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)
