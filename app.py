from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
from models.models import db, Users, Subjects, Chapter, Quiz, Question, Score # Importing db and Users from models
from functools import wraps
from werkzeug.security import generate_password_hash
import time
from controllers.login import login_bp
from controllers.student_dashboard import student_dashboard_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretch'  

db.init_app(app)  

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
    query = request.args.get('query', '').strip()
    
    if query:
        subjects = Subjects.query.filter(Subjects.name.ilike(f"%{query}%")).all()
    else:
        subjects = Subjects.query.all()
    
    subjects_with_chapters = []
    for subject in subjects:
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        subjects_with_chapters.append({
            'subject': subject,
            'chapters': chapters
        })
    
    return render_template('admin_dashboard.html', arr_items=subjects_with_chapters)



@app.route('/student/scores')
def student_scores():
    user_id = session.get('user_id')  # Get logged-in student's ID
    
    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if user not found

    # Fetch scores for the logged-in student
    scores = Score.query.filter_by(userId=user_id).all()

    # Fetch quiz names using qz_id
    quiz_names = [Quiz.query.get(score.qz_id).remarks if Quiz.query.get(score.qz_id) else "Unknown Quiz" for score in scores]
    quiz_scores = [score.score for score in scores]  # Extract score percentages
    
    # Combine quiz names and scores into tuples
    quiz_scores_data = list(zip(quiz_names, quiz_scores))

    return render_template('scores_sd.html', quiz_names=quiz_names, quiz_scores=quiz_scores, quiz_scores_data=quiz_scores_data)



@app.route('/student/performance')
def student_performance():
    user_id = session.get('user_id')  # Get logged-in student's ID
    
    if not user_id:
        return redirect(url_for('login'))  # Redirect to login if user not found

    # Fetch subjects and count quizzes attempted per subject
    subject_attempts = (
        db.session.query(Subjects.name, db.func.count(Score.qz_id))
        .join(Quiz, Quiz.id == Score.qz_id)
        .join(Subjects, Subjects.id == Quiz.subject_id)
        .filter(Score.userId == user_id)
        .group_by(Subjects.name)
        .all()
    )

    # Fetch total quizzes per subject (not just attempted)
    total_quizzes = (
        db.session.query(Subjects.name, db.func.count(Quiz.id))
        .join(Subjects, Subjects.id == Quiz.subject_id)
        .group_by(Subjects.name)
        .all()
    )

    # Convert query results to dictionaries for easier lookup
    subject_attempt_dict = dict(subject_attempts)
    total_quiz_dict = dict(total_quizzes)

    subjects = list(total_quiz_dict.keys())  # Get all subjects
    attempts = [subject_attempt_dict.get(subj, 0) for subj in subjects]  # Attempted quizzes (default 0 if not attempted)
    total = [total_quiz_dict[subj] for subj in subjects]  # Total quizzes

    return render_template('performance_sd.html', subjects=subjects, attempts=attempts, total=total)







@app.route('/summary')
def summary():
    # Get the highest score per subject
    top_scores = db.session.query(
        Subjects.name,
        db.func.max(Score.score)
    ).join(Quiz, Quiz.subject_id == Subjects.id) \
     .join(Score, Score.qz_id == Quiz.id) \
     .group_by(Subjects.name).all()

    # Get the number of quiz attempts per subject
    subject_attempts = db.session.query(
        Subjects.name, db.func.count(Score.userId.distinct())  # Count distinct users who attempted a quiz
    ).join(Quiz, Quiz.subject_id == Subjects.id) \
     .join(Score, Score.qz_id == Quiz.id) \
     .group_by(Subjects.name).all()

    return render_template('summary.html', top_scores=top_scores, subject_attempts=subject_attempts)



@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()

    if not query:
        return render_template('search_results.html', results=[], query=query)

    # Search in different tables
    users = Users.query.filter(Users.fullName.ilike(f"%{query}%")).all()
    subjects = Subjects.query.filter(Subjects.name.ilike(f"%{query}%")).all()
    chapters = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()
    quizzes = Quiz.query.filter(Quiz.remarks.ilike(f"%{query}%")).all()
    questions = Question.query.filter(Question.question_text.ilike(f"%{query}%")).all()

    # Combine results into a dictionary
    results = {
        "Users": users,
        "Subjects": subjects,
        "Chapters": chapters,
        "Quizzes": quizzes,
        "Questions": questions
    }

    return render_template('search_results.html', results=results, query=query)


