from flask import Flask, render_template, request, redirect, session, flash, Response
import os
import config
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from firebase_admin import db
import cv2
import csv
import face_recognition
import numpy as np
from datetime import datetime
from auth import login_user, register_user, get_user_role

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'registered_faces/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def is_admin():
    return 'role' in session and session['role'] == 'admin'


@app.route('/send-email', methods=['POST'])
def send_email():
    recipient_email = request.form['email']
    student_name = request.form['name']

    subject = "Attendance Alert"
    body = f"Dear Parent,\n\nYour child {student_name} was absent today."

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.EMAIL_CONFIG['sender_email']
    msg['To'] = recipient_email

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(config.EMAIL_CONFIG['smtp_server'], config.EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(config.EMAIL_CONFIG['sender_email'], config.EMAIL_CONFIG['sender_password'])
        server.sendmail(config.EMAIL_CONFIG['sender_email'], recipient_email, msg.as_string())
        server.quit()

        flash(f"Email sent successfully to {student_name} ({recipient_email})!")
    except smtplib.SMTPAuthenticationError:
        flash("Authentication error: Please check your email and password.")
    except smtplib.SMTPException as smtp_error:
        flash(f"Failed to send email: {smtp_error}")
    except Exception as e:
        flash(f"Unexpected error: {e}")
    
    return redirect('/dashboard')
@app.route('/export')
def export_csv():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/')

    today = datetime.now().strftime('%Y-%m-%d')
    attendance_ref = db.reference(f'attendance/{today}')
    attendance_data = attendance_ref.get() or {}

    if not attendance_data:
        flash("No attendance data available for today.")
        return redirect('/dashboard')

    # Generate CSV data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Timestamp'])
    for student_id, record in attendance_data.items():
        writer.writerow([student_id, record['timestamp']])
    
    output.seek(0)

    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=attendance_{today}.csv'}
    )

# Load and encode faces
def load_registered_faces(folder='registered_faces'):
    known_encodings = []
    known_names = []
    for filename in os.listdir(folder):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(folder, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])
    return known_encodings, known_names

known_face_encodings, known_face_names = load_registered_faces()

def mark_attendance(name):
    """Mark attendance for the current day."""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')  # Get today's date
    time_str = now.strftime('%H:%M:%S')  # Get current time

    ref = db.reference(f"attendance/{date_str}/{name}")
    ref.set({
        'name': name,
        'timestamp': time_str
    })
    print(f"Attendance marked for {name} at {time_str}.")


@app.route('/')
def home():
    return redirect('/mark-attendance')
@app.route('/reset-attendance', methods=['POST'])
def reset_attendance():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/dashboard')

    # Clear attendance records for today
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_ref = db.reference(f'attendance/{today}')
    attendance_ref.delete()

    # Reset attendance state
    state_ref = db.reference('attendance_state')
    state_ref.set('stopped')

    flash("Attendance for today has been reset.")
    return redirect('/dashboard')


@app.route('/stop-attendance', methods=['POST'])
def stop_attendance():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/dashboard')

    today = datetime.now().strftime('%Y-%m-%d')
    students_ref = db.reference('students')
    all_students = students_ref.get() or {}
    attendance_ref = db.reference(f'attendance/{today}')
    attendance_data = attendance_ref.get() or {}

    # Identify absentees and send emails
    absentees = [student_id for student_id in all_students if student_id not in attendance_data]
    for student_id in absentees:
        student = all_students[student_id]
        send_email_to_absentee(student['email'], student['name'])

    # Update attendance state to 'stopped'
    state_ref = db.reference('attendance_state')
    state_ref.set('stopped')

    flash("Attendance has been stopped, and emails have been sent to absentees.")
    return redirect('/dashboard')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = config.auth.sign_in_with_email_and_password(email, password)
            session['user'] = user['localId']
            
            # Fetch the user's role from Firebase
            user_ref = db.reference(f'users/{session["user"]}')
            user_info = user_ref.get()
            
            if user_info and user_info['role'] == 'admin':
                session['role'] = 'admin'
                return redirect('/dashboard')
            else:
                flash("You are not authorized to access this area.")
                return redirect('/mark-attendance')

        except Exception as e:
            flash("Invalid credentials. Please try again.")
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/')

    # Fetch all students
    students_ref = db.reference('students')
    all_students = students_ref.get() or {}

    # Fetch today's attendance
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_ref = db.reference(f'attendance/{today}')
    attendance_data = attendance_ref.get() or {}

    # Generate summary
    summary = {}
    if all_students:
        for student_id, student_info in all_students.items():
            summary[student_id] = {
                'name': student_info['name'],
                'status': 'Present' if student_id in attendance_data else 'Absent'
            }


    # Pass summary to the template
    return render_template('dashboard.html', summary=summary)


