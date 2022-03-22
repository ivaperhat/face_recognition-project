import multiprocessing
import threading
import time
import uuid
import cv2
from multiprocessing import Manager, Process, Queue, Lock
import face_recognition
import data_access.db_records as records
from datetime import datetime
import data_access.connection as conn
import face_analysis.facial_attribute_analysis as fae


def get_frame(frames_to_process_queue, camera_id):
    frame_rate = 2
    prev = 0
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # Video capture
    while (True):
        time_elapsed = time.time() - prev
        ret, frame = cap.read()  # Return a single frame

        if time_elapsed > 1./frame_rate:
            prev = time.time()
            frames_to_process_queue.put((camera_id, frame, datetime.now()))


def process_unknowns(unknowns_to_process_queue, Global):
    while not Global.is_exit:
        if not unknowns_to_process_queue.empty():
            unknown_face_tuple = unknowns_to_process_queue.get()
            face_id = unknown_face_tuple[0]
            frame = unknown_face_tuple[1]
            face_location = unknown_face_tuple[2]
            face_encoding = unknown_face_tuple[3]

            detected_age = fae.detect_age_new(frame, face_location)
            detected_gender = fae.detect_gender_new(frame, face_location)

            records.add_new_record(face_id, "Unknown", [face_encoding], detected_age, detected_gender, frame, face_location)
            print("db record added")
            conn.connection.commit()


def process_visitors(visitors_to_process_queue, Global):
    while not Global.is_exit:
        if not visitors_to_process_queue.empty():
            face_record = visitors_to_process_queue.get()
            face_id = face_record[0]

            records.add_visit_record(face_id, str(datetime.now()))
            conn.connection.commit()

            print("visitor record added")


def add_records(visitors_to_process_queue, unknowns_to_process_queue, Global):
    visitors_thread = threading.Thread(target=process_visitors, args=(visitors_to_process_queue, Global,))
    visitors_thread.start()

    unknowns_thread = threading.Thread(target=process_unknowns, args=(unknowns_to_process_queue, Global,))
    unknowns_thread.start()


def draw_detection(frame, face_locations, face_names, match_types):
    for (top, right, bottom, left), name, type in zip(face_locations, face_names, match_types):
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 0), 2)  # Draw a box around the face

        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 0), cv2.FILLED)  # Draw a name label
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
        cv2.putText(frame, str(type), (left + 6, bottom + 15), cv2.FONT_ITALIC, 0.5, (255, 255, 255), 1)


def match_search(face_encoding, db_ids, db_names, db_encodings, recent_ids, recent_names, recent_encodings,
                 frequent_ids, frequent_names, frequent_encodings):
    recent_visitors_matches = face_recognition.compare_faces(recent_encodings, face_encoding)
    if True in recent_visitors_matches:  # Search for a match in recent visitors
        match_index = recent_visitors_matches.index(True)
        return recent_ids[match_index], recent_names[match_index], recent_encodings[match_index], "recent visitor"
    else:  # Search for a match in frequent visitors
        frequent_visitors_matches = face_recognition.compare_faces(frequent_encodings, face_encoding)
        if True in frequent_visitors_matches:
            match_index = frequent_visitors_matches.index(True)
            return frequent_ids[match_index], frequent_names[match_index], frequent_encodings[match_index], "frequent visitor"
        else:  # Search for a match in database records
            database_matches = face_recognition.compare_faces(db_encodings, face_encoding)
            if True in database_matches:  # If a match was found in known_face_encodings
                match_index = database_matches.index(True)
                return db_ids[match_index], db_names[match_index], db_encodings[match_index], "database match"
            else:
                return False


def unknown_duplicate(unknowns_to_process_queue, face_encoding):
    while not unknowns_to_process_queue.empty:
        record = unknowns_to_process_queue.get()
        unknowns_to_process_queue.put(record)
        record_match = face_recognition.compare_faces([record[3]], face_encoding)
        if True in record_match:
            return True
        else:
            return False