@app.route('/student/quiz_attempt/<int:quiz_id>', methods=['GET', 'POST'])
def quiz_attempt(quiz_id):
    # Fetch all questions for this quiz
    questions = Question.query.filter_by(qz_id=quiz_id).all()
    quiz = Quiz.query.get(quiz_id) 

    # Handle case where no questions exist
    if not questions:
        return "No questions available for this quiz", 404

    arr_attempt = [{"question": q, "answer": ""} for q in questions]
    total_questions = len(arr_attempt)

    # Initialize session storage
    if 'quiz_answers' not in session:
        session['quiz_answers'] = {}
    quiz_key = str(quiz_id)

    if quiz_key not in session['quiz_answers']:
        session['quiz_answers'][quiz_key] = [""] * total_questions  # Store answers

    if 'current_index' not in session:
        session['current_index'] = 0
    current_index = session.get('current_index', 0)

    # Fetch quiz duration (in minutes) and initialize timer
    quiz = Quiz.query.get(quiz_id)
    time_duration = quiz.time_duration if quiz else 5  # Default to 5 minutes if not set

    if 'quiz_timer' not in session:
        session['quiz_timer'] = time.time() + (time_duration * 60)  # Store end time in seconds
        session.modified = True

    remaining_time = max(0, int(session['quiz_timer'] - time.time()))

    # If time is up, calculate and save the score before redirecting
    if remaining_time == 0:
        session.pop('quiz_timer', None)

        # Calculate the score for attempted questions
        answered_questions = sum(1 for ans in session['quiz_answers'][quiz_key] if ans != "")
        correct_answers_count = sum(int(answer) for answer in session['quiz_answers'][quiz_key] if answer != "")

        if answered_questions > 0:
            score_percentage = (correct_answers_count / answered_questions) * 100
        else:
            score_percentage = 0  # No questions answered

        # Store the score in the database
        user_id = session.get('user_id')
        if user_id:
            existing_score = Score.query.filter_by(userId=user_id, qz_id=quiz_id).first()
            if existing_score:
                existing_score.score = score_percentage
                existing_score.attempted_at = datetime.now()
            else:
                new_score = Score(userId=user_id, qz_id=quiz_id, score=score_percentage)
                db.session.add(new_score)
            db.session.commit()

        return render_template('quiz_timeout.html', score_percentage=score_percentage)

    # If all questions are answered, calculate and record the final score
    if current_index >= total_questions:
        session.pop('current_index', None)  # Reset session index
        session.pop('quiz_timer', None)  # Reset timer
        correct_answers_count = sum(int(answer) for answer in session['quiz_answers'][quiz_key])
        score_percentage = (correct_answers_count / total_questions) * 100

        # Get the logged-in user's ID
        user_id = session.get('user_id')

        if user_id:
            existing_score = Score.query.filter_by(userId=user_id, qz_id=quiz_id).first()
            if existing_score:
                existing_score.score = score_percentage
                existing_score.attempted_at = datetime.now()
            else:
                new_score = Score(userId=user_id, qz_id=quiz_id, score=score_percentage)
                db.session.add(new_score)

            db.session.commit()

        return render_template('quiz_success.html', score_percentage=score_percentage)

    # Handle POST request (saving user's selected answer)
    if request.method == 'POST':
        selected_option = request.form.get("selected_option")
        if selected_option:
            is_answer_correct = 1 if arr_attempt[current_index]['question'].correct_option == selected_option else 0

            session['quiz_answers'][quiz_key][current_index] = is_answer_correct
            session['current_index'] = current_index + 1
            session.modified = True

        return redirect(url_for('quiz_attempt', quiz_id=quiz_id))

    return render_template(
        'quiz_attempt.html',
        arr_attempt=arr_attempt,
        current_index=current_index,
        total_questions=total_questions,
        quiz=quiz,
        remaining_time=remaining_time
    )