def send_email_to_absentee(email, name):
    """Helper function to send email to a single absentee."""
    subject = "Attendance Alert"
    body = f"""
    Dear Parent,

    Your child {name} was absent today. Please ensure they attend future classes regularly.

    Best regards,
    Attendance System Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.EMAIL_CONFIG['sender_email']
    msg['To'] = email

    try:
        server = smtplib.SMTP(config.EMAIL_CONFIG['smtp_server'], config.EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(config.EMAIL_CONFIG['sender_email'], config.EMAIL_CONFIG['sender_password'])
        server.sendmail(config.EMAIL_CONFIG['sender_email'], email, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {name} ({email})!")
    except Exception as e:
        print(f"Failed to send email to {name}: {e}")
@app.route('/start-attendance', methods=['POST'])
def start_attendance():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/dashboard')

    state_ref = db.reference('attendance_state')
    state_ref.set('started')  # Update state to 'started'
    flash("Attendance has been started.")
    return redirect('/dashboard')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/')
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        photo = request.files['photo']

        if not student_id or not name or not email or not photo:
            flash("All fields are required.")
            return redirect('/register')

        students_ref = db.reference('students')
        students_ref.child(student_id).set({'name': name, 'email': email})

        filename = f"{student_id}.jpg"
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("Student registered successfully!")
        return redirect('/dashboard')
    return render_template('register.html')
@app.route('/init-attendance-state', methods=['POST'])
def init_attendance_state():
    if not is_admin():
        flash("Access denied! Admins only.")
        return redirect('/dashboard')

    # Create or reset the attendance state
    state_ref = db.reference('attendance_state')
    state_ref.set('stopped')  # Set the default state to 'stopped'
    flash("Attendance state has been initialized to 'stopped'.")
    return redirect('/dashboard')

@app.route('/mark-attendance')
def mark_attendance_page():
    # Check if attendance is started
    state_ref = db.reference('attendance_state')
    state = state_ref.get()
    if state != 'started':
        # Pass an empty summary and the message to the template
        return render_template('mark_attendance.html', message="Wait for admin to start attendance.", summary={})

    # Fetch student list and attendance data
    students_ref = db.reference('students')
    all_students = students_ref.get() or {}

    today = datetime.now().strftime('%Y-%m-%d')
    attendance_ref = db.reference(f'attendance/{today}')
    attendance_data = attendance_ref.get() or {}

    # Generate summary
    summary = {}
    for student_id, student_info in all_students.items():
        summary[student_id] = {
            'name': student_info['name'],
            'status': 'Present' if student_id in attendance_data else 'Absent'
        }

    return render_template('mark_attendance.html', summary=summary)





def generate_frames():
    print("Starting webcam feed...")
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            print("Webcam feed failed.")
            break

        # Optional: Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        # Match faces and annotate
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = known_face_names[match_index]

                # Mark attendance for recognized face
                mark_attendance(name)

                # Draw rectangle and name around face
                top, right, bottom, left = [v * 4 for v in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