def process_frame(db_ids, db_names, db_encodings, recent_ids, recent_names, recent_encodings, frequent_ids,
                  frequent_names, frequent_encodings, frames_to_process_queue, processed_frames_queue,
                  visitors_to_process_queue, unknowns_to_process_queue, Global, lock,):
    while not Global.is_exit:
        if not frames_to_process_queue.empty():
            frame_tuple = frames_to_process_queue.get()
            frame_idx = frame_tuple[0]
            frame = frame_tuple[1]
            time_read = frame_tuple[2]

            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_names = []
            match_types = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                encoding_match = match_search(face_encoding, db_ids, db_names, db_encodings, recent_ids, recent_names,
                                              recent_encodings, frequent_ids, frequent_names, frequent_encodings)
                if not encoding_match:
                    lock.acquire()
                    if not unknown_duplicate(unknowns_to_process_queue, face_encoding):
                        match_type = "unknown"
                        name = "Unknown"
                        face_id = str(uuid.uuid4())

                        recent_ids.append(face_id)
                        recent_names.append(name)
                        recent_encodings.extend([face_encoding])

                        db_ids.append(face_id)
                        db_names.append("Unknown")
                        db_encodings.extend([face_encoding])

                        visitors_to_process_queue.put(face_id)
                        unknown_face_tuple = (face_id, rgb_frame, face_location, face_encoding)
                        unknowns_to_process_queue.put(unknown_face_tuple)
                    lock.release()
                else:
                    face_id = encoding_match[0]
                    name = encoding_match[1]
                    match_type = encoding_match[3]
                    if match_type != "recent visitor":
                        recent_ids.append(face_id)
                        recent_names.append(name)
                        recent_encodings.extend([face_encoding])
                        visitors_to_process_queue.put((face_id, name, face_encoding))

                face_names.append(name)
                match_types.append(match_type)

            draw_detection(frame, face_locations, face_names, match_types)
            processed_frame_tuple = (frame_idx, frame, time_read)
            processed_frames_queue.put(processed_frame_tuple)

if __name__ == '__main__':
    lock = Lock()
    print("lock created")

    Global = multiprocessing.Manager().Namespace()
    Global.is_exit = False
    print("Global created")

    frames_to_process_queue = Queue()
    processed_frames_queue = Queue()
    unknowns_to_process_queue = Queue()
    visitors_to_process_queue = Queue()
    frames_with_matches_queue = Queue()
    print("queues created")

    db_records = records.db_data()
    frequent_visitors = records.frequent_visitors()
    recent_visitors = records.last_hour_visitors()
    print("records lists created")

    db_ids = Manager().list(db_records[0])
    db_names = Manager().list(db_records[1])
    db_encodings = Manager().list(db_records[2])
    print("db lists created")

    frequent_ids = Manager().list(frequent_visitors[0])
    frequent_names = Manager().list(frequent_visitors[1])
    frequent_encodings = Manager().list(frequent_visitors[2])
    print("frequent lists created")

    recent_ids = Manager().list(recent_visitors[0])
    recent_names = Manager().list(recent_visitors[1])
    recent_encodings = Manager().list(recent_visitors[2])
    print("recent lists created")

    camera_ids = [0]
    t = []
    for camera_id in camera_ids:
        t.append(threading.Thread(target=get_frame, args=(frames_to_process_queue, camera_id,)))
        t[camera_id].start()
        print("capture thread " + str(camera_id) + " started")

    p = []
    for worker_id in range(5):
        p.append(Process(target=process_frame, args=(db_ids, db_names, db_encodings, recent_ids, recent_names,
                                                     recent_encodings, frequent_ids, frequent_names, frequent_encodings,
                                                     frames_to_process_queue, processed_frames_queue,
                                                     visitors_to_process_queue, unknowns_to_process_queue, Global, lock,)))
        p[worker_id].start()
        print("worker process " + str(worker_id) + " started")

    new_records = Process(target=add_records, args=(visitors_to_process_queue, unknowns_to_process_queue, Global,))
    new_records.start()
    print("new_records process started")


    while (True):
        if not processed_frames_queue.empty():

            frame_to_display = processed_frames_queue.get()
            frame_idx = frame_to_display[0]
            frame = frame_to_display[1]
            time_read = frame_to_display[2]
            frame_delay = "frame delay: " + str(datetime.now() - time_read)
            time_text = "time: " + str(time_read)

            position = (0, 20)
            cv2.putText(frame, time_text, (5, 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, frame_delay, (5, 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            preview_name = "Camera " + str(frame_idx)
            cv2.imshow(preview_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # closing all windows
    cv2.destroyAllWindows()

    cv2.destroyWindow(previewName)

# Load names and encodings from the database
known_face_names = records.db_data()[0]
known_face_encodings = records.db_data()[1]

print(len(known_face_names), len(known_face_encodings))

# Create threads as follows
thread1 = camThread("Camera 1", 0)
#thread2 = camThread("Camera 2", 1)

thread1.start()
#thread2.start()

print("Active threads", threading.activeCount())

# conn.connection.close()