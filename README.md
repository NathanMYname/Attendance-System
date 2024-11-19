# Attendance System Documentation

## 1. Overview
The Attendance System is a web application for managing student attendance using facial recognition. It includes:
- Admin functionalities to **start**, **stop**, and **reset** attendance.
- A mark attendance feature for students using a webcam.
- Automated email notifications to absentees.
- Secure authentication for admin access.

---

## 2. Features
- **Admin Dashboard**:
  - Start, Stop, and Reset attendance for the day.
  - View absentees for the current day.
  - Export attendance data as CSV.
- **Mark Attendance**:
  - Students use facial recognition to mark their attendance.
  - Real-time attendance tracking.
- **Email Notifications**:
  - Automatically sends email notifications to absentees when attendance is stopped.

---

## 3. Prerequisites

### Tools and Software
- Python 3.10 or later
- Flask framework
- Firebase Realtime Database
- Webcam (for face recognition)
- Email account (e.g., Gmail, Yahoo) with **App Passwords** enabled.

---

## 4. Setup Instructions

### 4.1 Clone the Repository
```bash
git clone <your-repo-url>
cd attendance-system
```

### 4.2 Install Required Packages
Install the dependencies listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

### 4.3 Firebase Setup

#### Step 1: Create a Firebase Project
1. Go to the Firebase Console at [https://console.firebase.google.com/](https://console.firebase.google.com/).
2. Click **Add Project** and follow the steps.

#### Step 2: Enable Realtime Database
1. Navigate to **Build > Realtime Database**.
2. Click **Create Database** and select your location.
3. Set rules for testing:
   ```json
   {
     "rules": {
       ".read": true,
       ".write": true
     }
   }
   ```
4. **Important**: Update these rules for production to restrict access:
   ```json
   {
     "rules": {
       ".read": "auth != null",
       ".write": "auth != null"
     }
   }
   ```

#### Step 3: Get Firebase Service Account Key
1. Navigate to **Project Settings > Service Accounts**.
2. Click **Generate New Private Key** and download the JSON file.
3. Save the file as `serviceAccountKey.json` in your project root.

#### Step 4: Get Firebase Config Data
1. Navigate to **Project Settings > General > Your Apps**.
2. Copy the **apiKey**, **authDomain**, and **databaseURL** values.
3. Update `config.py` with these values:
   ```python
   FIREBASE_CONFIG = {
       "apiKey": "<your-api-key>",
       "authDomain": "<your-auth-domain>",
       "databaseURL": "<your-database-url>",
       "storageBucket": "<your-storage-bucket>"
   }
   ```

---

### 4.4 Email Setup

#### Step 1: Gmail or Yahoo Setup
1. Enable **2-Step Verification** for your email account.
2. Generate an **App Password**:
   - For Gmail: Follow [this guide](https://support.google.com/accounts/answer/185833?hl=en).
   - For Yahoo: Follow [this guide](https://help.yahoo.com/kb/generate-manage-third-party-passwords-sln15241.html).
3. Use the App Password as your email password.

#### Step 2: Update Email Config
1. Update the email details in `config.py`:
   ```python
   EMAIL_CONFIG = {
       "sender_email": "your_email@example.com",
       "sender_password": "your_app_password",
       "smtp_server": "smtp.gmail.com",  # Use "smtp.mail.yahoo.com" for Yahoo
       "smtp_port": 587
   }
   ```

---

### 4.5 Run the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://127.0.0.1:5000`.

---

## 5. Usage Instructions

### 5.1 Admin Login
1. Visit the Admin Login page at `/admin-login`.
2. Enter your admin credentials.
3. Access the dashboard.

### 5.2 Admin Dashboard
- **Start Attendance**: Enables students to mark attendance.
- **Stop Attendance**: Ends attendance for the day and triggers email notifications to absentees.
- **Reset Attendance**: Clears attendance data for the current day.

### 5.3 Mark Attendance
1. Students visit `/mark-attendance`.
2. The system uses facial recognition to identify students and mark attendance.

### 5.4 Export Attendance
Admins can export attendance data as a CSV file for record-keeping.

---

## 6. File Structure
```
attendance-system/
├── registered_faces/      # Folder for student face images
├── static/                # Static assets (CSS, JS)
│   └── style.css          # Custom styles
├── templates/             # HTML templates
│   ├── dashboard.html     # Admin dashboard
│   ├── login.html         # Admin login page
│   ├── mark_attendance.html # Mark attendance page
│   ├── register.html      # Register new students
├── app.py                 # Main Flask application
├── auth.py                # Handles authentication
├── config.py              # Configuration (Firebase, email, secret key)
├── requirements.txt       # Python dependencies
├── serviceAccountKey.json # Firebase service account key
```

---

## 7. Deployment Instructions

### 7.1 Environment Variables
Store sensitive data like Firebase credentials and SMTP passwords:
- Use `.env` files with libraries like `python-dotenv`.
- Example `.env` file:
  ```
  FIREBASE_API_KEY=<your-api-key>
  FIREBASE_AUTH_DOMAIN=<your-auth-domain>
  FIREBASE_DATABASE_URL=<your-database-url>
  EMAIL_USER=<your-email>
  EMAIL_PASSWORD=<your-app-password>
  ```
  
---

## 8. Troubleshooting

### Common Issues
- **Email Sending Issues**:
  Check SMTP credentials and verify App Passwords are set up correctly.
- **Face Recognition Errors**:
  Ensure student images are clear and properly encoded.

### Debugging
- Use Flask's built-in debugger (`debug=True` in `app.py`).
- Log errors and variables to the console using `print()`.

---

## 9. Future Enhancements
- **Mobile-Friendly UI**: Improve responsiveness for better usability on phones.
- **Multi-Role Support**: Add roles for teachers, students, and admins.
- **Attendance Reports**: Generate monthly or weekly attendance summaries.
- **Daily Automated Reset**: Use a scheduler like Cron to reset attendance daily.

