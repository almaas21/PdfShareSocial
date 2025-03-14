import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pdf2image import convert_from_bytes
from PIL import Image
import cv2
import numpy as np
import io
import tempfile
from utils.image_processor import process_image

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf'}
TEMP_FOLDER = tempfile.gettempdir()
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400

        # Read PDF file
        pdf_bytes = file.read()
        if len(pdf_bytes) > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds maximum limit of 10MB'}), 400

        # Convert PDF to images
        images = convert_from_bytes(pdf_bytes)

        # Convert images to base64 for preview
        image_data = []
        for i, image in enumerate(images):
            # Resize image to Instagram dimensions (1080x1080)
            image = image.resize((1080, 1080), Image.LANCZOS)

            # Save image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Convert to base64
            import base64
            image_data.append({
                'id': i,
                'data': base64.b64encode(img_byte_arr).decode('utf-8')
            })

        return jsonify({'images': image_data})

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({'error': 'Error processing PDF file'}), 500

@app.route('/process_image', methods=['POST'])
def process_image_endpoint():
    try:
        data = request.json
        image_data = data.get('image')
        operations = data.get('operations', {})

        # Get image data from base64
        import base64
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Process image using the utility function
        processed_bytes = process_image(image_bytes, operations)

        # Convert back to base64
        processed_image = base64.b64encode(processed_bytes).decode('utf-8')

        return jsonify({'processed_image': processed_image})

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': 'Error processing image'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)