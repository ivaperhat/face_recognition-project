import data_access as da
import face_recognition
import pickle
import MySQLdb
import uuid
import boto3

# Connect to S3 Bucket (https://www.aws.amazon.com/)
client = boto3.client('s3',
                      aws_access_key_id=da.ACCESS_KEY,
                      aws_secret_access_key=da.SECRET_ACCESS_KEY)

# Connect to Database (https://www.clever-cloud.com/)
connection = MySQLdb.connect(host=da.HOSTNAME,
                             user=da.USER,
                             passwd=da.PASSWORD,
                             db=da.DATABASE)

# Create a cursor for interacting
cursor = connection.cursor()


# Get face encodings from an image
def get_face_encodings(img):
    face_image = face_recognition.load_image_file(img)
    encodings = face_recognition.face_encodings(face_image)[0]
    return encodings


# Check if two faces match
def face_match(img1, img2):
    face_encodings1 = get_face_encodings(img1)
    face_encodings2 = get_face_encodings(img2)
    result = face_recognition.compare_faces([face_encodings1], face_encodings2)
    return result[0]


# Get 'distance' between two faces
def face_distance(img1, img2):
    face_encodings1 = get_face_encodings(img1)
    face_encodings2 = get_face_encodings(img2)
    distance = face_recognition.face_distance([face_encodings1], face_encodings2)
    return distance[0]


# Search for a match in the database
def find_match(img):
    face_encodings = get_face_encodings(img)
    cursor.execute(da.faces_select_ALL)
    rows = cursor.fetchall()
    for row in rows:
        if face_match(pickle.loads(row[2]), face_encodings) == 1:
            return row[0]
        else:
            return False


# Find match with lowest face distance
def find_closest_match(face_encodings):
    lowest_distance = 1
    lowest_distance_id = ""
    cursor.execute(da.faces_select_ALL)
    rows = cursor.fetchall()
    for row in rows:
        current_distance = face_distance(pickle.loads(row[2]), face_encodings)
        if current_distance <= lowest_distance:
            lowest_distance = current_distance
            lowest_distance_id = row[0]
    return lowest_distance_id, lowest_distance


# Add record to the database
def add_record_w_image(name, img):
    face_encodings = get_face_encodings(img)

    if find_match(face_encodings):  # Person is already in the database
        return False
    else:  # Add to the database
        unique_id = uuid.uuid4()
        key = "faces/" + str(unique_id) + ".jpg"
        bucket_name = "faces-db-bucket"

        # Add record to the MySQL database
        cursor.execute(da.faces_insert_NAME_ENCODINGS_IMG,
                       (name, pickle.dumps(face_encodings), unique_id))
        # Add photo to the S3 bucket
        client.upload_file(img, bucket_name, key, ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})

        return True


# Delete record from database
def delete_record(face_id):
    cursor.execute(da.faces_exists_ID, face_id)
    if cursor.fetchone()[0] == 1:  # If record exists
        cursor.execute(da.faces_select_IMG, face_id)
        img_id = cursor.fetchone()[0]
        key = "faces/" + img_id + ".jpg"

        cursor.execute(da.faces_delete_ID, face_id)  # Delete database record
        client.delete_object(Bucket='faces-db-bucket', Key=key)  # Delete photo file
        return True
    else:
        return False


connection.commit()
connection.close()
