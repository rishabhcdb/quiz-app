from flask import Blueprint, render_template, request, session, redirect, url_for, session
from models.models import db, Users, Subjects, Chapter, Quiz, Question # Importing db and Users from models


login_bp = Blueprint ('login', __name__)

@login_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        userName = request.form['userName']
        password = request.form['password']

        user = Users.query.filter_by(userName=userName, passWord=password).first()

        if user:
            # Set session variables
            session['user_id'] = user.userId
            session['is_admin'] = user.isAdmin
            session['user_name'] = user.userName
            
            if user.isAdmin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard.student_dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')



