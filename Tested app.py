import os
import sqlite3
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

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

# ------------------ UPLOAD API ------------------
@app.route('/upload', methods=['POST'])
def upload():
    # simple security
    print("REQUEST RECEIVED")
    print("FORM DATA:",request.form)
    print("FILES:",request.files)
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

    return jsonify({"status": "success"})

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)