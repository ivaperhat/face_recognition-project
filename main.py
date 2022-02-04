import face_recognition
import pickle
import MySQLdb
import db_statements as st


# Connect to Database (https://www.clever-cloud.com/)
connection = MySQLdb.connect(host="b97ulbrnkhrhixtxfcii-mysql.services.clever-cloud.com",
                             user="u52rwvwh0rmc0i50",
                             passwd="33iXkQ0rI0nyTR1EQbu0",
                             db="b97ulbrnkhrhixtxfcii")

# Create a cursor for interacting
cursor = connection.cursor()


# Add record to the database
def add_record(name, face_encodings):
    if find_match(face_encodings):  # Person is already in the database
        return False
    else:  # Add to the database
        cursor.execute(st.faces_insert_NAME_ENCODINGS, (name, pickle.dumps(face_encodings)))
        return True


# Delete record from database
def delete_record(face_id):
    cursor.execute(st.faces_exists_ID, face_id)
    if cursor.fetchone()[0] == 1:  # If record exists
        cursor.execute(st.faces_delete_ID, face_id)
        return True
    else:
        return False


# Get face encodings from an image
def get_face_encodings(image):
    face_image = face_recognition.load_image_file(image)
    encodings = face_recognition.face_encodings(face_image)[0]
    return encodings


# Check if two faces match
def face_match(face_encodings1, face_encodings2):
    result = face_recognition.compare_faces([face_encodings1], face_encodings2)
    return result[0]


# Get 'distance' between two faces
def face_distance(face_encodings1, face_encodings2):
    distance = face_recognition.face_distance([face_encodings1], face_encodings2)
    return distance[0]


# Search for a match in the database
def find_match(face_encodings):
    match_found = False
    cursor.execute(st.faces_select)
    rows = cursor.fetchall()
    for row in rows:
        if face_match(pickle.loads(row[2]), face_encodings) == 1:
            match_found = True
            return row[0]
    if match_found == 0:  # If match is not found
        return False


# Find match with lowest face distance
def find_closest_match(face_encodings):
    lowest_distance = 1
    lowest_distance_id = ""
    cursor.execute(st.faces_select)
    rows = cursor.fetchall()
    for row in rows:
        current_distance = face_distance(pickle.loads(row[2]), face_encodings)
        if current_distance <= lowest_distance:
            lowest_distance = current_distance
            lowest_distance_id = row[0]
    return lowest_distance_id, lowest_distance


connection.commit()
connection.close()
