from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from PIL import Image
import io
import os
import zmq
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ZMQ Publisher setup
context = zmq.Context()
socket = context.socket(zmq.PUB)

try:
    socket.bind("tcp://*:5555")
    print("Flask ZMQ Publisher bound to tcp://*:5555")
except zmq.ZMQError as e:
    print(f"Port 5555 in use, trying 5556...")
    try:
        socket.bind("tcp://*:5556")
        print("Flask ZMQ Publisher bound to tcp://*:5556")
    except zmq.ZMQError as e2:
        print(f"ZMQ bind error: {e2}")
        print("Please check if another FlipDisk instance is running")

def send_command(command, **kwargs):
    """Send command to FlipDisk backend via ZMQ"""
    message = {'command': command, **kwargs}
    socket.send_string(json.dumps(message))
    print(f"Sent ZMQ message: {message}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/standby', methods=['POST'])
def standby():
    send_command('standby')
    flash('Standby mode forced!')
    return redirect(url_for('index'))

@app.route('/weather', methods=['POST'])
def weather():
    send_command('weather')
    flash('Weather mode forced!')
    return redirect(url_for('index'))

@app.route('/cycle', methods=['POST'])
def cycle():
    send_command('cycle')
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
        
        # Send image to FlipDisk backend
        send_command('image', image_path=os.path.abspath(save_path), folder=target_folder)
        
        # Remove the temporary file from uploads folder
        try:
            os.remove(img_path)
        except:
            pass
        flash(f'Image cropped and sent to FlipDisk!')
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

@app.route('/release', methods=['POST'])
def release_mode():
    send_command('release')
    flash('Released forced mode - automatic switching resumed!')
    return redirect(url_for('index'))

@app.route('/exit', methods=['POST'])
def exit_flipdisk():
    send_command('exit')
    flash('FlipDisk shutdown initiated!')
    return redirect(url_for('index'))

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)