from flask import Flask, render_template, request, redirect, flash
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"   # needed for flash messages

# 👉 CHANGE THIS to your Raspberry Pi IP / public URL
PI_URL = "http://192.168.137.251:5000/upload"

# 👉 API key must match Raspberry Pi app.py
API_KEY = "mysecret"

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('admin.html')

# ---------------- UPLOAD ----------------
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

        headers = {
            "API-KEY": API_KEY
        }

        # -------- TEXT --------
        if media_type == 'text':
            data["content"] = request.form['content']

            response = requests.post(
                PI_URL,
                data=data,
                headers=headers
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
                PI_URL,
                data=data,
                files=files,
                headers=headers
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
                PI_URL,
                data=data,
                files=files,
                headers=headers
            )

        else:
            flash("Invalid media type")
            return redirect('/')

        # -------- RESPONSE CHECK --------
        if response.status_code == 200:
            flash("✅ Upload successful!")
        else:
            flash(f"❌ Upload failed: {response.text}")

    except Exception as e:
        flash(f"⚠️ Error: {str(e)}")

    return redirect('/')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)