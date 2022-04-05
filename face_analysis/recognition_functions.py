import uuid
import os
import face_recognition
import pickle
from PIL import Image
from numpy import asarray
import data_access.SQL_statements as st


def get_img_array(img_path):
    return face_recognition.load_image_file(img_path)


# Count faces in a photo
def count_faces(img_array):
    faces = face_recognition.face_locations(img_array)
    return len(faces)  # Returns the number of detected faces


# Get face images from an image, return the number of faces found
def crop_faces(img_array):
    images = []
    faces = face_recognition.face_locations(img_array)

    for i in range(len(faces)):  # For each face detected
        top, right, bottom, left = faces[i]

        face_img = img_array[top:bottom, left:right]
        final = Image.fromarray(face_img)
        new_size = (150, 150)
        final = final.resize(new_size)
        final_array = asarray(final)
        images.append(final_array)

    return images  # Returns an array list of face images


# Get face encodings from an image
def get_face_encodings(img_array):
    if count_faces(img_array) == 1:  # Check if the image only contains one face
        encodings = face_recognition.face_encodings(img_array)[0]
        return encodings
    else:
        return False


# Check if two faces match
def face_match(face_encodings1, face_encodings2):
    result = face_recognition.compare_faces([face_encodings1], face_encodings2)
    return result[0]


# Get 'distance' between two faces
def face_distance(face_encodings1, face_encodings2):
    distance = face_recognition.face_distance([face_encodings1], face_encodings2)
    return distance[0]
