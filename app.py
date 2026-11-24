
import os
import time

import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash

app = Flask(__name__)
CORS(app)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "academic_timetable")
    )


def get_data():
    return request.get_json(silent=True) or {}


def error_response(message, status=400):
    return jsonify({"error": message}), status


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return "Academic Timetable Backend is Running!"


# =========================================================
# LOGIN
# =========================================================

@app.route("/auth/login", methods=["POST"])
def login_user():
    data = get_data()

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email and password are required")

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, full_name, email, password_hash,
                   role, department, is_active
            FROM users
            WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return error_response("Invalid email or password", 401)

        if not user["is_active"]:
            return error_response(
                "Your account is inactive. Contact the administrator.",
                403
            )

        if not check_password_hash(user["password_hash"], password):
            return error_response("Invalid email or password", 401)

        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "department": user["department"]
            }
        }), 200

    except mysql.connector.Error:
        app.logger.exception("Login database error")
        return error_response("Database error during login", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# TEACHERS
# =========================================================

@app.route("/teachers", methods=["GET"])
def get_teachers():
    return fetch_all("SELECT * FROM teachers ORDER BY id")


@app.route("/teachers", methods=["POST"])
def add_teacher():
    data = get_data()

    values = (
        data.get("id"),
        data.get("name"),
        data.get("department"),
        data.get("email")
    )

    if not all(values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO teachers (id, name, department, email)
        VALUES (%s, %s, %s, %s)
    """, values, "Teacher added successfully")


@app.route("/teachers/<teacher_id>", methods=["PUT"])
def update_teacher(teacher_id):
    data = get_data()

    values = (
        data.get("name"),
        data.get("department"),
        data.get("email")
    )

    if not all(values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE teachers
        SET name=%s, department=%s, email=%s
        WHERE id=%s
    """, values + (teacher_id,), "Teacher updated successfully")


@app.route("/teachers/<teacher_id>", methods=["DELETE"])
def delete_teacher(teacher_id):
    return execute_delete(
        "DELETE FROM teachers WHERE id=%s",
        (teacher_id,),
        "Teacher deleted successfully"
    )


# =========================================================
# SUBJECTS
# =========================================================

@app.route("/subjects", methods=["GET"])
def get_subjects():
    return fetch_all("""
        SELECT s.id, s.name, s.credits, s.type,
               s.hours_per_week, s.teacher_id,
               t.name AS teacher_name
        FROM subjects s
        LEFT JOIN teachers t ON s.teacher_id=t.id
        ORDER BY s.id
    """)


@app.route("/subjects", methods=["POST"])
def add_subject():
    data = get_data()

    values = (
        data.get("id"),
        data.get("name"),
        data.get("credits"),
        data.get("type"),
        data.get("hours"),
        data.get("teacher_id")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO subjects
        (id, name, credits, type, hours_per_week, teacher_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, values, "Subject added successfully")


@app.route("/subjects/<subject_id>", methods=["PUT"])
def update_subject(subject_id):
    data = get_data()

    values = (
        data.get("name"),
        data.get("credits"),
        data.get("type"),
        data.get("hours"),
        data.get("teacher_id")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE subjects
        SET name=%s, credits=%s, type=%s,
            hours_per_week=%s, teacher_id=%s
        WHERE id=%s
    """, values + (subject_id,), "Subject updated successfully")


@app.route("/subjects/<subject_id>", methods=["DELETE"])
def delete_subject(subject_id):
    return execute_delete(
        "DELETE FROM subjects WHERE id=%s",
        (subject_id,),
        "Subject deleted successfully"
    )


# =========================================================
# CLASSES
# =========================================================

@app.route("/classes", methods=["GET"])
def get_classes():
    return fetch_all("SELECT * FROM classes ORDER BY id")


@app.route("/classes", methods=["POST"])
def add_class():
    data = get_data()

    values = (
        data.get("id"),
        data.get("course"),
        data.get("year"),
        data.get("semester"),
        data.get("section"),
        data.get("strength")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO classes
        (id, course, year, semester, section, strength)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, values, "Class added successfully")


@app.route("/classes/<class_id>", methods=["PUT"])
def update_class(class_id):
    data = get_data()

    values = (
        data.get("course"),
        data.get("year"),
        data.get("semester"),
        data.get("section"),
        data.get("strength")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE classes
        SET course=%s, year=%s, semester=%s,
            section=%s, strength=%s
        WHERE id=%s
    """, values + (class_id,), "Class updated successfully")


@app.route("/classes/<class_id>", methods=["DELETE"])
def delete_class(class_id):
    return execute_delete(
        "DELETE FROM classes WHERE id=%s",
        (class_id,),
        "Class deleted successfully"
    )


# =========================================================
# ROOMS AND LABS
# =========================================================

@app.route("/rooms", methods=["GET"])
def get_rooms():
    return fetch_all("SELECT * FROM rooms ORDER BY id")


@app.route("/rooms", methods=["POST"])
def add_room():
    data = get_data()

    values = (
        data.get("id"),
        data.get("number"),
        data.get("type"),
        data.get("capacity")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO rooms (id, number, type, capacity)
        VALUES (%s, %s, %s, %s)
    """, values, "Room added successfully")


@app.route("/rooms/<room_id>", methods=["PUT"])
def update_room(room_id):
    data = get_data()

    values = (
        data.get("number"),
        data.get("type"),
        data.get("capacity")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE rooms
        SET number=%s, type=%s, capacity=%s
        WHERE id=%s
    """, values + (room_id,), "Room updated successfully")


@app.route("/rooms/<room_id>", methods=["DELETE"])
def delete_room(room_id):
    return execute_delete(
        "DELETE FROM rooms WHERE id=%s",
        (room_id,),
        "Room deleted successfully"
    )


# =========================================================
# TIME SLOTS
# =========================================================

@app.route("/time-slots", methods=["GET"])
def get_time_slots():
    return fetch_all("""
        SELECT id, day, period,
               TIME_FORMAT(start_time, '%H:%i') AS startTime,
               TIME_FORMAT(end_time, '%H:%i') AS endTime
        FROM time_slots
        ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday',
                       'Thursday', 'Friday', 'Saturday'), period
    """)


@app.route("/time-slots", methods=["POST"])
def add_time_slot():
    data = get_data()

    values = (
        data.get("id"),
        data.get("day"),
        data.get("period"),
        data.get("startTime"),
        data.get("endTime")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO time_slots (id, day, period, start_time, end_time)
        VALUES (%s, %s, %s, %s, %s)
    """, values, "Time slot added successfully")


@app.route("/time-slots/<slot_id>", methods=["PUT"])
def update_time_slot(slot_id):
    data = get_data()

    values = (
        data.get("day"),
        data.get("period"),
        data.get("startTime"),
        data.get("endTime")
    )

    if not all(v is not None and v != "" for v in values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE time_slots
        SET day=%s, period=%s, start_time=%s, end_time=%s
        WHERE id=%s
    """, values + (slot_id,), "Time slot updated successfully")


@app.route("/time-slots/<slot_id>", methods=["DELETE"])
def delete_time_slot(slot_id):
    return execute_delete(
        "DELETE FROM time_slots WHERE id=%s",
        (slot_id,),
        "Time slot deleted successfully"
    )


# =========================================================
# TEACHER AVAILABILITY
# =========================================================

@app.route("/teacher-availability", methods=["GET"])
def get_teacher_availability():
    return fetch_all("""
        SELECT a.id, a.teacher_id, t.name AS teacher_name,
               a.day, a.period, a.available
        FROM teacher_availability a
        JOIN teachers t ON a.teacher_id=t.id
        ORDER BY a.teacher_id,
                 FIELD(a.day, 'Monday', 'Tuesday', 'Wednesday',
                       'Thursday', 'Friday', 'Saturday'),
                 a.period
    """)


@app.route("/teacher-availability", methods=["POST"])
def add_teacher_availability():
    data = get_data()

    values = (
        data.get("teacher_id"),
        data.get("day"),
        data.get("period"),
        data.get("available")
    )

    if any(v is None or v == "" for v in values):
        return error_response("All fields are required")

    return execute_insert("""
        INSERT INTO teacher_availability
        (teacher_id, day, period, available)
        VALUES (%s, %s, %s, %s)
    """, values, "Teacher availability added successfully")


@app.route("/teacher-availability/<int:availability_id>", methods=["PUT"])
def update_teacher_availability(availability_id):
    data = get_data()

    values = (
        data.get("teacher_id"),
        data.get("day"),
        data.get("period"),
        data.get("available")
    )

    if any(v is None or v == "" for v in values):
        return error_response("All fields are required")

    return execute_update("""
        UPDATE teacher_availability
        SET teacher_id=%s, day=%s, period=%s, available=%s
        WHERE id=%s
    """, values + (availability_id,),
       "Teacher availability updated successfully")


@app.route("/teacher-availability/<int:availability_id>", methods=["DELETE"])
def delete_teacher_availability(availability_id):
    return execute_delete("""
        DELETE FROM teacher_availability WHERE id=%s
    """, (availability_id,), "Teacher availability deleted successfully")


# =========================================================
# CLASS SUBJECTS
# =========================================================

@app.route("/class-subjects", methods=["GET"])
def get_class_subjects():
    return fetch_all("""
        SELECT cs.id, cs.class_id, c.course, c.year, c.section,
               cs.subject_id, s.name AS subject_name,
               s.teacher_id, t.name AS teacher_name
        FROM class_subjects cs
        JOIN classes c ON cs.class_id=c.id
        JOIN subjects s ON cs.subject_id=s.id
        LEFT JOIN teachers t ON s.teacher_id=t.id
        ORDER BY cs.class_id, cs.subject_id
    """)


@app.route("/class-subjects", methods=["POST"])
def add_class_subject():
    data = get_data()

    class_id = data.get("class_id")
    subject_id = data.get("subject_id")

    if not class_id or not subject_id:
        return error_response("Class and subject are required")

    return execute_insert("""
        INSERT INTO class_subjects (class_id, subject_id)
        VALUES (%s, %s)
    """, (class_id, subject_id),
       "Subject assigned to class successfully")


@app.route("/class-subjects/<int:assignment_id>", methods=["DELETE"])
def delete_class_subject(assignment_id):
    return execute_delete("""
        DELETE FROM class_subjects WHERE id=%s
    """, (assignment_id,), "Subject removed from class successfully")


# =========================================================
# LATEST TIMETABLE
# =========================================================

@app.route("/timetable", methods=["GET"])
def get_timetable():
    class_id = request.args.get("class_id")

    query = """
        SELECT tt.id, tt.class_id,
               c.course, c.year, c.semester, c.section,
               tt.subject_id, s.name AS subject_name,
               tt.teacher_id, t.name AS teacher_name,
               tt.room_id, r.number AS room_number,
               r.type AS room_type, tt.day, tt.period
        FROM timetable tt
        JOIN classes c ON tt.class_id=c.id
        JOIN subjects s ON tt.subject_id=s.id
        JOIN teachers t ON tt.teacher_id=t.id
        JOIN rooms r ON tt.room_id=r.id
    """

    params = ()

    if class_id:
        query += " WHERE tt.class_id=%s"
        params = (class_id,)

    query += """
        ORDER BY FIELD(tt.day, 'Monday', 'Tuesday', 'Wednesday',
                       'Thursday', 'Friday', 'Saturday'), tt.period
    """

    return fetch_all(query, params)


# =========================================================
# TIMETABLE VERSION HISTORY
# =========================================================

@app.route("/timetable/versions", methods=["GET"])
def get_timetable_versions():
    return fetch_all("""
        SELECT id, version_name, generated_at,
               total_entries, total_classes,
               quality_score, generation_time_seconds
        FROM timetable_versions
        ORDER BY id DESC
    """)


# =========================================================
# GET A PARTICULAR SAVED VERSION
# Optional: ?class_id=CLASS_ID
# =========================================================

@app.route("/timetable/versions/<int:version_id>", methods=["GET"])
def get_saved_timetable(version_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, version_name
            FROM timetable_versions
            WHERE id=%s
        """, (version_id,))

        version = cursor.fetchone()

        if not version:
            return error_response("Timetable version not found", 404)

        class_id = request.args.get("class_id")

        query = """
            SELECT e.id, e.class_id,
                   c.course, c.year, c.semester, c.section,
                   e.subject_id, s.name AS subject_name,
                   e.teacher_id, t.name AS teacher_name,
                   e.room_id, r.number AS room_number,
                   r.type AS room_type,
                   e.day, e.period
            FROM timetable_version_entries e
            JOIN classes c ON e.class_id=c.id
            JOIN subjects s ON e.subject_id=s.id
            JOIN teachers t ON e.teacher_id=t.id
            JOIN rooms r ON e.room_id=r.id
            WHERE e.version_id=%s
        """

        params = [version_id]

        if class_id:
            query += " AND e.class_id=%s"
            params.append(class_id)

        query += """
            ORDER BY FIELD(e.day, 'Monday', 'Tuesday', 'Wednesday',
                           'Thursday', 'Friday', 'Saturday'),
                     e.period
        """

        cursor.execute(query, tuple(params))
        entries = cursor.fetchall()

        return jsonify({
            "version": version,
            "entries": entries
        })

    except mysql.connector.Error:
        app.logger.exception("Get saved timetable failed")
        return error_response("Unable to fetch saved timetable", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# COMMON DATABASE HELPERS
# =========================================================

def fetch_all(query, params=()):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)

        return jsonify(cursor.fetchall())

    except mysql.connector.Error:
        app.logger.exception("Database read failed")
        return error_response("Database read operation failed", 500)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_insert(query, values, message):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()

        return jsonify({"message": message}), 201

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Database insert failed")
        return error_response(str(error), 400)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_update(query, values, message):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)

        if cursor.rowcount == 0:
            return error_response("Record not found", 404)

        connection.commit()

        return jsonify({"message": message})

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Database update failed")
        return error_response(str(error), 400)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_delete(query, values, message):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)

        if cursor.rowcount == 0:
            return error_response("Record not found", 404)

        connection.commit()

        return jsonify({"message": message})

    except mysql.connector.Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Database delete failed")
        return error_response(str(error), 400)

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# =========================================================
# AUTOMATIC TIMETABLE GENERATION - BACKTRACKING
# =========================================================

@app.route("/timetable/generate", methods=["POST"])
def generate_timetable():
    started_at = time.perf_counter()

    connection = None
    cursor = None

    nodes_visited = 0
    backtracks = 0

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # GET CLASS-SUBJECT ASSIGNMENTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT cs.class_id, cs.subject_id,
                   s.name AS subject_name,
                   s.type AS subject_type,
                   s.hours_per_week,
                   s.teacher_id,
                   c.strength,
                   t.name AS teacher_name
            FROM class_subjects cs
            JOIN subjects s ON cs.subject_id=s.id
            JOIN classes c ON cs.class_id=c.id
            JOIN teachers t ON s.teacher_id=t.id
            ORDER BY cs.class_id, cs.subject_id
        """)

        assignments = cursor.fetchall()

        if not assignments:
            return error_response("No class-subject assignments found")

        # -------------------------------------------------
        # GET ROOMS
        # -------------------------------------------------

        cursor.execute("""
            SELECT id, number, type, capacity
            FROM rooms
            ORDER BY id
        """)

        rooms = cursor.fetchall()

        # -------------------------------------------------
        # GET TIME SLOTS
        # -------------------------------------------------

        cursor.execute("""
            SELECT id, day, period, start_time, end_time
            FROM time_slots
            ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday',
                           'Thursday', 'Friday', 'Saturday'), period
        """)

        slots = cursor.fetchall()

        # -------------------------------------------------
        # GET TEACHER AVAILABILITY
        # -------------------------------------------------

        cursor.execute("""
            SELECT teacher_id, day, period, available
            FROM teacher_availability
        """)

        availability_rows = cursor.fetchall()

        if not rooms:
            return error_response("No rooms or labs are configured")

        if not slots:
            return error_response("No time slots are configured")

        availability = {
            (row["teacher_id"], row["day"], int(row["period"])):
                bool(row["available"])
            for row in availability_rows
        }

        # -------------------------------------------------
        # CREATE SCHEDULING TASKS
        # -------------------------------------------------

        tasks = []

        for item in assignments:
            hours = int(item["hours_per_week"])
            strength = int(item["strength"])

            if hours < 1 or strength < 1:
                return error_response(
                    "Weekly hours and class strength must be positive."
                )

            for occurrence in range(hours):
                tasks.append({
                    "class_id": item["class_id"],
                    "subject_id": item["subject_id"],
                    "subject_name": item["subject_name"],
                    "subject_type": item["subject_type"],
                    "teacher_id": item["teacher_id"],
                    "teacher_name": item["teacher_name"],
                    "strength": strength,
                    "occurrence": occurrence
                })

        # -------------------------------------------------
        # MOST CONSTRAINED TASKS FIRST
        # -------------------------------------------------

        tasks.sort(key=lambda task: (
            0 if str(task["subject_type"]).strip().lower() == "lab"
            else 1,
            -task["strength"],
            str(task["class_id"]),
            str(task["subject_id"]),
            task["occurrence"]
        ))

        for room in rooms:
            room["capacity"] = int(room["capacity"])
            room["type"] = str(room["type"] or "")

        possible_rooms = {
            i: [
                room for room in rooms
                if room["capacity"] >= task["strength"]
                and (
                    str(task["subject_type"]).strip().lower() != "lab"
                    or room["type"].strip().lower() == "lab"
                )
            ]
            for i, task in enumerate(tasks)
        }

        # -------------------------------------------------
        # TRACK OCCUPIED RESOURCES
        # -------------------------------------------------

        class_busy = set()
        teacher_busy = set()
        room_busy = set()

        generated = []

        daily_subject_count = {}
        daily_class_load = {}
        daily_subject_periods = set()

        def teacher_available(teacher_id, day, period):
            # Missing availability records mean available.
            return availability.get(
                (teacher_id, day, period), True
            )

        # -------------------------------------------------
        # CANDIDATE SCORING
        # -------------------------------------------------

        def score(task, slot):
            class_id = task["class_id"]
            subject_id = task["subject_id"]
            day = slot["day"]
            period = int(slot["period"])

            result = daily_subject_count.get(
                (class_id, subject_id, day), 0
            ) * 12

            for adjacent in (period - 1, period + 1):
                if (
                    class_id, subject_id, day, adjacent
                ) in daily_subject_periods:
                    result += 18

            result += daily_class_load.get(
                (class_id, day), 0
            ) * 2

            return result + period * 0.01

        # -------------------------------------------------
        # BACKTRACKING ALGORITHM
        # -------------------------------------------------

        def backtrack(index):
            nonlocal nodes_visited, backtracks

            nodes_visited += 1

            if index == len(tasks):
                return True

            if nodes_visited > 250000:
                return False

            task = tasks[index]
            candidates = []

            for slot in slots:
                day = slot["day"]
                period = int(slot["period"])

                class_key = (task["class_id"], day, period)
                teacher_key = (task["teacher_id"], day, period)

                if class_key in class_busy:
                    continue

                if teacher_key in teacher_busy:
                    continue

                if not teacher_available(
                    task["teacher_id"], day, period
                ):
                    continue

                for room in possible_rooms[index]:
                    room_key = (room["id"], day, period)

                    if room_key in room_busy:
                        continue

                    candidates.append((
                        score(task, slot),
                        str(day),
                        period,
                        slot,
                        room,
                        class_key,
                        teacher_key,
                        room_key
                    ))

            candidates.sort(
                key=lambda x: (
                    x[0], x[1], x[2], str(x[4]["id"])
                )
            )

            for (
                _, day, period, slot, room,
                class_key, teacher_key, room_key
            ) in candidates:

                class_id = task["class_id"]
                subject_id = task["subject_id"]

                subject_day_key = (class_id, subject_id, day)
                class_day_key = (class_id, day)
                subject_period_key = (
                    class_id, subject_id, day, period
                )

                class_busy.add(class_key)
                teacher_busy.add(teacher_key)
                room_busy.add(room_key)

                daily_subject_count[subject_day_key] = (
                    daily_subject_count.get(subject_day_key, 0) + 1
                )

                daily_class_load[class_day_key] = (
                    daily_class_load.get(class_day_key, 0) + 1
                )

                daily_subject_periods.add(subject_period_key)

                generated.append({
                    "class_id": class_id,
                    "subject_id": subject_id,
                    "teacher_id": task["teacher_id"],
                    "room_id": room["id"],
                    "day": day,
                    "period": period
                })

                if backtrack(index + 1):
                    return True

                # Undo assignment during backtracking.
                generated.pop()

                class_busy.remove(class_key)
                teacher_busy.remove(teacher_key)
                room_busy.remove(room_key)

                daily_subject_count[subject_day_key] -= 1

                if daily_subject_count[subject_day_key] == 0:
                    del daily_subject_count[subject_day_key]

                daily_class_load[class_day_key] -= 1

                if daily_class_load[class_day_key] == 0:
                    del daily_class_load[class_day_key]

                daily_subject_periods.remove(subject_period_key)

                backtracks += 1

            return False

        # -------------------------------------------------
        # RUN GENERATOR
        # -------------------------------------------------

        success = backtrack(0)

        elapsed = round(
            time.perf_counter() - started_at, 4
        )

        total_required = len(tasks)

        if not success:
            message = (
                "Unable to generate a complete conflict-free timetable. "
                "Check rooms, time slots, teacher availability and assignments."
            )

            if nodes_visited > 250000:
                message += (
                    " Search limit reached; simplify the constraints."
                )

            return jsonify({
                "error": message,
                "total_required_periods": total_required,
                "scheduled_periods": 0,
                "unscheduled_periods": total_required,
                "generation_time_seconds": elapsed,
                "backtracking_nodes": nodes_visited,
                "backtracks": backtracks
            }), 400

        # -------------------------------------------------
        # CALCULATE QUALITY SCORE
        # -------------------------------------------------

        repeated = sum(
            max(0, count - 1)
            for count in daily_subject_count.values()
        )

        quality_score = max(
            0,
            min(
                100,
                round(
                    100 - (
                        repeated * 5 / max(1, total_required)
                    ) * 100
                )
            )
        )

        total_classes = len({
            entry["class_id"] for entry in generated
        })

        # -------------------------------------------------
        # SAVE A NEW VERSION
        # AND UPDATE THE LATEST TIMETABLE
        # -------------------------------------------------

        cursor.close()
        cursor = connection.cursor()

        connection.start_transaction()

        # Create a new version for every successful generation.
        cursor.execute("""
            INSERT INTO timetable_versions
            (
                version_name,
                total_entries,
                total_classes,
                quality_score,
                generation_time_seconds
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            "New timetable",
            len(generated),
            total_classes,
            quality_score,
            elapsed
        ))

        version_id = cursor.lastrowid
        version_name = f"Version {version_id}"

        cursor.execute("""
            UPDATE timetable_versions
            SET version_name=%s
            WHERE id=%s
        """, (version_name, version_id))

        # Save every entry in version history.
        cursor.executemany("""
            INSERT INTO timetable_version_entries
            (
                version_id, class_id, subject_id,
                teacher_id, room_id, day, period
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [
            (
                version_id,
                entry["class_id"],
                entry["subject_id"],
                entry["teacher_id"],
                entry["room_id"],
                entry["day"],
                entry["period"]
            )
            for entry in generated
        ])

        # Keep the existing timetable table updated
        # with the latest generated version.
        cursor.execute("DELETE FROM timetable")

        cursor.executemany("""
            INSERT INTO timetable
            (class_id, subject_id, teacher_id, room_id, day, period)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, [
            (
                entry["class_id"],
                entry["subject_id"],
                entry["teacher_id"],
                entry["room_id"],
                entry["day"],
                entry["period"]
            )
            for entry in generated
        ])

        connection.commit()

        final_elapsed = round(
            time.perf_counter() - started_at, 4
        )

        return jsonify({
            "message": "Timetable generated and saved successfully",
            "version_id": version_id,
            "version_name": version_name,
            "total_entries": len(generated),
            "total_classes": total_classes,
            "total_required_periods": total_required,
            "scheduled_periods": len(generated),
            "unscheduled_periods": 0,
            "generation_time_seconds": final_elapsed,
            "backtracking_nodes": nodes_visited,
            "backtracks": backtracks,
            "quality_score": quality_score,
            "optimization": (
                "Weekly subject distribution and "
                "adjacent-period reduction"
            )
        })

    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Timetable database error")
        return error_response(
            "Timetable database operation failed. "
            "Check the timetable version tables.",
            500
        )

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()

        app.logger.exception("Timetable generation failed")
        return error_response("Timetable generation failed", 500)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
