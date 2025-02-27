# quiz-master-v1
This is a web-app project that helps students to prepare for exams utilizing Quizzes

# Quiz Master - V1

## Overview

Quiz Master is a multi-user web application designed for exam preparation across multiple subjects. It allows an administrator (Quiz Master) to create and manage quizzes, while registered users can attempt quizzes and track their scores.

## Features

- **Admin Role**

  - Single superuser (Quiz Master) with full control.
  - Manages users, subjects, chapters, quizzes, and questions.
  - Creates, updates, and deletes quizzes and questions.
  - Searches for users, subjects, and quizzes.
  - Views summary charts for quiz performance.

- **User Role**

  - Registers and logs into the platform.
  - Selects subjects and chapters for quizzes.
  - Attempts quizzes with multiple-choice questions.
  - Views past quiz scores and statistics.

## Technologies Used

- **Backend:** Flask (Python)
- **Database:** SQLite (using SQLAlchemy ORM)
- **Frontend:** Jinja2, HTML, CSS


## Project Structure

```
QuizMaster/
│-- controllers/         # Handles request logic
│-- models/              # Database models
│   ├── models.py        # Defines tables (Users, Subjects, Chapters, etc.)
│   ├── db.py            # Database configuration
│   ├── create_db.py     # Script to initialize the database
│-- static/              # CSS, JavaScript, images
│-- templates/           # Jinja2 templates (HTML files)
│-- app.py               # Main application file
│-- README.md            # Project documentation
```

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd QuizMaster
   ```
2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use 'venv\Scripts\activate'
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize the Database:**
   ```bash
   python models/create_db.py
   ```
5. **Run the Application:**
   ```bash
   python app.py
   ```
6. **Access the Web App:** Open `http://127.0.0.1:5000` in your browser.

## Usage

- **Admin Dashboard:** Manage users, subjects, quizzes, and view reports.
- **User Dashboard:** Attempt quizzes, view scores, and track progress.

## License

This project is for educational purposes and follows an open-source license.

---

Let me know if you need any modifications or enhancements! 🚀



