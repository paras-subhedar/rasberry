import os
import sqlite3
import time
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_PATH = "/home/jcoetee/noticeboard"
DB_PATH = os.path.join(BASE_PATH, "database.db")

IMAGE_FOLDER = os.path.join(BASE_PATH, "static/images")
VIDEO_FOLDER = os.path.join(BASE_PATH, "static/videos")
SLIDES_FOLDER = os.path.join(BASE_PATH, "static/slides")

LAST_UPDATED = time.time()

# ------------------ DATABASE ------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # ✅ IMPORTANT (gives dict-like access)
    return conn

# ------------------ VERSION API ------------------
@app.route('/api/version')
def get_version():
    return jsonify({"version": LAST_UPDATED})

# ------------------ HOME DISPLAY ------------------
@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    notices = []

    for row in rows:
        notice = {
            "id": row["id"],
            "title": row["title"],
            "type": row["media_type"],
            "content": row["content"],
            "file": row["file_path"],
            "duration": row["duration"],
            "slides": []
        }

        # Handle slideshow images
        if notice["type"] == "slideshow" and notice["file"]:
            folder = os.path.join(BASE_PATH, notice["file"])
            if os.path.exists(folder):
                images = os.listdir(folder)
                notice["slides"] = [notice["file"] + img for img in images]

        notices.append(notice)

    return render_template('index.html', notices=notices)

# ------------------ GET ALL NOTICES ------------------
@app.route('/notices', methods=['GET'])
def get_notices():
    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

# ------------------ UPLOAD ------------------
@app.route('/upload', methods=['POST'])
def upload():
    global LAST_UPDATED

    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    title = request.form.get('title')
    media_type = request.form.get('media_type')
    duration = request.form.get('duration', 20)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notices (title, media_type, duration)
        VALUES (?, ?, ?)
    """, (title, media_type, duration))

    notice_id = cursor.lastrowid
    db_path = None

    if media_type == 'image':
        file = request.files['file']
        filename = secure_filename(file.filename)
        path = os.path.join(IMAGE_FOLDER, filename)
        file.save(path)
        db_path = f"static/images/{filename}"

    elif media_type == 'video':
        file = request.files['file']
        filename = secure_filename(file.filename)
        path = os.path.join(VIDEO_FOLDER, filename)
        file.save(path)
        db_path = f"static/videos/{filename}"

    elif media_type == 'slideshow':
        files = request.files.getlist('files')
        folder_name = f"event_{notice_id}"
        folder_path = os.path.join(SLIDES_FOLDER, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        for file in files:
            filename = secure_filename(file.filename)
            file.save(os.path.join(folder_path, filename))

        db_path = f"static/slides/{folder_name}/"

    elif media_type == 'text':
        content = request.form.get('content')
        cursor.execute("UPDATE notices SET content=? WHERE id=?", (content, notice_id))

    if db_path:
        cursor.execute("UPDATE notices SET file_path=? WHERE id=?", (db_path, notice_id))

    conn.commit()
    conn.close()

    LAST_UPDATED = time.time()

    return jsonify({"status": "success", "id": notice_id})

# ------------------ UPDATE ------------------
@app.route('/update/<int:notice_id>', methods=['POST'])
def update_notice(notice_id):
    global LAST_UPDATED

    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    title = request.form.get('title')
    content = request.form.get('content')
    duration = request.form.get('duration')

    conn = get_db()
    cursor = conn.cursor()

    if title:
        cursor.execute("UPDATE notices SET title=? WHERE id=?", (title, notice_id))

    if content:
        cursor.execute("UPDATE notices SET content=? WHERE id=?", (content, notice_id))

    if duration:
        cursor.execute("UPDATE notices SET duration=? WHERE id=?", (duration, notice_id))

    conn.commit()
    conn.close()

    LAST_UPDATED = time.time()

    return jsonify({"status": "updated"})

# ------------------ DELETE ------------------
@app.route('/delete/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    global LAST_UPDATED

    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path, media_type FROM notices WHERE id=?", (notice_id,))
    row = cursor.fetchone()

    if row:
        file_path = row["file_path"]
        media_type = row["media_type"]

        if file_path:
            full_path = os.path.join(BASE_PATH, file_path)

            if media_type == 'slideshow':
                if os.path.exists(full_path):
                    for f in os.listdir(full_path):
                        os.remove(os.path.join(full_path, f))
                    os.rmdir(full_path)
            else:
                if os.path.exists(full_path):
                    os.remove(full_path)

    cursor.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    conn.commit()
    conn.close()

    LAST_UPDATED = time.time()

    return jsonify({"status": "deleted"})

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)