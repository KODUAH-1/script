import streamlit as st
import sqlite3
import hashlib
import os
import shutil
import io
import json
import zipfile
from datetime import datetime, date
import pandas as pd
import plotly.express as px

# ============================================================
# 21ST GLOBAL COMMUNITY SCHOOL
# COMPLETE SCHOOL PORTAL + LMS
# ============================================================

st.set_page_config(
    page_title=" Global Community School",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "school.db"
ASSET_DIR = "school_assets"
BACKUP_DIR = "backups"

os.makedirs(ASSET_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def execute(query, params=(), fetch=False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)

    if fetch:
        rows = cur.fetchall()
        conn.close()
        return rows

    conn.commit()
    conn.close()
    return None


def df_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def init_database():

    conn = get_connection()
    cur = conn.cursor()

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            linked_student_id TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # STUDENTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT,
            date_of_birth TEXT,
            class_name TEXT,
            parent_name TEXT,
            parent_phone TEXT,
            email TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # TEACHERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            gender TEXT,
            phone TEXT,
            email TEXT,
            subject TEXT,
            qualification TEXT,
            photo TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # CLASSES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT UNIQUE NOT NULL,
            class_teacher TEXT,
            room TEXT,
            academic_year TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SUBJECTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            subject_name TEXT NOT NULL,
            teacher TEXT,
            class_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ATTENDANCE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            class_name TEXT,
            attendance_date TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # RESULTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            class_name TEXT,
            subject TEXT,
            score REAL,
            grade TEXT,
            term TEXT,
            academic_year TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FEES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            fee_type TEXT,
            amount_due REAL,
            amount_paid REAL DEFAULT 0,
            balance REAL,
            payment_date TEXT,
            receipt_number TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # COURSES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            teacher TEXT,
            class_name TEXT,
            description TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # LESSONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            lesson_title TEXT NOT NULL,
            content TEXT,
            lesson_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ASSIGNMENTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT,
            title TEXT,
            description TEXT,
            due_date TEXT,
            total_marks REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # QUIZZES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT,
            quiz_title TEXT,
            total_questions INTEGER,
            duration INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ANNOUNCEMENTS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            message TEXT,
            audience TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # MESSAGES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # NOTIFICATIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT,
            title TEXT,
            message TEXT,
            notification_type TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # EXAMINATIONS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT,
            subject TEXT,
            class_name TEXT,
            exam_date TEXT,
            start_time TEXT,
            duration INTEGER,
            venue TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # TIMETABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            day TEXT,
            start_time TEXT,
            end_time TEXT,
            subject TEXT,
            teacher TEXT,
            room TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # CERTIFICATES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            certificate_type TEXT,
            description TEXT,
            issue_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SCHOOL SETTINGS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            school_name TEXT,
            academic_year TEXT,
            head_teacher TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            logo TEXT
        )
    """)

    # DEFAULT SETTINGS
    cur.execute("SELECT id FROM settings WHERE id=1")

    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO settings
            (id, school_name, academic_year, head_teacher, phone, email, address, logo)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "21st Global Community School",
            "2026/2027",
            "",
            "",
            "",
            "",
            ""
        ))

    # DEFAULT ADMIN
    cur.execute(
        "SELECT id FROM users WHERE username=?",
        ("admin",)
    )

    if cur.fetchone() is None:
        cur.execute("""
            INSERT INTO users
            (username,password,full_name,role,email,status)
            VALUES (?,?,?,?,?,?)
        """, (
            "admin",
            hash_password("admin123"),
            "System Administrator",
            "Administrator",
            "admin@21stglobal.edu",
            "Active"
        ))

    conn.commit()
    conn.close()


# ============================================================
# HELPERS
# ============================================================

def get_settings():
    rows = execute(
        "SELECT * FROM settings WHERE id=1",
        fetch=True
    )

    if rows:
        return dict(rows[0])

    return {
        "school_name": "21st Global Community School",
        "academic_year": "2026/2027",
        "logo": ""
    }


def school_name():
    return get_settings()["school_name"]


def logo_path():
    return get_settings().get("logo", "")


def calculate_grade(score):

    if score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    elif score >= 40:
        return "E"
    return "F"


def grade_remark(grade):

    remarks = {
        "A": "Excellent",
        "B": "Very Good",
        "C": "Good",
        "D": "Credit",
        "E": "Pass",
        "F": "Needs Improvement"
    }

    return remarks.get(grade, "")


def save_uploaded_file(uploaded_file, folder):

    if uploaded_file is None:
        return ""

    os.makedirs(folder, exist_ok=True)

    filename = uploaded_file.name.replace(" ", "_")
    path = os.path.join(folder, filename)

    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return path


# ============================================================
# CSS
# ============================================================

def load_css():

    st.markdown("""
    <style>

    .main {
        background-color: #f5f7fb;
    }

    .school-header {
        padding: 25px;
        border-radius: 18px;
        color: white;
        background: linear-gradient(
            135deg,
            #0d47a1,
            #1976d2,
            #42a5f5
        );
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }

    .welcome-title {
        font-size: 30px;
        font-weight: 800;
    }

    .welcome-subtitle {
        font-size: 16px;
        opacity: .9;
        margin-top: 8px;
    }

    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        box-shadow: 0 5px 20px rgba(0,0,0,.08);
        border-left: 5px solid #1976d2;
        min-height: 140px;
    }

    .metric-icon {
        font-size: 30px;
    }

    .metric-title {
        color: #666;
        font-size: 15px;
        margin-top: 8px;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #0d47a1;
    }

    .section-card {
        background: white;
        padding: 22px;
        border-radius: 18px;
        box-shadow: 0 5px 20px rgba(0,0,0,.07);
        margin-bottom: 20px;
    }

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# LOGIN
# ============================================================

