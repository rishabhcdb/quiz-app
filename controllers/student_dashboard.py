from flask import Blueprint, render_template, request, session, redirect, url_for, session
from models.models import db, Users, Subjects, Chapter, Quiz, Question # Importing db and Users from models



student_dashboard_bp= Blueprint('student_dashboard', __name__)


@student_dashboard_bp.route('/student')
def student_dashboard():
    # Step 1: Get the logged-in user ID from the session
    user_id = session.get('user_id')  # Ensure 'user_id' is set during login

    if user_id:
        # Step 2: Query the user from the database
        user = Users.query.get(user_id)
        
        if user:
            # Step 3: Pass the user's name and quizzes to the template
            quizzes = Quiz.query.all()
            return render_template('student_dashboard.html', quizzes=quizzes, userName=user.fullName)
        else:
            return "User not found", 404
    else:
        # Step 4: Redirect to login if no user is logged in
        return redirect('/login')