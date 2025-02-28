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
- **Frontend:** Jinja2, HTML, CSS, Javascript


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


## Usage

- **Admin Dashboard:** Manage users, subjects, quizzes, and view reports.
  **NOTE:** 
  Admin is a superuser, and is created when the database is initialised, hence there is no need for Admin signup.
  The admin can directly login with the following credentials (hardcoded in app.py while initialising)
  Email: admin
  Password: iamadmin

- **User Dashboard:** Attempt quizzes, view scores, and track progress.
    Every user needs to sign-up and login seperately

    **Running the app**
    Run the app.py file, database will automatically be created (if doesn't already exists)
    Follow the http://127.0.0.1:5000 link that appears in the terminal

    **Project Demo Video:**
    https://drive.google.com/file/d/1nnPa40-VusR5BdQ0YDRcLxt3LsSCuWZ5/view?usp=sharing

    Enjoy!!





