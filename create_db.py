from app import db, app  # Import the app and db object from your main app file
from models.models import Users, Subjects, Chapter, Quiz, Question, Score  # Import all models


# Create all tables
with app.app_context():

    db.create_all()
    print("Database created successfully!")