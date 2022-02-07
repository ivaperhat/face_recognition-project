import uuid
import os
import data_access as da
import face_recognition
import pickle
from PIL import Image
from numpy import asarray

# Create a cursor for interacting
cursor = da.connection.cursor()


# Count faces in a photo
def count_faces(img_array):
    faces = face_recognition.face_locations(img_array)
    return len(faces)  # Returns the number of detected faces


print("COUNT FACES: ")
print(count_faces(face_recognition.load_image_file("beatles.jpg")))


# Get face images from an image, return the number of faces found
def crop_faces(img_array):
    images = []
    faces = face_recognition.face_locations(img_array)

    for i in range(len(faces)):
        top, right, bottom, left = faces[i]

        face_img = img_array[top:bottom, left:right]
        final = Image.fromarray(face_img)
        new_size = (150, 150)
        final = final.resize(new_size)
        final_array = asarray(final)
        images.append(final_array)

    return images  # Returns an array list of face images


print("CROP FACES: ")
print(crop_faces(face_recognition.load_image_file("beatles.jpg")))


# Get face encodings from an image
def get_face_encodings(img_array):
    if count_faces(img_array) == 1:
        encodings = face_recognition.face_encodings(img_array)[0]
        return encodings
    else:
        return False


print("GET_FACE_ENCODINGS:")
print(get_face_encodings(face_recognition.load_image_file("miley_cyrus1.jpg")))


# Check if two faces match
def face_match(face_encodings1, face_encodings2):
    result = face_recognition.compare_faces([face_encodings1], face_encodings2)
    return result[0]


print("FACE_MATCH: ")
print(face_match(get_face_encodings(face_recognition.load_image_file("miley_cyrus1.jpg")),
                 get_face_encodings(face_recognition.load_image_file("miley_cyrus2.jpg"))))


# Get 'distance' between two faces
def face_distance(face_encodings1, face_encodings2):
    distance = face_recognition.face_distance([face_encodings1], face_encodings2)
    return distance[0]


print("FACE_DISTANCE: ")
print(face_distance(get_face_encodings(face_recognition.load_image_file("miley_cyrus1.jpg")),
                    get_face_encodings(face_recognition.load_image_file("miley_cyrus2.jpg"))))


# Search for a match in the database
def find_match(img_array):
    face_encodings = get_face_encodings(img_array)
    cursor.execute(da.FACES_SELECT_ALL)
    rows = cursor.fetchall()
    match_id = ""
    for row in rows:
        if face_match(pickle.loads(row[2]), face_encodings):
            match_id = row[0]

    if match_id == "":
        return False
    else:
        return match_id


print("FIND_MATCH:")
print(find_match(face_recognition.load_image_file("miley_cyrus1.jpg")))


# Find match with lowest face distance
def find_closest_match(face_encodings):
    lowest_distance = 1
    lowest_distance_id = ""
    cursor.execute(da.FACES_SELECT_ALL)
    rows = cursor.fetchall()
    for row in rows:
        current_distance = face_distance(pickle.loads(row[2]), face_encodings)
        if current_distance <= lowest_distance:
            lowest_distance = current_distance
            lowest_distance_id = row[0]
    return lowest_distance_id, lowest_distance


print("FIND_CLOSEST MATCH: ")
print(find_closest_match(get_face_encodings(face_recognition.load_image_file("miley_cyrus1.jpg"))))


# Add record to the database
def add_record(name, img_array):
    if count_faces(img_array) == 1:
        face_encodings = get_face_encodings(img_array)

        if find_match(img_array):  # Person is already in the database
            return False
        else:  # Add to the database
            unique_id = uuid.uuid4()
            key = "faces/" + str(unique_id) + ".jpg"
            bucket_name = "faces-db-bucket"

            new_img = Image.fromarray(crop_faces(img_array)[0])
            new_img.save("saving.jpg")

            # Add record to the MySQL database
            cursor.execute(da.FACES_INSERT, (name, pickle.dumps(face_encodings), unique_id))
            # Add photo to the S3 bucket
            da.client.upload_file("saving.jpg", bucket_name, key,
                                  ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})
            os.remove("saving.jpg")

            return True
    else:
        return False


print("ADD_RECORD: ")
print(add_record("Miley", face_recognition.load_image_file("miley_cyrus1.jpg")))


# Delete record from database
def delete_record(face_id):
    cursor.execute(da.FACES_EXISTS, (face_id,))
    if cursor.fetchone()[0] == 1:  # If record exists
        cursor.execute(da.FACES_SELECT_IMG, (face_id,))
        img_id = cursor.fetchone()[0]
        key = "faces/" + img_id + ".jpg"

        cursor.execute(da.FACES_DELETE_RECORD, (face_id,))  # Delete database record
        da.client.delete_object(Bucket='faces-db-bucket', Key=key)  # Delete photo file
        return True
    else:
        return False


print("DELETE_RECORD: ")
print(delete_record("15"))


da.connection.commit()
da.connection.close()
