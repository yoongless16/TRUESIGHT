from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import smtplib
from email.mime.text import MIMEText
import uuid
import cv2
import joblib
import numpy as np
from skimage.feature import local_binary_pattern
from functools import wraps
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'avi'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///truesight.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    security_question = db.Column(db.String(255), nullable=False)
    security_answer = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # This column is required
    verification_token = db.Column(db.String(255), unique=True, nullable=True)


class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()
    print("Database tables created.")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your_email_password"  # Replace with your email password

# Helper Functions

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('You need to be logged in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def send_email(email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
            print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_lbp_features(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, P=24, R=3, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 27), range=(0, 26))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)
    return hist

def process_image(file_path):
    return "Fake", 90  

def process_video(file_path):
    return "Real", 95  

# Routes
@app.route('/')
def index():
    logged_in = 'user' in session  # Check if the user is logged in
    username = session.get('user', None)  # Get the username if logged in
    return render_template('index.html', logged_in=logged_in, username=username)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        # Basic validation
        if not all([email, username, password, confirm_password, security_question, security_answer]):
            flash('All fields are required.', 'error')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))

        # Check if the email or username is already registered
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Email or username already exists.', 'error')
            return redirect(url_for('signup'))

        # Hash the password and save the user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            security_question=security_question,
            security_answer=security_answer.lower(),
            is_verified=True  # For now, automatically verify the user
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        # Store the username in session
        session['user'] = user.username
        flash('Login successful!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    if 'user' not in session:
        flash('You must log in to access this page.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['user']).first()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    result, confidence = process_image(file_path)
                elif filename.lower().endswith(('.mp4', '.avi')):
                    result, confidence = process_video(file_path)
                else:
                    flash('Unsupported file type.', 'error')
                    return redirect(request.url)

                new_upload = Upload(user_id=user.id, file_path=filename)
                db.session.add(new_upload)
                db.session.commit()

                return render_template('detect.html', result=result, percentage=confidence)
            except Exception as e:
                print(f"Error during detection: {e}")
                flash('Error processing file.', 'error')
            finally:
                os.remove(file_path)

    return render_template('detect.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not found.', 'error')
            return redirect(url_for('forgot_password'))

        session['reset_email'] = email
        flash('Please answer your security question.', 'info')
        return redirect(url_for('security_question'))

    return render_template('forgot_password.html')

@app.route('/security-question', methods=['GET', 'POST'])
def security_question():
    email = session.get('reset_email')
    if not email:
        flash('Session expired. Please try again.', 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if request.method == 'POST':
        answer = request.form.get('security_answer').lower()
        if user.security_answer != answer:
            flash('Incorrect answer. Please try again.', 'error')
            return redirect(url_for('security_question'))

        flash('Answer verified! You can now reset your password.', 'success')
        return redirect(url_for('reset_password'))

    return render_template('security_question.html', security_question=user.security_question)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = session.get('reset_email')
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password'))

        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        flash('Password reset successful! You can now log in.', 'success')
        session.pop('reset_email', None)
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/profile')
@login_required
def profile():
    username = session.get('user')
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    uploads = Upload.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', username=user.username, email=user.email, uploads=uploads)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('uploaded_file', filename=filename))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        flash('File not found.', 'error')
        return redirect(url_for('profile'))

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