@app.route('/student/start_quiz_prev/<int:quiz_id>')
def start_quiz_prev(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    questions = Question.query.filter_by(qz_id=quiz_id).all()
    quiz_questions_numbers = Question.query.filter_by(qz_id=quiz_id).count()
    subject_name = Subjects.query.get(quiz.subject_id).name
    chapter_name = Chapter.query.get(quiz.chapter_id).name
    return render_template('start_quiz_prev.html', quiz = quiz,quiz_questions_numbers=quiz_questions_numbers,questions=questions, subject_name= subject_name, chapter_name = chapter_name)



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
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        questions = Question.query.filter_by(qz_id=quiz_id).all()
        if questions:
            for question in questions:
                db.session.delete(question) 
                Score.query.filter_by(qz_id=quiz.id).delete()

        db.session.delete(quiz)
        db.session.commit()
        return redirect(url_for('chapters_list', subject_id=subject_id))
    else:
        return "Quiz not found", 404


@app.route('/admin/subjects/<int:subject_id>/details/<int:qz_id>/delete_question/<int:ques_id>', methods=['POST'])
def delete_question(subject_id, qz_id, ques_id):
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
        userName = request.form['userName'].strip().lower()  # Normalize email
        password = request.form['password']
        fullName = request.form['fullName']

        # Check if email already exists in the database
        existing_user = Users.query.filter_by(userName=userName).first()
        if existing_user:
            return render_template('register.html', error="User already exists. Please use a different email.")

        # Hash the password before saving
        

        # Create and save the new user
        new_user = Users(userName=userName, passWord=password, fullName=fullName)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login.login'))  # Redirect to login page after successful registration

    return render_template('register.html')

@app.route('/admin/search', methods=['GET'])
def admin_search():
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', '')

    if not search_query:
        return redirect(request.referrer or url_for('admin_dashboard'))  # If empty search, go back

    results = {
        "Users": [],
        "Subjects": [],
        "Quizzes": []
    }

    if category == "users":
        results["Users"] = Users.query.filter(Users.userName.ilike(f"%{search_query}%")).all()
    elif category == "subjects":
        results["Subjects"] = Subjects.query.filter(Subjects.name.ilike(f"%{search_query}%")).all()
    elif category == "quizzes":
        results["Quizzes"] = Quiz.query.filter(Quiz.remarks.ilike(f"%{search_query}%")).all()

    return render_template('search_results.html', results=results, query=search_query)






@app.route('/admin/subject/<int:subject_id>/chapters_list', methods=['GET'])
def chapters_list(subject_id):
    # Fetch the specific subject by ID
    subject = Subjects.query.get(subject_id)
    if not subject:
        return "Subject not found", 404

    # Get search query from the request
    search_query = request.args.get('q', '').strip()

    # Get all chapters related to this subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    quizzes_with_chapters = []

    for chapter in chapters:
        if search_query:
            # Filter quizzes by search term
            quizzes = Quiz.query.filter(Quiz.chapter_id == chapter.id, Quiz.remarks.ilike(f"%{search_query}%")).all()
        else:
            # Otherwise, fetch all quizzes
            quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()

        # Only add the chapter if it has matching quizzes (for search mode)
        if quizzes or not search_query:
            quizzes_with_chapters.append({
                'chapter': chapter,
                'quiz': quizzes
            })

    return render_template('chapters_list.html', arr_quiz=quizzes_with_chapters, subject=subject, search_query=search_query)

@app.route('/admin/users')
def list_users():
    users = Users.query.filter_by(isAdmin=False).all()

    # Count quizzes attempted by each user (from Score table)
    users_data = []
    for user in users:
        quiz_count = Score.query.filter_by(userId=user.userId).count()
        users_data.append({
            'id': user.userId,
            'username': user.userName,
            'fullname': user.fullName,
            'quiz_attempts': quiz_count
        })

    return render_template('users_list.html', users=users_data)

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
        quiz=quiz,
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
        
        quizzes = Quiz.query.filter_by(subject_id=subject_id).all()

        
        for quiz in quizzes:
            Question.query.filter_by(qz_id=quiz.id).delete()
            Score.query.filter_by(qz_id=quiz.id).delete()

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
        return redirect(url_for("admin_dashboard"))

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
                Score.query.filter_by(qz_id=quiz.id).delete()
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
    return redirect(url_for('login.login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
        print("Database initialized!")


        
        admin = Users.query.filter_by(userName='admin').first()
        if not admin:
            
            admin = Users(
                userName='admin',
                passWord='iamadmin',  
                fullName='Quiz Master',
                isAdmin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.debug = True
    app.run()



