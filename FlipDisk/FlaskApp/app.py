from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from PIL import Image
import io
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import zmq
import json
from Board import FDProcessing
from constants import boardSize
import cv2
import numpy as np

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Use absolute path for uploads folder relative to the project root
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ZMQ Publisher setup (for sending commands to backend)
context = zmq.Context()
socket = context.socket(zmq.PUB)

try:
    socket.bind("tcp://*:5555")
    print("Flask ZMQ Publisher bound to tcp://*:5555", flush=True)
except zmq.ZMQError as e:
    print(f"Port 5555 in use, trying 5556...", flush=True)
    try:
        socket.bind("tcp://*:5556")
        print("Flask ZMQ Publisher bound to tcp://*:5556", flush=True)
    except zmq.ZMQError as e2:
        print(f"ZMQ bind error: {e2}", flush=True)
        print("Please check if another FlipDisk instance is running", flush=True)

# ZMQ Subscriber setup (for receiving status from backend)
status_context = zmq.Context()
status_socket = status_context.socket(zmq.SUB)
status_socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages

# Global variable to store latest status
latest_status = {
    'current_mode': 'Unknown',
    'is_forced': False,
    'forced_mode': None,
    'timestamp': None
}

def status_listener():
    """Listen for status updates from backend"""
    global latest_status
    try:
        status_socket.connect("tcp://localhost:5557")
        print("Flask status subscriber connected to backend on port 5557", flush=True)
        
        while True:
            try:
                message = status_socket.recv_string(zmq.NOBLOCK)
                data = json.loads(message)
                latest_status = data
            except zmq.Again:
                # No message available
                pass
            except Exception as e:
                print(f"Status listener error: {e}", flush=True)
            time.sleep(0.1)
    except Exception as e:
        print(f"Failed to connect status listener: {e}", flush=True)

# Start status listener thread
import threading
import time
status_thread = threading.Thread(target=status_listener, daemon=True)
status_thread.start()

def send_command(command, **kwargs):
    """Send command to FlipDisk backend via ZMQ"""
    message = {'command': command, **kwargs}
    socket.send_string(json.dumps(message))
    print(f"Sent ZMQ message: {message}", flush=True)

def can_force_mode(target_mode_name):
    """
    Check if we can force a mode based on current system state
    Returns (allowed: bool, reason: str)
    """
    if latest_status is None:
        return False, "System status not available"
    
    current_mode = latest_status.get('current_mode', 'Unknown')
    is_forced = latest_status.get('is_forced', False)
    forced_mode = latest_status.get('forced_mode', None)
    
    # Check if already in the target mode and it's forced
    if is_forced and forced_mode == target_mode_name:
        return False, f"Already in forced {target_mode_name} mode"
    
    # Check if already in the target mode naturally (not forced)
    if current_mode == target_mode_name and not is_forced:
        return False, f"Already in {target_mode_name} mode"
    
    # Check if another mode is currently forced
    if is_forced and forced_mode != target_mode_name:
        return False, f"Another mode ({forced_mode}) is currently forced. Release it first."
    
    return True, "OK"


def process_image_for_board(image_path, processing_type='SimpleBW', size=None):
    """Process image for board display using FDProcessing functions"""
    try:
        img = Image.open(image_path)
        target_size = size if size is not None else boardSize
        
        if processing_type == 'SimpleBW':
            processed_img = FDProcessing.SimpleBW(img, target_size, invert=False)
        elif processing_type == 'EdgeDetection':
            processed_img = FDProcessing.EdgeDetection(img, target_size)
        elif processing_type == 'YoloSeg':
            processed_img = FDProcessing.yoloSeg(img, target_size)
        else:
            # Default to SimpleBW
            processed_img = FDProcessing.SimpleBW(img, target_size, invert=False)
        
        return processed_img
    except Exception as e:
        print(f"Error processing image: {e}", flush=True)
        return None

