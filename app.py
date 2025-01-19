from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
from models.models import db, Users, Subjects, Chapter, Quiz, Question # Importing db and Users from models
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db?check_same_thread=False'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretch'  # Add this line

db.init_app(app)  # Initialize the database with the app

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            # Redirect unauthorized users to login
            flash("You must be an admin to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['POST', 'GET'])
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
                return redirect(url_for('student_dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/admin/subjects/<int:subject_id>/<int:chapter_id>/details/create', methods=['GET', 'POST'])
def create_quiz(subject_id, chapter_id):
    if request.method == 'POST':
        # Fetch form data
        
        chapter_id = request.form['chapter_id']
        subject_id = request.form['subject_id']
        date_of_quiz = request.form['date_of_quiz']
        duration = request.form['time_duration']
        remarks = request.form['remarks']

        # Validate and process inputs
        try:
            date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d").date()
            duration = int(duration)
        except ValueError:
            return "Invalid input format", 400

        # Create new quiz
        new_quiz = Quiz(
            chapter_id=chapter_id,
            subject_id= subject_id,
            date_of_quiz=date_of_quiz,
            time_duration=duration,
            remarks=remarks
        )


        db.session.add(new_quiz)
        db.session.commit()

        # Respond with success
        return redirect(url_for('chapters_list', subject_id=subject_id))

    # If it's a GET request, render the quiz creation form
    return render_template('add_quiz.html', subject_id=subject_id, chapter_id=chapter_id)



@app.route('/admin/subjects/<int:subject_id>/chapters/<int:chapter_id>/quiz/<int:quiz_id>/delete', methods=['POST'])
def delete_quiz(subject_id, chapter_id, quiz_id):
    # Find the quiz by ID
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        # Find all questions related to the quiz
        questions = Question.query.filter_by(qz_id=quiz_id).all()
        if questions:
            for question in questions:
                db.session.delete(question)  # Delete each question

        # Delete the quiz itself
        db.session.delete(quiz)
        db.session.commit()
        return redirect(url_for('chapters_list', subject_id=subject_id))
    else:
        return "Quiz not found", 404


@app.route('/admin/subjects/<int:subject_id>/details/<int:qz_id>/delete_question/<int:ques_id>', methods=['POST'])
def delete_question(subject_id, qz_id, ques_id):
    # Fetch the question by its ID
    question = Question.query.get(ques_id)
    
    if question:
        db.session.delete(question)
        db.session.commit()
        all_questions = Question.query.filter_by(qz_id=qz_id).all()
        
        # Provide feedback to the admin and return to the questions page
        return render_template('quiz_questions.html', 
                               q_id=qz_id, 
                               questions=all_questions, 
                               subject_id=subject_id, 
                               message="Question deleted successfully!")
    else:
        # Return an error message if the question doesn't exist
        return render_template('quiz_questions.html', 
                               q_id=qz_id, 
                               questions=Question.query.filter_by(qz_id=qz_id).all(), 
                               subject_id=subject_id, 
                               message="Question not found.")


@app.route('/admin/subjects/<int:subject_id>/details/<int:qz_id>/add_questions', methods = ['GET', 'POST'])
def add_questions(subject_id, qz_id):
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_1 = request.form['option_1']
        option_2 = request.form['option_2']
        option_3 = request.form['option_3']
        option_4 = request.form['option_4']
        correct_option = request.form['correct_option']

        new_question = Question(           
            qz_id = qz_id,
            question_text = question_text,
            option1 = option_1,
            option2 = option_2,
            option3 = option_3,
            option4 = option_4,
            correct_option = correct_option
        )

        db.session.add(new_question)
        db.session.commit()

        all_questions = Question.query.filter_by(qz_id = qz_id).all()
        response = {
            "message": "success",
            "user": {
                "id": new_question.ques_id,               
            }
        }
        return render_template('quiz_questions.html', q_id=qz_id, questions= all_questions, subject_id=subject_id)
       # return (response), 200

    else:      
        return render_template('add_question.html', subject_id=subject_id, qz_id=qz_id)
       # return jsonify (response), 200

        
       # return redirect(url_for('subject_details'))


@app.route('/')
def index():
    return render_template('register.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userName = request.form['userName']
        password = request.form['password']
        fullName = request.form['fullName']


        existing_user = Users.query.filter_by(userName=userName).first()

        if existing_user:
            return render_template('register.html', error="User already exists. Please use a different email.")
            # User exists, show "User already exists" message
            #return jsonify({"message": "User already exists"}), 400

        # Create and save the new user
        new_user = Users(userName=userName, passWord=password, fullName=fullName)
        db.session.add(new_user)
        db.session.commit()

        # Prepare and return the JSON response
        response = {
            "message": "success",
            "user": {
                "id": new_user.userId,
                "userName": new_user.userName,
                "fullName": new_user.fullName
            }
        }
        #return jsonify(response), 200
        return render_template('login.html')
    elif request.method == 'GET':
        return render_template('register.html')




@app.route('/admin')
@admin_required
def admin_dashboard():
    subjects = Subjects.query.all()
    subjects_with_chapters = []
    for subject in subjects:
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        subjects_with_chapters.append({
            'subject': subject,
            'chapters': chapters
        })
    return render_template('admin_dashboard.html', arr_items=subjects_with_chapters)


@app.route('/admin/subject/<int:subject_id>/chapters_list')
def chapters_list(subject_id):
    # Fetch the specific subject by ID
    subject = Subjects.query.get(subject_id)
    if not subject:
        return "Subject not found", 404  # Handle the case where the subject is not found

    # Get all chapters related to this subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    quizzes_with_chapters = []
    for chapter in chapters:
        quizzes = Quiz.query.filter_by(chapter_id = chapter.id).all()
        quizzes_with_chapters.append({
            'chapter': chapter,
            'quiz': quizzes
        })
    print(quizzes_with_chapters)
    return render_template('chapters_list.html', arr_quiz = quizzes_with_chapters, subject = subject )

@app.route('/admin/subjects/<int:quiz_id>/quiz_questions', methods=['GET', 'POST'])
def quiz_questions(quiz_id):
    # Fetch all questions for the given quiz
    questions = Question.query.filter_by(qz_id=quiz_id).all()

    # Fetch the quiz details to retrieve the subject_id
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return "Quiz not found", 404

    # Pass questions, quiz, and subject_id to the template
    return render_template(
        'quiz_questions.html',
        questions=questions,
        q_id=quiz.id,
        subject_id=quiz.subject_id
    )



@app.route('/student')
def student_dashboard():
    subjects = Subjects.query.all()
    return render_template('student_dashboard.html', subjects=subjects)

@app.route("/admin/subjects/new" , methods = ['GET', 'POST'])
def create_subject():
    if request.method== 'POST':
        #subject_id = request.form['s_id']
        subject_name = request.form['s_name']
        description = request.form['description']
        

        new_subject = Subjects(name = subject_name, description = description)
        db.session.add(new_subject)
        db.session.commit()

        '''
        response = {
           # "subject_id": subject_id,
            "subject_name": new_subject.name,
            "description": new_subject.description,
            "s_id": new_subject.id

        }'''
        
        return redirect(url_for("admin_dashboard"))
        #return jsonify(response), 200
    
    return render_template("create_subject.html")



@app.route("/admin/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    # Find the subject by ID
    subject = Subjects.query.get(subject_id)
    if subject:
        # Delete quizzes associated with the subject
        Quiz.query.filter_by(subject_id=subject_id).delete()

        # Delete chapters associated with the subject
        Chapter.query.filter_by(subject_id=subject_id).delete()

        # Delete the subject from the database
        db.session.delete(subject)
        db.session.commit()
        flash(f"Subject '{subject.name}' has been deleted successfully!", "success")
    else:
        flash("Subject not found!", "danger")
    
    # Redirect back to the admin dashboard
    return redirect(url_for("admin_dashboard"))


@app.route('/admin/subjects/chapters/<int:subject_id>', methods=['GET', 'POST'])
  # This handles chapter_id
def add_chapters(subject_id):
    if request.method == 'GET':
        arrChapters = Chapter.query.filter_by(subject_id=subject_id).all()
        if arrChapters:           
            chapters_data = [chapter.to_dict() for chapter in arrChapters]  
            return render_template('add_chapter.html', subject_id=subject_id)         
            return jsonify(chapters_data), 200
        else:
            # Return a response if no chapters were found for the given subject
            return jsonify({"message": "No chapters found for this subject."}), 404


    elif request.method== 'POST':
        chapter_name = request.form['name']
        description = request.form['description']
        new_chapter = Chapter(subject_id = subject_id, name= chapter_name, description = description)
        db.session.add(new_chapter)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    

        return render_template('add_chapter.html', subject_id=subject_id)
        return redirect(url_for("admin_dashboard"))
        return jsonify ({'message': 'added chapter',
                         'chapter_id': new_chapter.id }), 200
    
    
        


    


@app.route('/admin/subjects/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    # Fetch the chapter to be deleted
    del_ch = Chapter.query.get(chapter_id)

    if del_ch:
        # Find all quizzes associated with the chapter
        del_quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        if del_quizzes:
            for quiz in del_quizzes:
                # Delete all questions associated with the quiz
                Question.query.filter_by(qz_id=quiz.id).delete()
                db.session.delete(quiz)

        # Delete the chapter
        db.session.delete(del_ch)
        db.session.commit()

        return redirect(url_for("admin_dashboard"))
        return flash(message = "chapter deleted succesfully")


    else:
        return jsonify({'message': "Chapter doesn't exist"}), 404



@app.route('/admin/subjects/<int:subject_id>/add_chapter')
def render_addchapter(subject_id):
    return render_template('add_chapter.html', subject_id = subject_id)



'''   wrong code for below code
@app.route('/admin/subjects/<int:subject_id>/details', methods = ['GET'])
def subject_details(subject_id):
    subject = Subjects.query.get(subject_id)
    if not subject:
        return "Subject not found", 404  # Handle case where subject doesn't exist
    
    # Fetch chapters for the subject (replace with your ORM query)
    Chapter = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('subject_details.html', subject_id = subject_id) '''




@app.route('/admin/subjects/<int:subject_id>/details', methods=['GET'])
def subject_details(subject_id):
    # Fetch subject details
    subject = Subjects.query.get(subject_id)
    if not subject:
        return "Subject not found", 404

    # Fetch all quizzes for the subject
    else:
        quizzes = (Quiz.query.filter_by(subject_id = subject_id).all())



    # Pass data to the template
    return render_template('subject_details.html', subject=subject, quizzes=quizzes)





@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))







if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database tables
        print("Database initialized!")


        # Check if the admin user exists
        admin = Users.query.filter_by(userName='admin').first()
        if not admin:
            # Create the admin user
            admin = Users(
                userName='admin',
                passWord='iamadmin',  # Use a hashed password in production
                fullName='Quiz Master',
                isAdmin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.debug = True
    app.run()



