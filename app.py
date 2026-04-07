import os
import sqlite3
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

# ------------------ DATABASE ------------------
def get_db():
    return sqlite3.connect(DB_PATH)

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
        notice = list(row)

        # slideshow images
        if row[3] == 'slideshow' and row[4]:
            folder = os.path.join(BASE_PATH, row[4])
            if os.path.exists(folder):
                images = os.listdir(folder)
                images = [row[4] + img for img in images]
                notice.append(images)
            else:
                notice.append([])
        else:
            notice.append([])

        notices.append(notice)

    return render_template('index.html', notices=notices)

# ------------------ GET ALL NOTICES (READ) ------------------
@app.route('/notices', methods=['GET'])
def get_notices():
    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return jsonify(rows)

# ------------------ UPLOAD (CREATE) ------------------
@app.route('/upload', methods=['POST'])
def upload():
    print("REQUEST RECEIVED")
    print("FORM DATA:", request.form)
    print("FILES:", request.files)

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

    return jsonify({"status": "success", "id": notice_id})

# ------------------ UPDATE ------------------
@app.route('/update/<int:notice_id>', methods=['POST'])
def update_notice(notice_id):
    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    title = request.form.get('title')
    content = request.form.get('content')
    duration = request.form.get('duration')

    conn = get_db()
    cursor = conn.cursor()

    # Update only provided fields
    if title:
        cursor.execute("UPDATE notices SET title=? WHERE id=?", (title, notice_id))

    if content:
        cursor.execute("UPDATE notices SET content=? WHERE id=?", (content, notice_id))

    if duration:
        cursor.execute("UPDATE notices SET duration=? WHERE id=?", (duration, notice_id))

    conn.commit()
    conn.close()

    return jsonify({"status": "updated"})

# ------------------ DELETE ------------------
@app.route('/delete/<int:notice_id>', methods=['DELETE'])
def delete_notice(notice_id):
    if request.headers.get("API-KEY") != "mysecret":
        return "Unauthorized", 403

    conn = get_db()
    cursor = conn.cursor()

    # Get file path before deleting
    cursor.execute("SELECT file_path, media_type FROM notices WHERE id=?", (notice_id,))
    row = cursor.fetchone()

    if row:
        file_path, media_type = row

        # Delete files if exist
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

    # Delete DB row
    cursor.execute("DELETE FROM notices WHERE id=?", (notice_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)