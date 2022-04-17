import os
from typing import List

import cv2
import face_recognition
import numpy as np

from network.config import FACES_DIR


def encode_faces():
    known_face_encodings = []
    known_face_names = []
    for face_name in os.listdir(FACES_DIR):
        face = face_recognition.load_image_file(os.path.join(FACES_DIR, face_name))
        face_encoding = face_recognition.face_encodings(face)[0]
        known_face_encodings.append(face_encoding)
        known_face_names.append(face_name[:face_name.rfind(".")])
    return known_face_encodings, known_face_names


KNOWN_FACES, KNOWN_NAMES = encode_faces()


def annotate_image(image, face_locations, face_names):
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        if name != "Unknown":
            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        else:
            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)

        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(image, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    return image, face_names


def detect_faces(frame: np.ndarray,
                 known_face_encodings: List = KNOWN_FACES,
                 known_face_names: List = KNOWN_NAMES
                 ) -> np.ndarray:
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    face_locations = face_recognition.face_locations(small_frame)

    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        face_names.append(name)

    annotated_image, result = annotate_image(frame, face_locations, face_names)

    return annotated_image
