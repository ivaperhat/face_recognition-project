import os
import pickle
import uuid
from PIL import Image
import face_analysis.recognition_functions as fr
import data_access.SQL_statements as st
import data_access.connection as conn

# Create a cursor for interacting
cursor = conn.connection.cursor()


# Add record to the database
def add_record(name, img_array):
    if fr.count_faces(img_array) == 1:
        face_encodings = fr.get_face_encodings(img_array)

        if fr.find_match(img_array):  # Person is already in the database
            return False
        else:  # Add to the database
            unique_id = uuid.uuid4()
            key = "faces/" + str(unique_id) + ".jpg"
            bucket_name = "faces-db-bucket"

            new_img = Image.fromarray(fr.crop_faces(img_array)[0])
            new_img.save("saving.jpg")

            # Add record to the MySQL database
            cursor.execute(st.FACES_INSERT, (name, pickle.dumps(face_encodings), unique_id))
            # Add photo to the S3 bucket
            conn.client.upload_file("saving.jpg", bucket_name, key,
                                  ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})
            os.remove("saving.jpg")

            return True
    else:
        return False


# Delete record from database
def delete_record(face_id):
    cursor.execute(st.FACES_EXISTS, (face_id,))
    if cursor.fetchone()[0] == 1:  # If record exists
        cursor.execute(conn.FACES_SELECT_IMG, (face_id,))
        img_id = cursor.fetchone()[0]
        key = "faces/" + img_id + ".jpg"

        cursor.execute(st.FACES_DELETE_RECORD, (face_id,))  # Delete database record
        conn.client.delete_object(Bucket='faces-db-bucket', Key=key)  # Delete photo file
        return True
    else:
        return False