def login_page():

    settings = get_settings()

    st.markdown("""
    <div class="school-header" style="text-align:center;">
        <div style="font-size:55px;">🎓</div>
        <div class="welcome-title">
            21st Global Community School
        </div>
        <div class="welcome-subtitle">
            School Portal & Learning Management System
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:

        st.markdown("### 🔐 Secure Login")

        with st.form("login_form"):

            username = st.text_input(
                "Username",
                autocomplete="username"
            )

            password = st.text_input(
                "Password",
                type="password",
                autocomplete="current-password"
            )

            submitted = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True
            )

            if submitted:

                user = execute("""
                    SELECT * FROM users
                    WHERE username=?
                    AND password=?
                    AND status='Active'
                """, (
                    username.strip(),
                    hash_password(password)
                ), fetch=True)

                if user:

                    st.session_state.logged_in = True
                    st.session_state.user = dict(user[0])

                    st.rerun()

                else:

                    st.error(
                        "Invalid username, password or inactive account."
                    )

        st.caption(
            "Administrator account:"
        )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    user = st.session_state.user
    settings = get_settings()

    st.markdown(f"""
    <div class="school-header">
        <div class="welcome-title">
            👋 Welcome, {user['full_name']}
        </div>
        <div class="welcome-subtitle">
            {settings['school_name']} |
            {settings['academic_year']} |
            Role: {user['role']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    students = execute(
        "SELECT COUNT(*) total FROM students",
        fetch=True
    )[0]["total"]

    teachers = execute(
        "SELECT COUNT(*) total FROM teachers",
        fetch=True
    )[0]["total"]

    classes = execute(
        "SELECT COUNT(*) total FROM classes",
        fetch=True
    )[0]["total"]

    courses = execute(
        "SELECT COUNT(*) total FROM courses",
        fetch=True
    )[0]["total"]

    fees = df_query("SELECT * FROM fees")
    results = df_query("SELECT * FROM results")
    attendance = df_query("SELECT * FROM attendance")

    collected = (
        fees["amount_paid"].sum()
        if not fees.empty else 0
    )

    outstanding = (
        fees["balance"].sum()
        if not fees.empty else 0
    )

    cols = st.columns(6)

    metrics = [
        ("👨‍🎓", "Students", students),
        ("👩‍🏫", "Teachers", teachers),
        ("🏫", "Classes", classes),
        ("🎓", "LMS Courses", courses),
        ("💰", "Fees Collected", f"GHS {collected:,.2f}"),
        ("⚠️", "Outstanding", f"GHS {outstanding:,.2f}")
    ]

    for col, item in zip(cols, metrics):

        icon, title, value = item

        with col:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">{icon}</div>
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("👨‍🎓 Student Demographics")

        gender = df_query("""
            SELECT gender, COUNT(*) count
            FROM students
            GROUP BY gender
        """)

        if not gender.empty:

            fig = px.pie(
                gender,
                names="gender",
                values="count",
                hole=.45,
                title="Students by Gender"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info("No student data yet.")

    with col2:

        st.subheader("📊 Academic Performance")

        if not results.empty:

            performance = (
                results
                .groupby("subject")["score"]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                performance,
                x="subject",
                y="score",
                title="Average Score by Subject",
                text_auto=".1f"
            )

            fig.update_yaxes(range=[0, 100])

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info("No academic results yet.")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🕐 Attendance")

        if not attendance.empty:

            att = (
                attendance["status"]
                .value_counts()
                .reset_index()
            )

            att.columns = ["Status", "Count"]

            fig = px.pie(
                att,
                names="Status",
                values="Count",
                hole=.45
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info("No attendance records.")

    with col2:

        st.subheader("💰 Fees")

        if not fees.empty:

            fee_data = pd.DataFrame({
                "Category": [
                    "Due",
                    "Paid",
                    "Balance"
                ],
                "Amount": [
                    fees["amount_due"].sum(),
                    fees["amount_paid"].sum(),
                    fees["balance"].sum()
                ]
            })

            fig = px.bar(
                fee_data,
                x="Category",
                y="Amount",
                text_auto=".2f"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:

            st.info("No fee records.")

    st.subheader("📢 Recent Announcements")

    announcements = execute("""
        SELECT * FROM announcements
        ORDER BY id DESC
        LIMIT 5
    """, fetch=True)

    if announcements:

        for a in announcements:

            st.info(
                f"**{a['title']}**\n\n{a['message']}"
            )

    else:

        st.info("No announcements.")


# ============================================================
# STUDENTS
# ============================================================

def students_page():

    st.title("👨‍🎓 Student Management")

    tab1, tab2 = st.tabs([
        "➕ Add Student",
        "📋 Records"
    ])

    with tab1:

        with st.form("student_add_form"):

            c1, c2 = st.columns(2)

            with c1:

                student_id = st.text_input("Student ID")
                full_name = st.text_input("Full Name")

                gender = st.selectbox(
                    "Gender",
                    ["Male", "Female"]
                )

                dob = st.date_input(
                    "Date of Birth",
                    value=date(2015, 1, 1)
                )

                class_name = st.text_input("Class")

            with c2:

                parent_name = st.text_input(
                    "Parent/Guardian Name"
                )

                parent_phone = st.text_input(
                    "Parent Phone"
                )

                email = st.text_input("Email")

                status = st.selectbox(
                    "Status",
                    ["Active", "Inactive"]
                )

                photo = st.file_uploader(
                    "Student Photograph",
                    type=["jpg", "jpeg", "png"]
                )

            submitted = st.form_submit_button(
                "Add Student",
                type="primary"
            )

            if submitted:

                if not student_id or not full_name:

                    st.error(
                        "Student ID and Full Name are required."
                    )

                else:

                    try:

                        photo_path = save_uploaded_file(
                            photo,
                            os.path.join(
                                ASSET_DIR,
                                "students"
                            )
                        )

                        execute("""
                            INSERT INTO students
                            (
                                student_id,
                                full_name,
                                gender,
                                date_of_birth,
                                class_name,
                                parent_name,
                                parent_phone,
                                email,
                                photo,
                                status
                            )
                            VALUES (?,?,?,?,?,?,?,?,?,?)
                        """, (
                            student_id,
                            full_name,
                            gender,
                            str(dob),
                            class_name,
                            parent_name,
                            parent_phone,
                            email,
                            photo_path,
                            status
                        ))

                        st.success(
                            "Student added successfully."
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "Student ID already exists."
                        )

    with tab2:

        df = df_query(
            "SELECT * FROM students ORDER BY id DESC"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        if not df.empty:

            st.download_button(
                "📥 Download Students CSV",
                df.to_csv(index=False),
                "students.csv",
                "text/csv",
                key="download_students_csv"
            )


# ============================================================
# TEACHERS
# ============================================================

def teachers_page():

    st.title("👩‍🏫 Teacher Management")

    tab1, tab2 = st.tabs([
        "➕ Add Teacher",
        "📋 Teacher Records"
    ])

    with tab1:

        with st.form("teacher_add_form"):

            c1, c2 = st.columns(2)

            with c1:

                teacher_id = st.text_input("Teacher ID")
                full_name = st.text_input("Full Name")

                gender = st.selectbox(
                    "Gender",
                    ["Male", "Female"]
                )

                phone = st.text_input("Phone")

            with c2:

                email = st.text_input("Email")
                subject = st.text_input("Main Subject")
                qualification = st.text_input(
                    "Qualification"
                )

                photo = st.file_uploader(
                    "Teacher Photograph",
                    type=["jpg", "jpeg", "png"]
                )

                status = st.selectbox(
                    "Status",
                    ["Active", "Inactive"]
                )

            submitted = st.form_submit_button(
                "Add Teacher",
                type="primary"
            )

            if submitted:

                try:

                    photo_path = save_uploaded_file(
                        photo,
                        os.path.join(
                            ASSET_DIR,
                            "teachers"
                        )
                    )

                    execute("""
                        INSERT INTO teachers
                        (
                            teacher_id,
                            full_name,
                            gender,
                            phone,
                            email,
                            subject,
                            qualification,
                            photo,
                            status
                        )
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (
                        teacher_id,
                        full_name,
                        gender,
                        phone,
                        email,
                        subject,
                        qualification,
                        photo_path,
                        status
                    ))

                    st.success(
                        "Teacher added successfully."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "Teacher ID already exists."
                    )

    with tab2:

        df = df_query(
            "SELECT * FROM teachers ORDER BY id DESC"
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLASSES
# ============================================================

def classes_page():

    st.title("🏫 Classes")

    with st.form("class_form"):

        c1, c2 = st.columns(2)

        with c1:

            class_name = st.text_input("Class Name")
            class_teacher = st.text_input(
                "Class Teacher"
            )

        with c2:

            room = st.text_input("Room")
            academic_year = st.text_input(
                "Academic Year",
                value="2026/2027"
            )

        submitted = st.form_submit_button(
            "Add Class",
            type="primary"
        )

        if submitted:

            try:

                execute("""
                    INSERT INTO classes
                    (
                        class_name,
                        class_teacher,
                        room,
                        academic_year
                    )
                    VALUES (?,?,?,?)
                """, (
                    class_name,
                    class_teacher,
                    room,
                    academic_year
                ))

                st.success("Class added.")

            except sqlite3.IntegrityError:

                st.error("Class already exists.")

    st.dataframe(
        df_query("SELECT * FROM classes"),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# SUBJECTS
# ============================================================

def subjects_page():

    st.title("📚 Subjects")

    with st.form("subject_form"):

        c1, c2 = st.columns(2)

        with c1:

            code = st.text_input("Subject Code")
            name = st.text_input("Subject Name")

        with c2:

            teacher = st.text_input("Teacher")
            class_name = st.text_input("Class")

        submitted = st.form_submit_button(
            "Add Subject",
            type="primary"
        )

        if submitted:

            try:

                execute("""
                    INSERT INTO subjects
                    (
                        subject_code,
                        subject_name,
                        teacher,
                        class_name
                    )
                    VALUES (?,?,?,?)
                """, (
                    code,
                    name,
                    teacher,
                    class_name
                ))

                st.success("Subject added.")

            except sqlite3.IntegrityError:

                st.error(
                    "Subject code already exists."
                )

    st.dataframe(
        df_query("SELECT * FROM subjects"),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ATTENDANCE
# ============================================================

def attendance_page():

    st.title("🕐 Attendance")

    students = df_query("""
        SELECT student_id, full_name, class_name
        FROM students
        WHERE status='Active'
    """)

    if students.empty:

        st.warning("Add students first.")
        return

    student_id = st.selectbox(
        "Student",
        students["student_id"].tolist(),
        key="attendance_student"
    )

    student = students[
        students["student_id"] == student_id
    ].iloc[0]

    attendance_date = st.date_input(
        "Date",
        date.today(),
        key="attendance_date"
    )

    status = st.selectbox(
        "Status",
        ["Present", "Absent", "Late", "Excused"],
        key="attendance_status"
    )

    if st.button(
        "Save Attendance",
        type="primary",
        key="save_attendance"
    ):

        execute("""
            INSERT INTO attendance
            (
                student_id,
                student_name,
                class_name,
                attendance_date,
                status
            )
            VALUES (?,?,?,?,?)
        """, (
            student["student_id"],
            student["full_name"],
            student["class_name"],
            str(attendance_date),
            status
        ))

        st.success("Attendance saved.")

    st.dataframe(
        df_query(
            "SELECT * FROM attendance ORDER BY id DESC"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# RESULTS
# ============================================================

def results_page():

    st.title("📝 Academic Results / Gradebook")

    students = df_query("""
        SELECT student_id, full_name, class_name
        FROM students
        WHERE status='Active'
    """)

    if students.empty:

        st.warning("Add students first.")
        return

    student_id = st.selectbox(
        "Student",
        students["student_id"].tolist(),
        key="result_student"
    )

    student = students[
        students["student_id"] == student_id
    ].iloc[0]

    subject = st.text_input(
        "Subject",
        key="result_subject"
    )

    score = st.number_input(
        "Score",
        min_value=0.0,
        max_value=100.0,
        step=0.5,
        key="result_score"
    )

    term = st.selectbox(
        "Term",
        [
            "First Term",
            "Second Term",
            "Third Term"
        ],
        key="result_term"
    )

    academic_year = st.text_input(
        "Academic Year",
        "2026/2027",
        key="result_year"
    )

    if st.button(
        "Save Result",
        type="primary",
        key="save_result"
    ):

        grade = calculate_grade(score)

        execute("""
            INSERT INTO results
            (
                student_id,
                student_name,
                class_name,
                subject,
                score,
                grade,
                term,
                academic_year,
                remarks
            )
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            student["student_id"],
            student["full_name"],
            student["class_name"],
            subject,
            score,
            grade,
            term,
            academic_year,
            grade_remark(grade)
        ))

        st.success(
            f"Result saved. Grade: {grade}"
        )

    st.dataframe(
        df_query(
            "SELECT * FROM results ORDER BY id DESC"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# REPORT CARDS
# ============================================================

def report_cards_page():

    st.title("📄 Report Cards")

    students = df_query("""
        SELECT student_id, full_name, class_name
        FROM students
        ORDER BY full_name
    """)

    if students.empty:

        st.info("Add students and results first.")
        return

    student_id = st.selectbox(
        "Select Student",
        students["student_id"].tolist(),
        key="report_student"
    )

    student = students[
        students["student_id"] == student_id
    ].iloc[0]

    term = st.selectbox(
        "Term",
        [
            "First Term",
            "Second Term",
            "Third Term"
        ],
        key="report_term"
    )

    year = st.text_input(
        "Academic Year",
        "2026/2027",
        key="report_year"
    )

    results = df_query("""
        SELECT subject, score, grade, remarks
        FROM results
        WHERE student_id=?
        AND term=?
        AND academic_year=?
    """, (
        student_id,
        term,
        year
    ))

    if results.empty:

        st.warning(
            "No results found for this student."
        )

        return

    st.markdown(f"""
    <div class="school-header">
        <h2>{school_name()}</h2>
        <p>STUDENT ACADEMIC REPORT</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    c1.write(f"**Student:** {student['full_name']}")
    c2.write(f"**Student ID:** {student_id}")
    c3.write(f"**Class:** {student['class_name']}")

    st.write(f"**Term:** {term}")
    st.write(f"**Academic Year:** {year}")

    st.dataframe(
        results,
        use_container_width=True,
        hide_index=True
    )

    average = results["score"].mean()

    st.metric(
        "Average Score",
        f"{average:.2f}%"
    )

    csv = results.to_csv(index=False)

    st.download_button(
        "📥 Download Report Card",
        csv,
        f"report_card_{student_id}.csv",
        "text/csv",
        key="download_report_card"
    )


# ============================================================
# FEES
# ============================================================

def fees_page():

    st.title("💰 Fees Management")

    students = df_query("""
        SELECT student_id, full_name
        FROM students
        WHERE status='Active'
    """)

    if students.empty:

        st.warning("Add students first.")
        return

    student_id = st.selectbox(
        "Student",
        students["student_id"].tolist(),
        key="fee_student"
    )

    student = students[
        students["student_id"] == student_id
    ].iloc[0]

    fee_type = st.selectbox(
        "Fee Type",
        [
            "School Fees",
            "Tuition",
            "Books",
            "ICT",
            "Examination",
            "Transportation",
            "Other"
        ],
        key="fee_type"
    )

    amount_due = st.number_input(
        "Amount Due (GHS)",
        min_value=0.0,
        key="amount_due"
    )

    amount_paid = st.number_input(
        "Amount Paid (GHS)",
        min_value=0.0,
        key="amount_paid"
    )

    payment_date = st.date_input(
        "Payment Date",
        date.today(),
        key="payment_date"
    )

    receipt_number = st.text_input(
        "Receipt Number",
        key="receipt_number"
    )

    balance = amount_due - amount_paid

    if balance <= 0:
        status = "Paid"
    elif amount_paid > 0:
        status = "Partially Paid"
    else:
        status = "Outstanding"

    st.metric(
        "Balance",
        f"GHS {balance:,.2f}"
    )

    if st.button(
        "💾 Save Fee",
        type="primary",
        key="save_fee"
    ):

        execute("""
            INSERT INTO fees
            (
                student_id,
                student_name,
                fee_type,
                amount_due,
                amount_paid,
                balance,
                payment_date,
                receipt_number,
                status
            )
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            student["student_id"],
            student["full_name"],
            fee_type,
            amount_due,
            amount_paid,
            balance,
            str(payment_date),
            receipt_number,
            status
        ))

        st.success("Fee record saved.")

    st.dataframe(
        df_query(
            "SELECT * FROM fees ORDER BY id DESC"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FEE RECEIPTS
# ============================================================

def fee_receipts_page():

    st.title("🧾 Fee Receipts")

    receipts = df_query("""
        SELECT *
        FROM fees
        ORDER BY id DESC
    """)

    if receipts.empty:

        st.info("No fee receipts available.")
        return

    receipt = st.selectbox(
        "Receipt Number",
        receipts["receipt_number"].fillna("").tolist(),
        key="receipt_select"
    )

    row = receipts[
        receipts["receipt_number"].fillna("") == receipt
    ]

    if not row.empty:

        r = row.iloc[0]

        st.markdown(f"""
        <div class="school-header">
            <h2>{school_name()}</h2>
            <h3>OFFICIAL FEE RECEIPT</h3>
        </div>
        """, unsafe_allow_html=True)

        st.write(f"**Receipt No.:** {r['receipt_number']}")
        st.write(f"**Student:** {r['student_name']}")
        st.write(f"**Student ID:** {r['student_id']}")
        st.write(f"**Fee Type:** {r['fee_type']}")
        st.write(f"**Amount Due:** GHS {r['amount_due']:,.2f}")
        st.write(f"**Amount Paid:** GHS {r['amount_paid']:,.2f}")
        st.write(f"**Balance:** GHS {r['balance']:,.2f}")
        st.write(f"**Status:** {r['status']}")
        st.write(f"**Payment Date:** {r['payment_date']}")

        st.download_button(
            "📥 Download Receipt",
            row.to_csv(index=False),
            f"receipt_{receipt}.csv",
            "text/csv",
            key="download_receipt"
        )


# ============================================================
# FEE STATEMENTS
# ============================================================

def fee_statements_page():

    st.title("📑 Fee Statements")

    students = df_query("""
        SELECT student_id, full_name
        FROM students
        ORDER BY full_name
    """)

    if students.empty:
        st.info("No students available.")
        return

    student_id = st.selectbox(
        "Student",
        students["student_id"].tolist(),
        key="statement_student"
    )

    statement = df_query("""
        SELECT
            fee_type,
            amount_due,
            amount_paid,
            balance,
            payment_date,
            receipt_number,
            status
        FROM fees
        WHERE student_id=?
        ORDER BY id
    """, (student_id,))

    st.dataframe(
        statement,
        use_container_width=True,
        hide_index=True
    )

    if not statement.empty:

        total_due = statement["amount_due"].sum()
        total_paid = statement["amount_paid"].sum()
        total_balance = statement["balance"].sum()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Due",
            f"GHS {total_due:,.2f}"
        )

        c2.metric(
            "Total Paid",
            f"GHS {total_paid:,.2f}"
        )

        c3.metric(
            "Balance",
            f"GHS {total_balance:,.2f}"
        )

        st.download_button(
            "📥 Download Fee Statement",
            statement.to_csv(index=False),
            f"fee_statement_{student_id}.csv",
            "text/csv",
            key="download_fee_statement"
        )


# ============================================================
# LMS
# ============================================================

def lms_page():

    st.title("🎓 Learning Management System")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Courses",
        "Lessons",
        "Assignments",
        "Quizzes"
    ])

    with tab1:

        with st.form("course_form"):

            code = st.text_input("Course Code")
            name = st.text_input("Course Name")
            teacher = st.text_input("Teacher")
            class_name = st.text_input("Class")
            description = st.text_area(
                "Description"
            )

            submitted = st.form_submit_button(
                "Create Course",
                type="primary"
            )

            if submitted:

                try:

                    execute("""
                        INSERT INTO courses
                        (
                            course_code,
                            course_name,
                            teacher,
                            class_name,
                            description
                        )
                        VALUES (?,?,?,?,?)
                    """, (
                        code,
                        name,
                        teacher,
                        class_name,
                        description
                    ))

                    st.success("Course created.")

                except sqlite3.IntegrityError:

                    st.error(
                        "Course code already exists."
                    )

        st.dataframe(
            df_query("SELECT * FROM courses"),
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        courses = df_query(
            "SELECT id, course_name FROM courses"
        )

        if courses.empty:

            st.info("Create a course first.")

        else:

            course_id = st.selectbox(
                "Course",
                courses["id"].tolist(),
                format_func=lambda x:
                    courses.loc[
                        courses["id"] == x,
                        "course_name"
                    ].iloc[0],
                key="lesson_course"
            )

            title = st.text_input(
                "Lesson Title",
                key="lesson_title"
            )

            content = st.text_area(
                "Lesson Content",
                height=200,
                key="lesson_content"
            )

            lesson_date = st.date_input(
                "Lesson Date",
                key="lesson_date"
            )

            if st.button(
                "Add Lesson",
                type="primary",
                key="add_lesson"
            ):

                execute("""
                    INSERT INTO lessons
                    (
                        course_id,
                        lesson_title,
                        content,
                        lesson_date
                    )
                    VALUES (?,?,?,?)
                """, (
                    course_id,
                    title,
                    content,
                    str(lesson_date)
                ))

                st.success("Lesson added.")

    with tab3:

        course_name = st.text_input(
            "Course Name",
            key="assignment_course"
        )

        title = st.text_input(
            "Assignment Title",
            key="assignment_title"
        )

        description = st.text_area(
            "Instructions",
            key="assignment_description"
        )

        due_date = st.date_input(
            "Due Date",
            key="assignment_due"
        )

        total_marks = st.number_input(
            "Total Marks",
            min_value=1.0,
            key="assignment_marks"
        )

        if st.button(
            "Create Assignment",
            type="primary",
            key="create_assignment"
        ):

            execute("""
                INSERT INTO assignments
                (
                    course_name,
                    title,
                    description,
                    due_date,
                    total_marks
                )
                VALUES (?,?,?,?,?)
            """, (
                course_name,
                title,
                description,
                str(due_date),
                total_marks
            ))

            st.success("Assignment created.")

        st.dataframe(
            df_query("SELECT * FROM assignments"),
            use_container_width=True,
            hide_index=True
        )

    with tab4:

        course_name = st.text_input(
            "Course Name",
            key="quiz_course"
        )

        quiz_title = st.text_input(
            "Quiz Title",
            key="quiz_title"
        )

        total_questions = st.number_input(
            "Questions",
            min_value=1,
            step=1,
            key="quiz_questions"
        )

        duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            step=1,
            key="quiz_duration"
        )

        if st.button(
            "Create Quiz",
            type="primary",
            key="create_quiz"
        ):

            execute("""
                INSERT INTO quizzes
                (
                    course_name,
                    quiz_title,
                    total_questions,
                    duration
                )
                VALUES (?,?,?,?)
            """, (
                course_name,
                quiz_title,
                total_questions,
                duration
            ))

            st.success("Quiz created.")


# ============================================================
# ANALYTICS
# ============================================================

def analytics_page():

    st.title("📈 Real-Time School Analytics")

    students = df_query("SELECT * FROM students")
    results = df_query("SELECT * FROM results")
    attendance = df_query("SELECT * FROM attendance")
    fees = df_query("SELECT * FROM fees")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Students", len(students))
    c2.metric("Results", len(results))
    c3.metric("Attendance Records", len(attendance))

    collected = (
        fees["amount_paid"].sum()
        if not fees.empty else 0
    )

    c4.metric(
        "Collected",
        f"GHS {collected:,.2f}"
    )

    if not results.empty:

        st.subheader("📊 Performance by Subject")

        performance = (
            results
            .groupby("subject")["score"]
            .agg(["mean", "count"])
            .reset_index()
        )

        fig = px.bar(
            performance,
            x="subject",
            y="mean",
            text_auto=".1f"
        )

        fig.update_yaxes(
            title="Average Score",
            range=[0, 100]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("🎯 Grade Distribution")

        grades = (
            results["grade"]
            .value_counts()
            .reset_index()
        )

        grades.columns = ["Grade", "Count"]

        fig = px.pie(
            grades,
            names="Grade",
            values="Count",
            hole=.4
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# CHARTS
# ============================================================

def charts_page():

    st.title("📊 School Charts")

    students = df_query("SELECT * FROM students")
    results = df_query("SELECT * FROM results")
    fees = df_query("SELECT * FROM fees")
    attendance = df_query("SELECT * FROM attendance")

    chart_type = st.selectbox(
        "Choose Chart",
        [
            "Students by Class",
            "Students by Gender",
            "Scores by Subject",
            "Grades",
            "Attendance",
            "Fees"
        ],
        key="chart_type"
    )

    if chart_type == "Students by Class":

        data = (
            students["class_name"]
            .value_counts()
            .reset_index()
        )

        data.columns = ["Class", "Students"]

        fig = px.bar(
            data,
            x="Class",
            y="Students"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    elif chart_type == "Students by Gender":

        data = (
            students["gender"]
            .value_counts()
            .reset_index()
        )

        data.columns = ["Gender", "Students"]

        fig = px.pie(
            data,
            names="Gender",
            values="Students"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    elif chart_type == "Scores by Subject":

        if results.empty:
            st.info("No results.")
        else:

            data = (
                results
                .groupby("subject")["score"]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                data,
                x="subject",
                y="score"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    elif chart_type == "Grades":

        if results.empty:
            st.info("No results.")
        else:

            data = (
                results["grade"]
                .value_counts()
                .reset_index()
            )

            data.columns = ["Grade", "Count"]

            fig = px.pie(
                data,
                names="Grade",
                values="Count"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    elif chart_type == "Attendance":

        if attendance.empty:
            st.info("No attendance.")
        else:

            data = (
                attendance["status"]
                .value_counts()
                .reset_index()
            )

            data.columns = ["Status", "Count"]

            fig = px.pie(
                data,
                names="Status",
                values="Count"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    elif chart_type == "Fees":

        if fees.empty:
            st.info("No fee data.")
        else:

            data = pd.DataFrame({
                "Category": [
                    "Due",
                    "Paid",
                    "Balance"
                ],
                "Amount": [
                    fees["amount_due"].sum(),
                    fees["amount_paid"].sum(),
                    fees["balance"].sum()
                ]
            })

            fig = px.bar(
                data,
                x="Category",
                y="Amount"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


# ============================================================
# AI TEACHER ASSISTANT
# ============================================================

def ai_teacher_assistant_page():

    st.title("🤖 AI Teacher Assistant")

    st.info(
        "This is the built-in school AI assistant. "
        "You can later connect it to an external AI API."
    )

    question = st.text_area(
        "Ask the AI Teacher Assistant",
        placeholder=(
            "Example: Create a lesson plan on population "
            "for JHS 2."
        ),
        key="ai_teacher_question"
    )

    if st.button(
        "🤖 Ask AI Assistant",
        type="primary",
        key="ask_ai_teacher"
    ):

        if not question.strip():

            st.warning("Enter a question first.")

        else:

            q = question.lower()

            if "lesson" in q:

                response = """
### Suggested Lesson Plan

**Topic:** Based on your request

**Introduction**
Begin with a short discussion and connect the topic
to learners' prior knowledge.

**Objectives**
By the end of the lesson, learners should be able to:
1. Define the main concept.
2. Explain important features.
3. Give relevant examples.
4. Apply the concept to real-life situations.

**Activities**
- Teacher explanation
- Group discussion
- Learner presentation
- Question and answer

**Assessment**
Use short-answer questions, class exercises and an
exit ticket.
"""

            elif "quiz" in q:

                response = """
### Suggested Quiz

1. Define the main concept.
2. State three important features.
3. Explain two examples.
4. Describe one real-life application.
5. Give two advantages.
"""

            elif "assessment" in q:

                response = """
### Assessment Suggestions

- Diagnostic assessment
- Formative assessment
- Summative assessment
- Performance assessment
- Project-based assessment
- Digital quizzes
- Portfolio assessment
"""

            else:

                response = """
### AI Teacher Assistant

I can help you create:

- Lesson plans
- Teaching notes
- Quizzes
- Assignments
- Assessment questions
- Marking schemes
- Learning objectives
- Classroom activities
- Revision exercises

Try asking a more specific question.
"""

            st.markdown(response)


# ============================================================
# AI SCHOOL ANALYTICS
# ============================================================

def ai_school_analytics_page():

    st.title("🧠 AI School Analytics")

    results = df_query("SELECT * FROM results")
    attendance = df_query("SELECT * FROM attendance")
    fees = df_query("SELECT * FROM fees")

    if results.empty:

        st.info(
            "Enter academic results to generate AI-style insights."
        )

        return

    average = results["score"].mean()

    pass_rate = (
        (results["score"] >= 40).mean() * 100
    )

    best_subject = (
        results.groupby("subject")["score"]
        .mean()
        .idxmax()
    )

    weakest_subject = (
        results.groupby("subject")["score"]
        .mean()
        .idxmin()
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Overall Average",
        f"{average:.1f}%"
    )

    c2.metric(
        "Pass Rate",
        f"{pass_rate:.1f}%"
    )

    c3.metric(
        "Best Subject",
        best_subject
    )

    st.subheader("🤖 AI-Generated School Insights")

    if average >= 70:

        st.success(
            "Overall academic performance is strong."
        )

    elif average >= 50:

        st.warning(
            "Overall performance is moderate. "
            "Consider targeted intervention."
        )

    else:

        st.error(
            "Overall performance requires significant "
            "academic intervention."
        )

    st.write(
        f"**Strongest subject:** {best_subject}"
    )

    st.write(
        f"**Subject requiring attention:** {weakest_subject}"
    )

    if not attendance.empty:

        absent_rate = (
            (attendance["status"] == "Absent").mean()
            * 100
        )

        st.write(
            f"**Absenteeism rate:** {absent_rate:.1f}%"
        )

        if absent_rate > 20:

            st.warning(
                "High absenteeism detected. "
                "School management should investigate."
            )

    if not fees.empty:

        balance = fees["balance"].sum()

        st.write(
            f"**Outstanding fees:** GHS {balance:,.2f}"
        )


# ============================================================
# CERTIFICATES
# ============================================================

def certificates_page():

    st.title("🏆 Certificates")

    students = df_query("""
        SELECT student_id, full_name
        FROM students
        ORDER BY full_name
    """)

    if students.empty:

        st.info("Add students first.")
        return

    student_id = st.selectbox(
        "Student",
        students["student_id"].tolist(),
        key="certificate_student"
    )

    student = students[
        students["student_id"] == student_id
    ].iloc[0]

    certificate_type = st.selectbox(
        "Certificate Type",
        [
            "Certificate of Achievement",
            "Certificate of Completion",
            "Best Student",
            "Best Attendance",
            "Academic Excellence",
            "Participation"
        ],
        key="certificate_type"
    )

    description = st.text_area(
        "Certificate Description",
        key="certificate_description"
    )

    issue_date = st.date_input(
        "Issue Date",
        date.today(),
        key="certificate_date"
    )

    if st.button(
        "🏆 Issue Certificate",
        type="primary",
        key="issue_certificate"
    ):

        execute("""
            INSERT INTO certificates
            (
                student_id,
                student_name,
                certificate_type,
                description,
                issue_date
            )
            VALUES (?,?,?,?,?)
        """, (
            student["student_id"],
            student["full_name"],
            certificate_type,
            description,
            str(issue_date)
        ))

        st.success("Certificate issued.")

    st.dataframe(
        df_query(
            "SELECT * FROM certificates ORDER BY id DESC"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

def notifications_page():

    st.title("🔔 Notifications")

    recipient = st.text_input(
        "Recipient Username",
        key="notification_recipient"
    )

    title = st.text_input(
        "Notification Title",
        key="notification_title"
    )

    message = st.text_area(
        "Notification Message",
        key="notification_message"
    )

    notification_type = st.selectbox(
        "Type",
        [
            "General",
            "Academic",
            "Fees",
            "Attendance",
            "Examination",
            "LMS"
        ],
        key="notification_type"
    )

    if st.button(
        "Send Notification",
        type="primary",
        key="send_notification"
    ):

        execute("""
            INSERT INTO notifications
            (
                recipient,
                title,
                message,
                notification_type
            )
            VALUES (?,?,?,?)
        """, (
            recipient,
            title,
            message,
            notification_type
        ))

        st.success("Notification sent.")

    user = st.session_state.user

    notifications = df_query("""
        SELECT *
        FROM notifications
        WHERE recipient=?
        OR recipient='Everyone'
        ORDER BY id DESC
    """, (user["username"],))

    st.dataframe(
        notifications,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# MESSAGING
# ============================================================

def messaging_page():

    st.title("💬 Messaging")

    user = st.session_state.user

    tab1, tab2 = st.tabs([
        "✉️ Compose",
        "📥 Inbox"
    ])

    with tab1:

        recipient = st.text_input(
            "Recipient Username",
            key="message_recipient"
        )

        subject = st.text_input(
            "Subject",
            key="message_subject"
        )

        message = st.text_area(
            "Message",
            height=200,
            key="message_body"
        )

        if st.button(
            "Send Message",
            type="primary",
            key="send_message"
        ):

            execute("""
                INSERT INTO messages
                (
                    sender,
                    recipient,
                    subject,
                    message
                )
                VALUES (?,?,?,?)
            """, (
                user["username"],
                recipient,
                subject,
                message
            ))

            st.success("Message sent.")

    with tab2:

        inbox = df_query("""
            SELECT *
            FROM messages
            WHERE recipient=?
            ORDER BY id DESC
        """, (user["username"],))

        st.dataframe(
            inbox,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# EXAMINATIONS
# ============================================================

def examinations_page():

    st.title("📝 Examinations")

    with st.form("examination_form"):

        exam_name = st.text_input("Examination Name")
        subject = st.text_input("Subject")
        class_name = st.text_input("Class")

        exam_date = st.date_input(
            "Examination Date",
            key="exam_date"
        )

        start_time = st.time_input(
            "Start Time",
            key="exam_time"
        )

        duration = st.number_input(
            "Duration (minutes)",
            min_value=1,
            step=1,
            key="exam_duration"
        )

        venue = st.text_input(
            "Venue",
            key="exam_venue"
        )

        submitted = st.form_submit_button(
            "Schedule Examination",
            type="primary"
        )

        if submitted:

            execute("""
                INSERT INTO examinations
                (
                    exam_name,
                    subject,
                    class_name,
                    exam_date,
                    start_time,
                    duration,
                    venue
                )
                VALUES (?,?,?,?,?,?,?)
            """, (
                exam_name,
                subject,
                class_name,
                str(exam_date),
                str(start_time),
                duration,
                venue
            ))

            st.success(
                "Examination scheduled."
            )

    st.dataframe(
        df_query(
            "SELECT * FROM examinations ORDER BY exam_date"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TIMETABLE
# ============================================================

def timetable_page():

    st.title("🗓️ School Timetable")

    with st.form("timetable_form"):

        class_name = st.text_input(
            "Class",
            key="tt_class"
        )

        day = st.selectbox(
            "Day",
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ],
            key="tt_day"
        )

        c1, c2 = st.columns(2)

        with c1:

            start_time = st.time_input(
                "Start Time",
                key="tt_start"
            )

        with c2:

            end_time = st.time_input(
                "End Time",
                key="tt_end"
            )

        subject = st.text_input(
            "Subject",
            key="tt_subject"
        )

        teacher = st.text_input(
            "Teacher",
            key="tt_teacher"
        )

        room = st.text_input(
            "Room",
            key="tt_room"
        )

        submitted = st.form_submit_button(
            "Add Timetable Entry",
            type="primary"
        )

        if submitted:

            execute("""
                INSERT INTO timetable
                (
                    class_name,
                    day,
                    start_time,
                    end_time,
                    subject,
                    teacher,
                    room
                )
                VALUES (?,?,?,?,?,?,?)
            """, (
                class_name,
                day,
                str(start_time),
                str(end_time),
                subject,
                teacher,
                room
            ))

            st.success("Timetable entry added.")

    timetable = df_query("""
        SELECT *
        FROM timetable
        ORDER BY
        CASE day
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
        END,
        start_time
    """)

    st.dataframe(
        timetable,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ANNOUNCEMENTS
# ============================================================

def announcements_page():

    st.title("📢 Announcements")

    with st.form("announcement_form"):

        title = st.text_input(
            "Title",
            key="announcement_title"
        )

        message = st.text_area(
            "Message",
            key="announcement_message"
        )

        audience = st.selectbox(
            "Audience",
            [
                "Everyone",
                "Students",
                "Teachers",
                "Parents"
            ],
            key="announcement_audience"
        )

        submitted = st.form_submit_button(
            "Publish Announcement",
            type="primary"
        )

        if submitted:

            execute("""
                INSERT INTO announcements
                (
                    title,
                    message,
                    audience
                )
                VALUES (?,?,?)
            """, (
                title,
                message,
                audience
            ))

            st.success(
                "Announcement published."
            )

    st.dataframe(
        df_query(
            "SELECT * FROM announcements ORDER BY id DESC"
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# USERS / ADMINISTRATION
# ============================================================

def users_page():

    st.title("👥 User Management")

    user = st.session_state.user

    if user["role"] != "Administrator":

        st.error(
            "Only administrators can manage users."
        )

        return

    tab1, tab2 = st.tabs([
        "➕ Create User",
        "👥 User Accounts"
    ])

    with tab1:

        with st.form("create_user_form"):

            username = st.text_input(
                "Username",
                key="new_username"
            )

            full_name = st.text_input(
                "Full Name",
                key="new_full_name"
            )

            password = st.text_input(
                "Temporary Password",
                type="password",
                key="new_password"
            )

            role = st.selectbox(
                "Role",
                [
                    "Administrator",
                    "Teacher",
                    "Student",
                    "Parent"
                ],
                key="new_role"
            )

            email = st.text_input(
                "Email",
                key="new_email"
            )

            phone = st.text_input(
                "Phone",
                key="new_phone"
            )

            linked_student_id = st.text_input(
                "Linked Student ID (for Student/Parent)",
                key="linked_student"
            )

            submitted = st.form_submit_button(
                "Create User",
                type="primary"
            )

            if submitted:

                if not username or not full_name or not password:

                    st.error(
                        "Username, name and password are required."
                    )

                else:

                    try:

                        execute("""
                            INSERT INTO users
                            (
                                username,
                                password,
                                full_name,
                                role,
                                email,
                                phone,
                                linked_student_id
                            )
                            VALUES (?,?,?,?,?,?,?)
                        """, (
                            username,
                            hash_password(password),
                            full_name,
                            role,
                            email,
                            phone,
                            linked_student_id
                        ))

                        st.success(
                            f"{role} account created."
                        )

                    except sqlite3.IntegrityError:

                        st.error(
                            "Username already exists."
                        )

    with tab2:

        users = df_query("""
            SELECT
                id,
                username,
                full_name,
                role,
                email,
                phone,
                linked_student_id,
                status,
                created_at
            FROM users
            ORDER BY id DESC
        """)

        st.dataframe(
            users,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password_page():

    st.title("🔐 Change Password")

    user = st.session_state.user

    with st.form("change_password_form"):

        current = st.text_input(
            "Current Password",
            type="password",
            key="current_password"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_password"
        )

        confirm = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_password"
        )

        submitted = st.form_submit_button(
            "Change Password",
            type="primary"
        )

        if submitted:

            stored = execute("""
                SELECT password
                FROM users
                WHERE id=?
            """, (user["id"],), fetch=True)

            if not stored:

                st.error("User account not found.")

            elif hash_password(current) != stored[0]["password"]:

                st.error(
                    "Current password is incorrect."
                )

            elif not new_password:

                st.error(
                    "Enter a new password."
                )

            elif new_password != confirm:

                st.error(
                    "Passwords do not match."
                )

            elif len(new_password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                execute("""
                    UPDATE users
                    SET password=?
                    WHERE id=?
                """, (
                    hash_password(new_password),
                    user["id"]
                ))

                st.success(
                    "Password changed successfully."
                )


# ============================================================
# PROFILE
# ============================================================

def profile_page():

    st.title("👤 My Profile")

    user = st.session_state.user

    st.markdown(f"""
    <div class="section-card">
        <h2>👤 {user['full_name']}</h2>
        <p><b>Username:</b> {user['username']}</p>
        <p><b>Role:</b> {user['role']}</p>
        <p><b>Email:</b> {user.get('email','')}</p>
        <p><b>Phone:</b> {user.get('phone','')}</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# SETTINGS
# ============================================================

def settings_page():

    st.title("⚙️ School Settings")

    user = st.session_state.user

    if user["role"] != "Administrator":

        st.error(
            "Only administrators can change school settings."
        )

        return

    settings = get_settings()

    tab1, tab2 = st.tabs([
        "🏫 School Information",
        "🖼️ School Logo"
    ])

    with tab1:

        with st.form("school_settings_form"):

            school = st.text_input(
                "School Name",
                settings["school_name"]
            )

            year = st.text_input(
                "Academic Year",
                settings["academic_year"]
            )

            head = st.text_input(
                "Head Teacher / Headmaster",
                settings["head_teacher"]
            )

            phone = st.text_input(
                "School Phone",
                settings["phone"]
            )

            email = st.text_input(
                "School Email",
                settings["email"]
            )

            address = st.text_area(
                "School Address",
                settings["address"]
            )

            submitted = st.form_submit_button(
                "Save School Settings",
                type="primary"
            )

            if submitted:

                execute("""
                    UPDATE settings
                    SET
                        school_name=?,
                        academic_year=?,
                        head_teacher=?,
                        phone=?,
                        email=?,
                        address=?
                    WHERE id=1
                """, (
                    school,
                    year,
                    head,
                    phone,
                    email,
                    address
                ))

                st.success(
                    "School settings saved."
                )

                st.rerun()

    with tab2:

        st.write(
            "Upload your school logo. It will be saved permanently "
            "inside the school application folder."
        )

        logo = st.file_uploader(
            "Upload School Logo",
            type=["png", "jpg", "jpeg"],
            key="school_logo_upload"
        )

        if logo is not None:

            path = save_uploaded_file(
                logo,
                ASSET_DIR
            )

            execute("""
                UPDATE settings
                SET logo=?
                WHERE id=1
            """, (path,))

            st.success(
                "School logo saved permanently."
            )

            st.rerun()

        current_logo = logo_path()

        if current_logo and os.path.exists(current_logo):

            st.image(
                current_logo,
                width=180
            )


# ============================================================
# DATABASE BACKUP / RESTORE / DOWNLOAD
# ============================================================

def download_page():

    st.title("📥 Downloads & Database Backup")

    user = st.session_state.user

    if user["role"] != "Administrator":

        st.error(
            "Only administrators can manage database backups."
        )

        return

    st.subheader("💾 Create Database Backup")

    if st.button(
        "Create Backup",
        type="primary",
        key="create_database_backup"
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_name = (
            f"school_backup_{timestamp}.db"
        )

        backup_path = os.path.join(
            BACKUP_DIR,
            backup_name
        )

        shutil.copy2(
            DB_NAME,
            backup_path
        )

        st.success(
            f"Backup created: {backup_name}"
        )

    st.divider()

    st.subheader("📥 Download Current Database")

    with open(DB_NAME, "rb") as f:

        db_bytes = f.read()

    st.download_button(
        "⬇️ Download school.db",
        db_bytes,
        "school.db",
        "application/octet-stream",
        key="download_database"
    )

    st.divider()

    st.subheader("♻️ Restore Database")

    uploaded_backup = st.file_uploader(
        "Upload a previous school.db backup",
        type=["db"],
        key="restore_database_file"
    )

    if uploaded_backup is not None:

        if st.button(
            "Restore Uploaded Database",
            type="primary",
            key="restore_database"
        ):

            emergency_name = (
                f"before_restore_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )

            shutil.copy2(
                DB_NAME,
                os.path.join(
                    BACKUP_DIR,
                    emergency_name
                )
            )

            with open(DB_NAME, "wb") as f:
                f.write(
                    uploaded_backup.getbuffer()
                )

            st.success(
                "Database restored successfully. "
                "Restart the application."
            )

            st.stop()

    st.divider()

    st.subheader("📦 Download Full School Backup")

    if st.button(
        "Create Full Backup ZIP",
        key="create_full_backup"
    ):

        memory = io.BytesIO()

        with zipfile.ZipFile(
            memory,
            "w",
            zipfile.ZIP_DEFLATED
        ) as z:

            if os.path.exists(DB_NAME):

                z.write(
                    DB_NAME,
                    arcname="school.db"
                )

            if os.path.exists(ASSET_DIR):

                for root, dirs, files in os.walk(
                    ASSET_DIR
                ):

                    for file in files:

                        full_path = os.path.join(
                            root,
                            file
                        )

                        relative = os.path.relpath(
                            full_path
                        )

                        z.write(
                            full_path,
                            arcname=relative
                        )

        memory.seek(0)

        st.download_button(
            "⬇️ Download Full School Backup",
            memory.getvalue(),
            "21st_global_school_full_backup.zip",
            "application/zip",
            key="download_full_backup"
        )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.user = None

    # Clear page selection
    if "main_navigation" in st.session_state:
        del st.session_state["main_navigation"]

    st.rerun()


# ============================================================
# INITIALIZATION
# ============================================================

init_database()
load_css()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# ============================================================
# APPLICATION
# ============================================================

if not st.session_state.logged_in:

    login_page()

else:

    user = st.session_state.user

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    with st.sidebar:

        settings = get_settings()

        logo = settings.get("logo", "")

        if logo and os.path.exists(logo):

            st.image(
                logo,
                use_container_width=True
            )

        else:

            st.markdown("""
            <div style="
                text-align:center;
                padding:15px;
                background:linear-gradient(
                    135deg,
                    #0d47a1,
                    #1565c0
                );
                color:white;
                border-radius:15px;
            ">
                <h2>🎓 21ST GLOBAL</h2>
                <p>COMMUNITY SCHOOL</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.write(
            f"👤 **{user['full_name']}**"
        )

        st.caption(
            f"Role: {user['role']}"
        )

        st.divider()

        # ----------------------------------------------------
        # ROLE-BASED MENUS
        # ----------------------------------------------------

        if user["role"] == "Administrator":

            menu_items = [

                "📊 Dashboard",
                "👨‍🎓 Students",
                "👩‍🏫 Teachers",
                "🏫 Classes",
                "📚 Subjects",
                "🕐 Attendance",
                "📝 Results",
                "📄 Report Cards",
                "💰 Fees",
                "🧾 Fee Receipts",
                "📑 Fee Statements",
                "🎓 LMS",
                "📈 Analytics",
                "📊 Charts",
                "🏆 Certificates",
                "🔔 Notifications",
                "💬 Messaging",
                "📝 Examinations",
                "🗓️ Timetable",
                "📢 Announcements",
                "🤖 AI Teacher Assistant",
                "🧠 AI School Analytics",
                "👥 User Management",
                "📥 Downloads",
                "⚙️ Settings",
                "👤 My Profile",
                "🔐 Change Password"
            ]

        elif user["role"] == "Teacher":

            menu_items = [

                "📊 ",
                "👨‍🎓 Students",
                "🕐 Attendance",
                "📝 Results",
                "📄 Report Cards",
                "🎓 LMS",
                "📈 Analytics",
                "📊 Charts",
                "🏆 Certificates",
                "🔔 Notifications",
                "💬 Messaging",
                "📝 Examinations",
                "🗓️ Timetable",
                "📢 Announcements",
                "🤖 AI Teacher Assistant",
                "🧠 AI School Analytics",
                "👤 My Profile",
                "🔐 "
            ]

        elif user["role"] == "Student":

            menu_items = [

                "📊 ",
                "📄 Report Cards",
                "🎓 LMS",
                "📝 Examinations",
                "🗓️ Timetable",
                "💰 Fees",
                "🧾 Fee Receipts",
                "📑 Fee Statements",
                "🔔 Notifications",
                "💬 Messaging",
                "📢 Announcements",
                "👤 My Profile",
                "🔐 "
            ]

        else:

            menu_items = [

                "📊 Dashboard",
                "📄 Report Cards",
                "🎓 LMS",
                "📝 Examinations",
                "🗓️ Timetable",
                "💰 Fees",
                "🧾 Fee Receipts",
                "📑 Fee Statements",
                "🔔 Notifications",
                "💬 Messaging",
                "📢 Announcements",
                "👤 My Profile",
                "🔐 "
            ]

        menu = st.radio(
            "MAIN MENU",
            menu_items,
            key="main_navigation"
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            key="sidebar_logout_button",
            use_container_width=True
        ):

            logout()


    # --------------------------------------------------------
    # PAGE ROUTING
    # --------------------------------------------------------

    if menu == "📊 Dashboard":
        dashboard()

    elif menu == "👨‍🎓 Students":
        students_page()

    elif menu == "👩‍🏫 Teachers":
        teachers_page()

    elif menu == "🏫 Classes":
        classes_page()

    elif menu == "📚 Subjects":
        subjects_page()

    elif menu == "🕐 Attendance":
        attendance_page()

    elif menu == "📝 Results":
        results_page()

    elif menu == "📄 Report Cards":
        report_cards_page()

    elif menu == "💰 Fees":
        fees_page()

    elif menu == "🧾 Fee Receipts":
        fee_receipts_page()

    elif menu == "📑 Fee Statements":
        fee_statements_page()

    elif menu == "🎓 LMS":
        lms_page()

    elif menu == "📈 Analytics":
        analytics_page()

    elif menu == "📊 Charts":
        charts_page()

    elif menu == "🏆 Certificates":
        certificates_page()

    elif menu == "🔔 Notifications":
        notifications_page()

    elif menu == "💬 Messaging":
        messaging_page()

    elif menu == "📝 Examinations":
        examinations_page()

    elif menu == "🗓️ Timetable":
        timetable_page()

    elif menu == "📢 Announcements":
        announcements_page()

    elif menu == "🤖 AI Teacher Assistant":
        ai_teacher_assistant_page()

    elif menu == "🧠 AI School Analytics":
        ai_school_analytics_page()

    elif menu == "👥 User Management":
        users_page()

    elif menu == "📥 Downloads":
        download_page()

    elif menu == "⚙️ Settings":
        settings_page()

    elif menu == "👤 My Profile":
        profile_page()

    elif menu == "🔐 Change Password":
        change_password_page()
