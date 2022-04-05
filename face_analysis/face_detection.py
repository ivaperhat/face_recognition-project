from PIL import Image
from numpy import asarray

# Get face images from an image, return the number of faces found
def crop_face(img_array, face_location):
    top, right, bottom, left = face_location
    face_img = img_array[top:bottom, left:right]
    final = Image.fromarray(face_img)
    new_size = (150, 150)
    final = final.resize(new_size)
    final_array = asarray(final)
    face_img = final_array

    return face_img