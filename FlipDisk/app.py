from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from PIL import Image
import io
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/standby', methods=['POST'])
def standby():
    print('force standby')
    flash('Standby mode forced!')
    return redirect(url_for('index'))

@app.route('/weather', methods=['POST'])
def weather():
    print('force weather')
    flash('Weather mode forced!')
    return redirect(url_for('index'))

@app.route('/cycle', methods=['POST'])
def cycle():
    print('force cycle')
    flash('Cycle mode forced!')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            img = Image.open(file.stream)
            filename = file.filename
            # Save to temporary uploads folder for cropping
            img.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('crop', filename=filename))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/crop', methods=['GET', 'POST'])
def crop():
    filename = request.args.get('filename') if request.method == 'GET' else request.form.get('filename')
    if request.method == 'POST':
        x = int(request.form['x'])
        y = int(request.form['y'])
        size = int(request.form['size'])
        img_display_w = int(request.form['img_display_w'])
        img_display_h = int(request.form['img_display_h'])
        target_folder = request.form.get('target_folder', 'SimpleBW')
        img_path = os.path.join(UPLOAD_FOLDER, filename)
        img = Image.open(img_path)
        orig_w, orig_h = img.size
        scale_x = orig_w / img_display_w
        scale_y = orig_h / img_display_h
        x_scaled = int(x * scale_x)
        y_scaled = int(y * scale_y)
        size_scaled = int(size * min(scale_x, scale_y))
        cropped = img.crop((x_scaled, y_scaled, x_scaled + size_scaled, y_scaled + size_scaled))
        # Save to selected folder
        save_folder = os.path.join(UPLOAD_FOLDER, target_folder)
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, filename)
        cropped.save(save_path)
        # Remove the temporary file from uploads folder
        try:
            os.remove(img_path)
        except:
            pass
        flash(f'Image cropped and will be processed using {target_folder}!')
        return redirect(url_for('upload'))
    return render_template('crop.html', filename=filename)

@app.route('/rotate', methods=['POST'])
def rotate():
    filename = request.form.get('filename')
    img_path = os.path.join(UPLOAD_FOLDER, filename)
    img = Image.open(img_path)
    rotated = img.rotate(-90, expand=True)  # -90 for clockwise rotation
    rotated.save(img_path)
    return redirect(url_for('crop', filename=filename))

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='10.0.0.143', port=5000, debug=True)
