import io
import pickle
from PIL import Image
import data_access.connections as conn
import face_analysis.face_detection as detect
import pytz
import datetime
from datetime import datetime, timedelta
import data_access.SQL_statements as sql


# Set a new name for the face record
def set_name(new_name, face_id):
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()
    cursor.execute(sql.SET_NAME, (new_name, face_id,))
    mysql_connection.commit()
    mysql_connection.close()


def add_face_record(face_id, name, face_encodings, age, gender, frame, face_location):
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    bucket_name = "face-recognition-faces"
    img_path = "faces/" + face_id + ".jpg"

    face_img = detect.crop_face(frame, face_location)
    img = Image.fromarray(face_img)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    # Add Database Record
    cursor.execute(sql.FACES_INSERT, (face_id, name, pickle.dumps(face_encodings), img_path, age, gender,))

    # Add photo to the S3 bucket
    conn.client.upload_fileobj(io.BytesIO(img_byte_arr), bucket_name, img_path,
                               ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpeg'})

    mysql_connection.commit()
    mysql_connection.close()


# Delete record from database
def delete_record(face_id):
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()
    cursor.execute(sql.FACES_EXISTS, (face_id,))
    if cursor.fetchone()[0] == 1:  # If record exists
        cursor.execute(sql.FACES_SELECT_IMG, (face_id,))
        img_id = cursor.fetchone()[0]

        cursor.execute(sql.FACES_DELETE_RECORD, (face_id,))  # Delete database record
        cursor.execute(sql.DELETE_VISITS_BY_ID, (face_id,))  # Delete all associated visits
        conn.client.delete_object(Bucket='face-recognition-faces', Key=img_id)  # Delete photo file
        mysql_connection.commit()
        mysql_connection.close()
        return True
    else:
        return False


def add_visit_record(face_id, time):
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    cursor.execute(sql.VISITS_INSERT, (face_id, time,))
    mysql_connection.commit()
    mysql_connection.close()


def visits_data():
    db_connection = conn.mysql_connection()
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql.VISITS_SELECT_ALL)
    rows = db_cursor.fetchall()

    visit_ids = []
    face_ids = []
    times = []
    for row in rows:
        visit_ids.append(row[0])
        face_ids.append(row[1])
        times.append(row[2])

    db_connection.close()

    return visit_ids, face_ids, times


def get_face_record(face_id):
    db_connection = conn.mysql_connection()
    # Create a cursor for interacting
    db_cursor = db_connection.cursor()

    db_cursor.execute(sql.GET_FACE_RECORD, (face_id,))
    row = db_cursor.fetchone()

    if row != None:
        name = row[0]
        face_encodings = pickle.loads(row[1])
        img_id = row[2]
        age = row[3]
        gender = row[4]
        db_connection.close()
        return name, face_encodings, img_id, age, gender

    else:
        db_connection.close()
        return []


def delete_all_visit_records():
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    cursor.execute(sql.DELETE_ALL_VISIT_RECORDS)

    mysql_connection.commit()
    mysql_connection.close()


def face_records():
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    face_records = []
    cursor.execute(sql.FACES_SELECT_ALL)
    rows = cursor.fetchall()
    for row in rows:
        face_record = (row[0], row[1], pickle.loads(row[2]), row[3], row[4], row[5])
        face_records.append(face_record)

    mysql_connection.close()
    return face_records


def face_record_exists(face_id):
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    cursor.execute(sql.FACES_EXISTS, (face_id,))

    if cursor.fetchone()[0] == 1:
        mysql_connection.close()
        return True
    else:
        mysql_connection.close()
        return False


# Get top 10 visitors with most appearances
def frequent_visitors():
    mysql_connection = conn.mysql_connection()
    cursor = mysql_connection.cursor()

    cursor.execute(sql.TOP_TEN_VISITORS)
    rows = cursor.fetchall()

    frequent_visitors = []
    for row in rows:
        frequent_visitor = (row[0], row[1], pickle.loads(row[2]))
        frequent_visitors.append(frequent_visitor)

    mysql_connection.close()
    return frequent_visitors

# Get all visit records
def visit_records():
    db_connection = conn.mysql_connection()
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql.VISITS_SELECT_ALL)
    rows = db_cursor.fetchall()

    visit_records = []

    for row in rows:
        visit_record = (row[0], row[1], row[2], row[3], pickle.loads(row[4]))
        visit_records.append(visit_record)

    db_connection.close()
    return visit_records

# All visitors from last 10 minutes
def recent_visitors():
    all_visit_records = visit_records()
    recent_visitors = []

    tz = pytz.timezone('Europe/London')

    for visit_record in all_visit_records:
        visit_time = tz.localize(visit_record[1])
        face_id = visit_record[2]
        name = visit_record[3]
        face_encodings = visit_record[4]

        record_tuple = (face_id, name, face_encodings, visit_time)
        recent_visitors.append(record_tuple)

    result = find_recent(recent_visitors)

    return result

def find_recent(visitors_list):
    tz = pytz.timezone('Europe/London')
    recent_visitors = []

    for visitor_record in visitors_list:
        if visitor_record[3] and visitor_record[3] > datetime.now(tz) - timedelta(minutes=10):
            face_id = visitor_record[0]
            name = visitor_record[1]
            face_encodings = visitor_record[2]
            visit_time = visitor_record[3]

            recent_visitor_tuple = (face_id, name, face_encodings, visit_time)
            recent_visitors.append(recent_visitor_tuple)
        else:
            break

    return recent_visitors