def cleanup_temp_images():
    """Clean up temporary images in uploads root and preview directories"""
    try:
        # Clean up files in the uploads root directory (not subdirectories)
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):  # Only delete files, not directories
                os.remove(file_path)
                print(f"Cleaned up: {file_path}", flush=True)
        
        # Clean up the preview directory completely
        preview_folder = os.path.join(UPLOAD_FOLDER, 'preview')
        if os.path.exists(preview_folder):
            for filename in os.listdir(preview_folder):
                file_path = os.path.join(preview_folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Cleaned up preview: {file_path}", flush=True)
        
        print("Temporary image cleanup completed", flush=True)
        
    except Exception as e:
        print(f"Error during cleanup: {e}", flush=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/standby', methods=['POST'])
def standby():
    allowed, reason = can_force_mode('StandbyMode')
    if not allowed:
        flash(f'Cannot force Standby mode: {reason}')
        return redirect(url_for('index'))
    
    send_command('standby', force=True)
    flash('Standby mode forced!')
    return redirect(url_for('index'))

@app.route('/weather', methods=['POST'])
def weather():
    allowed, reason = can_force_mode('WeatherMode')
    if not allowed:
        flash(f'Cannot force Weather mode: {reason}')
        return redirect(url_for('index'))
    
    send_command('weather', force=True)
    flash('Weather mode forced!')
    return redirect(url_for('index'))

@app.route('/cycle', methods=['POST'])
def cycle():
    allowed, reason = can_force_mode('CycleMode')
    if not allowed:
        flash(f'Cannot force Cycle mode: {reason}')
        return redirect(url_for('index'))
    
    # Clean up temporary images when starting cycle mode
    cleanup_temp_images()
    send_command('cycle', force=True)
    flash('Cycle mode forced! Temporary images cleared.')
    return redirect(url_for('index'))

@app.route('/release', methods=['POST'])
def release():
    if latest_status is None:
        flash('System status not available')
        return redirect(url_for('index'))
    
    is_forced = latest_status.get('is_forced', False)
    if not is_forced:
        flash('No mode is currently forced')
        return redirect(url_for('index'))
    
    send_command('release')
    flash('Released forced mode. Returning to automatic mode switching.')
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
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # For GIFs, save as binary to preserve animation
            if filename.lower().endswith('.gif'):
                file.save(file_path)
                print(f"Saved GIF as binary: {file_path}", flush=True)
            else:
                # For other images, use PIL processing as before
                img = Image.open(file.stream)
                img.save(file_path)
                print(f"Saved image via PIL: {file_path}", flush=True)
            
            return redirect(url_for('crop', filename=filename))
    return render_template('upload.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    print(f"Serving file: {filename} from {UPLOAD_FOLDER}", flush=True)
    full_path = os.path.join(UPLOAD_FOLDER, filename)
    print(f"Full path: {full_path}", flush=True)
    print(f"File exists: {os.path.exists(full_path)}", flush=True)
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/crop', methods=['GET', 'POST'])
def crop():
    filename = request.args.get('filename') if request.method == 'GET' else request.form.get('filename')
    
    if request.method == 'POST':
        # If GIF, skip cropping and go directly to preview with selected processing type
        if filename and filename.lower().endswith('.gif'):
            target_folder = request.form.get('target_folder', 'SimpleBW')
            return redirect(url_for('preview', filename=filename, target_folder=target_folder))
        
        # Regular image cropping logic
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
        
        # Save cropped image temporarily for preview
        preview_folder = os.path.join(UPLOAD_FOLDER, 'preview')
        os.makedirs(preview_folder, exist_ok=True)
        preview_path = os.path.join(preview_folder, filename)
        cropped.save(preview_path)
        
        # Remove the original temporary file from uploads folder
        try:
            os.remove(img_path)
        except:
            pass

        # Redirect to preview page instead of saving directly
        return redirect(url_for('preview', filename=filename, target_folder=target_folder))
    return render_template('crop.html', filename=filename)

@app.route('/preview')
def preview():
    filename = request.args.get('filename')
    target_folder = request.args.get('target_folder', 'SimpleBW')
    
    if not filename:
        flash('No image to preview')
        return redirect(url_for('upload'))
    
    # Check if this is a GIF that needs frame extraction
    if filename.lower().endswith('.gif'):
        # For GIFs, use the original file from uploads folder
        original_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(original_path):
            flash(f'Original GIF not found at {original_path}')
            return redirect(url_for('upload'))
        
        # Extract first frame from GIF
        try:
            gif_img = Image.open(original_path)
            gif_img.seek(0)  # Go to first frame
            first_frame = gif_img.convert('RGB')  # Convert to RGB for processing
            
            # Save the first frame to preview folder for processing
            preview_folder = os.path.join(UPLOAD_FOLDER, 'preview')
            os.makedirs(preview_folder, exist_ok=True)
            frame_filename = f"frame_{filename.replace('.gif', '.png')}"
            preview_path = os.path.join(preview_folder, frame_filename)
            first_frame.save(preview_path)
            print(f"Extracted first frame from GIF to: {preview_path}", flush=True)
        except Exception as e:
            flash(f'Error extracting frame from GIF: {e}')
            return redirect(url_for('upload'))
    else:
        # Get the cropped image path for regular images
        preview_path = os.path.join(UPLOAD_FOLDER, 'preview', filename)
        print(f"Preview path: {preview_path}", flush=True)
        print(f"Preview path exists: {os.path.exists(preview_path)}", flush=True)
        
        if not os.path.exists(preview_path):
            flash(f'Preview image not found at {preview_path}')
            return redirect(url_for('upload'))
    
    # Process the image at actual board size to see how it will really look
    board_processed_img = process_image_for_board(preview_path, target_folder, size=boardSize)
    
    if board_processed_img is None:
        flash('Error processing image for preview')
        return redirect(url_for('upload'))
    
    # Scale up the board-size image for display while maintaining pixelated look
    # Use nearest neighbor to keep sharp pixels
    scale_factor = 12  # Scale 28x28 to 336x336 for good visibility
    display_size = (boardSize[0] * scale_factor, boardSize[1] * scale_factor)
    display_img = board_processed_img.resize(display_size, Image.NEAREST)
    
    # Save the scaled preview
    processed_filename = f"processed_{filename}"
    processed_path = os.path.join(UPLOAD_FOLDER, 'preview', processed_filename)
    display_img.save(processed_path)
    print(f"Board preview saved to: {processed_path} (scaled from {boardSize} to {display_size})", flush=True)
    
    return render_template('preview.html', 
                         filename=filename, 
                         processed_filename=processed_filename,
                         target_folder=target_folder,
                         board_size=boardSize)

@app.route('/confirm_image', methods=['POST'])
def confirm_image():
    filename = request.form.get('filename')
    target_folder = request.form.get('target_folder', 'SimpleBW')
    
    if not filename:
        flash('No image to confirm')
        return redirect(url_for('upload'))
    
    save_folder = os.path.join(UPLOAD_FOLDER, target_folder)
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, filename)
    
    try:
        import shutil
        
        # Handle GIFs differently - use original file
        if filename.lower().endswith('.gif'):
            # For GIFs, copy the original unmodified file using binary copy
            original_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(original_path):
                # Use binary copy to preserve the GIF exactly as is
                with open(original_path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                print(f"Binary copied original GIF from {original_path} to {save_path}", flush=True)
            else:
                flash('Original GIF file not found')
                return redirect(url_for('upload'))
        else:
            # For regular images, use the cropped version from preview
            preview_path = os.path.join(UPLOAD_FOLDER, 'preview', filename)
            shutil.copy2(preview_path, save_path)
        
        # Send image to FlipDisk backend
        send_command('image', image_path=filename, folder=target_folder)
        
        # Clean up preview files
        try:
            if filename.lower().endswith('.gif'):
                # For GIFs, remove the original uploaded file and extracted frame
                original_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(original_path):
                    os.remove(original_path)
                # Remove extracted frame if it exists
                frame_filename = f"frame_{filename.replace('.gif', '.png')}"
                frame_path = os.path.join(UPLOAD_FOLDER, 'preview', frame_filename)
                if os.path.exists(frame_path):
                    os.remove(frame_path)
            else:
                # For regular images, remove the cropped preview
                preview_path = os.path.join(UPLOAD_FOLDER, 'preview', filename)
                if os.path.exists(preview_path):
                    os.remove(preview_path)
            
            # Always clean up the processed preview
            processed_preview_path = os.path.join(UPLOAD_FOLDER, 'preview', f"processed_{filename}")
            if os.path.exists(processed_preview_path):
                os.remove(processed_preview_path)
        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}", flush=True)
        
        flash(f'Image confirmed and sent to FlipDisk!')
        return redirect(url_for('upload'))
        
    except Exception as e:
        flash(f'Error confirming image: {e}')
        return redirect(url_for('upload'))

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

@app.route('/status')
def get_status():
    """Return current backend status as JSON"""
    return json.dumps(latest_status)

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)