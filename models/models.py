from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()



class Users(db.Model):
    __tablename__ = "users"
    userId = db.Column(db.Integer,  primary_key= True)
    userName = db.Column(db.String(120), unique = True, nullable = False)
    passWord = db.Column(db.String(120), nullable = False)
    fullName = db.Column(db.String(120), nullable = False)
    isAdmin = db.Column(db.Boolean, default = False)


class Subjects(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)



class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }
    

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.Text, nullable=True)

class Question(db.Model):
    __tablename__ = 'questions'
    ques_id = db.Column(db.Integer, primary_key=True)
    qz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(100), nullable=False)

class Score(db.Model):
    __tablename__ = 'scores'
    sc_id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    qz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)



