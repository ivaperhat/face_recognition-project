import cv2
import numpy as np


# Get face blob from an image
def get_face_blob(img_path):
    img = cv2.imread(img_path)

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = detector.detectMultiScale(img, 1.3, 5)  # Detect face

    if len(faces) == 1:  # If one face was detected
        x, y, w, h = faces[0]
        detected_face = img[int(y):int(y + h), int(x):int(x + w)]
        detected_face = cv2.resize(detected_face, (224, 224))
        detected_face_blob = cv2.dnn.blobFromImage(detected_face)
        return detected_face_blob
    else:
        return False


# Detect Gender
def detect_gender(img_path):
    detected_face_blob = get_face_blob(img_path)

    gender_model = cv2.dnn.readNetFromCaffe("gender.prototxt", "gender.caffemodel")
    gender_model.setInput(detected_face_blob)
    gender_result = gender_model.forward()

    if np.argmax(gender_result[0]) == 0:
        return "F"
    else:
        return "M"


# Detect Age
def detect_age(img_path):
    detected_face_blob = get_face_blob(img_path)

    age_model = cv2.dnn.readNetFromCaffe("age.prototxt", "dex_chalearn_iccv2015.caffemodel")
    age_model.setInput(detected_face_blob)
    age_result = age_model.forward()

    indexes = np.array([i for i in range(0, 101)])
    detected_age = round(np.sum(age_result[0] * indexes))

    return detected_age
