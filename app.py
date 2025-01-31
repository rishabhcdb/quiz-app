from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
from models.models import db, Users, Subjects, Chapter, Quiz, Question # Importing db and Users from models
from functools import wraps

from controllers.login import login_bp
from controllers.student_dashboard import student_dashboard_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db?check_same_thread=False'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretch'  # Add this line

db.init_app(app)  # Initialize the database with the app

app.register_blueprint(login_bp)
app.register_blueprint(student_dashboard_bp)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            # Redirect unauthorized users to login
            flash("You must be an admin to access this page.", "danger")
            return render_template('login.html')
        return f(*args, **kwargs)
    return decorated_function



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


@app.route('/student/start_quiz_prev')
def start_quiz_prev():
    return render_template('start_quiz_prev.html')

@app.route('/student/view_quiz_details/<int:quiz_id>')
def get_quiz_details(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    quiz_questions_numbers = Question.query.filter_by(qz_id=quiz_id).count()
    subject_name = Subjects.query.get(quiz.subject_id).name
    chapter_name = Chapter.query.get(quiz.chapter_id).name
    return render_template('quiz_details_student.html', quiz = quiz,quiz_questions_numbers=quiz_questions_numbers, subject_name= subject_name, chapter_name = chapter_name)



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
        return redirect(request.path)
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

@app.route('/admin/subjects/<int:quiz_id>/quiz_questions', methods=['GET', 'POST','UPDATE'])
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





@app.route("/admin/subjects/new" , methods = ['GET', 'POST'])
def create_subject():
    if request.method== 'POST':
        #subject_id = request.form['s_id']
        subject_name = request.form['s_name']
        description = request.form['description']
        

        new_subject = Subjects(name = subject_name, description = description)
        db.session.add(new_subject)
        db.session.commit()       
        return redirect(url_for("admin_dashboard"))
        #return jsonify(response), 200
    return render_template("create_subject.html")



@app.route("/admin/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    # Find the subject by ID
    subject = Subjects.query.get(subject_id)
    if subject:
        # Get all quizzes associated with the subject
        quizzes = Quiz.query.filter_by(subject_id=subject_id).all()

        # Delete questions associated with these quizzes
        for quiz in quizzes:
            Question.query.filter_by(qz_id=quiz.id).delete()

        # Delete quizzes associated with the subject
        Quiz.query.filter_by(subject_id=subject_id).delete()

        # Delete chapters associated with the subject
        Chapter.query.filter_by(subject_id=subject_id).delete()

        # Delete the subject itself
        db.session.delete(subject)
        db.session.commit()
        flash(f"Subject '{subject.name}' has been deleted successfully!", "success")
    else:
        flash("Subject not found!", "danger")
    
    # Redirect back to the admin dashboard
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/edit_subject/<int:subject_id>")
def redirect_edit_subject(subject_id):
    subject = Subjects.query.get(subject_id)
    return render_template("create_subject.html", subject = subject, is_editing = True)

@app.route("/admin/update_subject/<int:subject_id>", methods = ['POST'])
def update_subject(subject_id):
    if request.method== 'POST':
        #subject_id = request.form['s_id']
        subject_name = request.form['s_name']
        description = request.form['description']
        updated_subject = Subjects.query.get(subject_id)
        updated_subject.name = subject_name
        updated_subject.description = description
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/edit_chapter/<int:chapter_id>")
def redirect_edit_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    subject_id = chapter.subject_id  # Assuming `subject_id` is available in the Chapter model
    return render_template("add_chapter.html", chapter=chapter, is_editing=True, subject_id=subject_id)


@app.route("/admin/update_chapter/<int:chapter_id>", methods=['POST'])
def update_chapter(chapter_id):
    if request.method == 'POST':
        chapter_name = request.form['name']
        description = request.form['description']
        updated_chapter = Chapter.query.get(chapter_id)
        updated_chapter.name = chapter_name
        updated_chapter.description = description
        db.session.commit()

        # Get the subject_id from the chapter (assuming Chapter has a subject_id field)
        subject_id = updated_chapter.subject_id
        return redirect(url_for("chapters_list", subject_id=subject_id))

    # Redirect in case of invalid method
    return redirect(url_for("chapters_list", subject_id=subject_id))




@app.route("/admin/edit_quiz/<int:quiz_id>")
def redirect_edit_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    subject_id = quiz.subject_id
    chapter_id = quiz.chapter_id
    return render_template("add_quiz.html", quiz = quiz, subject_id = subject_id, chapter_id = chapter_id, is_editing = True)




@app.route("/admin/update_quiz/<int:quiz_id>", methods=['POST'])
def update_quiz(quiz_id):
    if request.method == 'POST':
        # Retrieve form data
        date_str = request.form['date_of_quiz']  # Retrieve updated date from the form
        remarks = request.form['remarks']       # Retrieve updated remarks from the form
        duration = request.form['time_duration']  # Retrieve updated duration from the form

        # Convert the date string to a datetime.date object
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400

        # Retrieve the quiz from the database
        updated_quiz = Quiz.query.get(quiz_id)
        if not updated_quiz:
            return "Quiz not found.", 404

        # Update quiz details
        updated_quiz.date_of_quiz = date
        updated_quiz.remarks = remarks
        updated_quiz.time_duration = duration
        db.session.commit()

        # Redirect to the quizzes list for the associated subject and chapter
        subject_id = updated_quiz.subject_id
        chapter_id = updated_quiz.chapter_id
        return redirect(url_for("chapters_list", subject_id=subject_id, chapter_id=chapter_id))

    # Redirect in case of invalid method
    return redirect(url_for("dashboard"))




@app.route('/admin/quiz/<int:quiz_id>/questions/<int:ques_id>/edit', methods=['GET'])
def redirect_edit_question(quiz_id, ques_id):
    # Fetch the question to pre-fill the form
    question = Question.query.get(ques_id)
    if not question:
        return "Question not found", 404

    return render_template('add_question.html', question=question, quiz_id=quiz_id, is_editing = True)



@app.route('/admin/quiz/<int:quiz_id>/questions/<int:ques_id>/update', methods=['POST'])
def update_question(quiz_id, ques_id):
    # Retrieve the question from the database
    question = Question.query.get(ques_id)
    if not question:
        return "Question not found", 404

    # Update question details from the form data
    question.question_text = request.form['question_text']
    question.option1 = request.form['option_1']
    question.option2 = request.form['option_2']
    question.option3 = request.form['option_3']
    question.option4 = request.form['option_4']
    question.correct_option = request.form['correct_option']

    # Commit the changes
    db.session.commit()

    # Redirect back to the quiz questions list
    return redirect(url_for('quiz_questions', quiz_id=quiz_id))







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



