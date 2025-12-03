import face_recognition
import cv2
import pickle
import os

class FaceRecognizer:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.load_encodings()

    def load_encodings(self):
        if os.path.exists('encodings.pickle'):
            with open('encodings.pickle', 'rb') as f:
                data = pickle.load(f)
                self.known_encodings = data['encodings']
                self.known_names = data['names']

    def recognize(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        for encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=0.5)
            if True in matches:
                match_index = matches.index(True)
                return self.known_names[match_index]
        return None
