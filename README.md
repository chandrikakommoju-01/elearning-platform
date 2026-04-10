## 🌐 Live Demo
👉 https://elearning-platform-ama9.onrender.com
# 📚 EduLearn — Full-Stack eLearning Platform

A complete eLearning web application with **Student Portal** and **Admin Portal** built with
**Flask + SQLite + Bootstrap 5**.

---

## 🗂️ Project Structure

```
elearning-platform/
│
├── app.py                  ← Main Flask app + all routes
├── models.py               ← SQLAlchemy database models
├── requirements.txt        ← Python dependencies
│
├── static/
│   ├── css/
│   │   └── style.css       ← Custom CSS
│   ├── js/
│   │   └── main.js         ← Custom JavaScript
│   └── uploads/            ← Auto-created on first run
│       ├── thumbnails/     ← Course thumbnail images
│       ├── videos/         ← Uploaded video files
│       ├── materials/      ← PDFs and downloadable files
│       └── avatars/        ← Student profile photos
│
└── templates/
    ├── base.html           ← Master layout (all pages extend this)
    ├── index.html          ← Public landing page
    ├── login.html          ← Login page
    ├── register.html       ← Student registration
    │
    ├── student/
    │   ├── base_student.html   ← Student layout with sidebar
    │   ├── dashboard.html      ← Student home
    │   ├── courses.html        ← Browse & search courses
    │   ├── course_view.html    ← Video player + lesson content
    │   ├── quiz.html           ← Take a quiz
    │   ├── quiz_result.html    ← Quiz score result
    │   └── profile.html        ← Edit profile + quiz history
    │
    ├── admin/
    │   ├── base_admin.html     ← Admin layout with sidebar
    │   ├── dashboard.html      ← Analytics + overview
    │   ├── courses.html        ← Course list table
    │   ├── add_course.html     ← Create new course
    │   ├── edit_course.html    ← Edit existing course
    │   ├── course_detail.html  ← Manage lessons/materials/quizzes
    │   ├── add_lesson.html     ← Add video lesson
    │   ├── add_quiz.html       ← Build quiz with questions
    │   ├── students.html       ← Student management table
    │   └── student_detail.html ← View student profile + progress
    │
    └── errors/
        ├── 403.html
        ├── 404.html
        └── 500.html
```

---

## 🗃️ Database Schema

| Table              | Key Fields |
|--------------------|------------|
| `users`            | id, username, email, password (hashed), role (student/admin) |
| `courses`          | id, title, description, instructor, thumbnail, category, level |
| `lessons`          | id, course_id, title, video_url, duration, order, is_preview |
| `materials`        | id, course_id, lesson_id, title, file_path, file_type |
| `enrollments`      | id, user_id, course_id, completed, progress |
| `lesson_progress`  | id, user_id, course_id, lesson_id, completed |
| `quizzes`          | id, course_id, title, pass_score |
| `quiz_questions`   | id, quiz_id, question, option_a–d, correct_answer |
| `quiz_results`     | id, user_id, quiz_id, score, total, percentage, passed |
| `course_ratings`   | id, user_id, course_id, rating, review |

---

## ⚙️ Setup Instructions

### Step 1 — Prerequisites

Make sure you have **Python 3.9+** installed.
Check by running: `python --version`

---

### Step 2 — Download the Project

Place all files in a folder called `elearning-platform`.

---

### Step 3 — Create a Virtual Environment

Open your terminal / command prompt inside the project folder:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal line.

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug and other required packages.

---

### Step 5 — Run the Application

```bash
python app.py
```

You will see:
```
✅ Database ready. Admin: admin@elearn.com / admin123
 * Running on http://127.0.0.1:5000
```

---

### Step 6 — Open in Browser

Go to: **http://127.0.0.1:5000**

---

## 🔑 Default Login Credentials

| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Admin   | admin@elearn.com       | admin123    |
| Student | student@elearn.com     | student123  |

---

## 🌐 All Available URLs

| URL                        | Description                    |
|----------------------------|--------------------------------|
| `/`                        | Public landing page            |
| `/login`                   | Login for both portals         |
| `/register`                | Student registration           |
| `/student/dashboard`       | Student home                   |
| `/student/courses`         | Browse + search courses        |
| `/student/course/<id>`     | View course + watch lessons    |
| `/student/profile`         | Edit student profile           |
| `/student/quiz/<id>`       | Take a quiz                    |
| `/admin/dashboard`         | Admin analytics                |
| `/admin/courses`           | Manage all courses             |
| `/admin/course/add`        | Create new course              |
| `/admin/course/<id>`       | Manage course content          |
| `/admin/students`          | View & manage students         |
| `/admin/student/<id>`      | Student detail + progress      |

---

## 🚀 How to Use — Admin Workflow

1. Login as admin → `admin@elearn.com / admin123`
2. Go to **Add Course** → fill title, description, instructor, thumbnail
3. Open the course → click **Add Lesson** → paste YouTube embed URL or upload video
4. Upload **PDFs** via "Upload Material" button
5. Click **Add Quiz** → type questions and options dynamically
6. View **Students** tab to monitor progress

## 📖 How to Use — Student Workflow

1. Register or login as `student@elearn.com / student123`
2. Browse **Courses** → click **Enroll Free**
3. Watch video lessons → click **Mark Complete** after each one
4. Download materials (PDFs) from the lesson sidebar
5. Take quizzes and view your score
6. Rate the course after completion
7. Update your profile photo and bio

---

## 🔒 Security Features

- Passwords hashed with **Werkzeug PBKDF2-SHA256**
- Session management via **Flask-Login**
- Admin routes protected by custom `@admin_required` decorator
- File downloads restricted to enrolled students only
- Secure filenames via `werkzeug.utils.secure_filename`

---

## 💡 Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port already in use | Change `port=5000` to `port=5001` in `app.py` |
| Images not showing | Make sure `static/uploads/` folder exists |
| Database errors | Delete `elearning.db` and rerun `python app.py` |
