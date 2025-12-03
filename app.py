from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
from models.face_detector import FaceRecognizer
from models.liveness_detector import LivenessDetector

app = Flask(__name__)
face_recognizer = FaceRecognizer()
liveness_detector = LivenessDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth', methods=['POST'])
def authenticate():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    image = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # Liveness check first
    if not liveness_detector.is_live(image):
        return jsonify({'status': 'failed', 'reason': 'Liveness failed'})

    # Face recognition
    identity = face_recognizer.recognize(image)
    if identity:
        return jsonify({'status': 'success', 'user': identity})
    return jsonify({'status': 'failed', 'reason': 'Unknown face'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
