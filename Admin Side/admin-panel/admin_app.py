from flask import Flask, render_template, request, redirect, flash
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

BASE_URL = "http://192.168.137.251:5000"
API_KEY = "mysecret"

HEADERS = {"API-KEY": API_KEY}

# ---------------- HOME (UPLOAD PAGE) ----------------
@app.route('/')
def index():
    return render_template('admin.html')


# ---------------- CREATE (UPLOAD) ----------------
@app.route('/upload', methods=['POST'])
def upload():
    try:
        media_type = request.form['media_type']
        title = request.form['title']
        duration = request.form.get('duration', 20)

        data = {
            "title": title,
            "media_type": media_type,
            "duration": duration
        }

        # -------- TEXT --------
        if media_type == 'text':
            data["content"] = request.form['content']

            response = requests.post(
                f"{BASE_URL}/upload",
                data=data,
                headers=HEADERS
            )

        # -------- IMAGE / VIDEO --------
        elif media_type in ['image', 'video']:
            file = request.files['file']

            if file.filename == "":
                flash("No file selected")
                return redirect('/')

            files = {
                "file": (file.filename, file.stream, file.mimetype)
            }

            response = requests.post(
                f"{BASE_URL}/upload",
                data=data,
                files=files,
                headers=HEADERS
            )

        # -------- SLIDESHOW --------
        elif media_type == 'slideshow':
            uploaded_files = request.files.getlist('files')

            if not uploaded_files or uploaded_files[0].filename == "":
                flash("No files selected for slideshow")
                return redirect('/')

            files = []
            for file in uploaded_files:
                files.append(
                    ("files", (file.filename, file.stream, file.mimetype))
                )

            response = requests.post(
                f"{BASE_URL}/upload",
                data=data,
                files=files,
                headers=HEADERS
            )

        else:
            flash("Invalid media type")
            return redirect('/')

        if response.status_code == 200:
            flash("✅ Upload successful!")
        else:
            flash(f"❌ Upload failed: {response.text}")

    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect('/')


# ---------------- READ (VIEW ALL NOTICES) ----------------
@app.route('/view')
def view():
    try:
        response = requests.get(f"{BASE_URL}/notices", headers=HEADERS)

        if response.status_code == 200:
            notices = response.json()
        else:
            notices = []
            flash("❌ Failed to fetch notices")

    except Exception as e:
        notices = []
        flash(f"⚠️ Error: {str(e)}")

    return render_template('view.html', notices=notices)


# ---------------- DELETE ----------------
@app.route('/delete/<int:notice_id>')
def delete(notice_id):
    try:
        response = requests.delete(
            f"{BASE_URL}/delete/{notice_id}",
            headers=HEADERS
        )

        if response.status_code == 200:
            flash("🗑️ Deleted successfully")
        else:
            flash("❌ Delete failed")

    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect('/view')


# ---------------- UPDATE ----------------
@app.route('/update/<int:notice_id>', methods=['GET', 'POST'])
def update(notice_id):
    if request.method == 'POST':
        try:
            data = {
                "title": request.form['title'],
                "content": request.form.get('content'),
                "duration": request.form.get('duration')
            }

            response = requests.post(
                f"{BASE_URL}/update/{notice_id}",
                data=data,
                headers=HEADERS
            )

            if response.status_code == 200:
                flash("✏️ Updated successfully")
            else:
                flash("❌ Update failed")

        except Exception as e:
            flash(f"⚠️ Error: {str(e)}")

        return redirect('/view')

    return render_template('update.html', notice_id=notice_id)


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)