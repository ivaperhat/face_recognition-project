import cv2
import numpy as np
from PIL import Image
from numpy import asarray


# Get face blob from an image
def get_face_blob(img_array, face_location):
    top, right, bottom, left = face_location

    face_img = img_array[top:bottom, left:right]
    final = Image.fromarray(face_img)
    final = final.resize((224, 224))
    detected_face_blob = cv2.dnn.blobFromImage(asarray(final))
    return detected_face_blob  # Returns an array list of face images


# Detect Age
def detect_age(img_array, face_location):
    age_model = cv2.dnn.readNetFromCaffe("age.prototxt", "dex_chalearn_iccv2015.caffemodel")
    detected_face_blob = get_face_blob(img_array, face_location)

    age_model.setInput(detected_face_blob)
    age_result = age_model.forward()

    indexes = np.array([i for i in range(0, 101)])
    detected_age = round(np.sum(age_result[0] * indexes))

    return detected_age


# Detect Gender
def detect_gender(img_array, face_location):
    gender_model = cv2.dnn.readNetFromCaffe("gender.prototxt", "gender.caffemodel")
    detected_face_blob = get_face_blob(img_array, face_location)

    gender_model.setInput(detected_face_blob)
    gender_result = gender_model.forward()

    if np.argmax(gender_result[0]) == 0:
        return "f"
    else:
        return "m"
