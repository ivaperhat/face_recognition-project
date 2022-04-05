from __future__ import print_function
import os
import threading
import time
import uuid
from multiprocessing import Process, Queue
import face_recognition
import face_analysis.manage_records as records
from datetime import datetime, timedelta
import face_analysis.facial_attribute_analysis as fae
import cv2
import pytz

tz = pytz.timezone('Europe/London')

def draw_detection(frame, face_locations, face_names, match_types):
    for (top, right, bottom, left), name, type in zip(face_locations, face_names, match_types):
        # Draw a rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 0), 2)

        # Draw a name label (including: face_name, match_type)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
        cv2.putText(frame, str(type), (left + 6, bottom + 15), cv2.FONT_ITALIC, 0.5, (255, 255, 255), 1)


def match_search(face_encoding, faces_records, recent_visitor_records, frequent_visitor_records):
    recent_encodings = []
    frequent_encodings = []
    db_encodings = []

    for database_record in faces_records:
        db_encodings.extend(database_record[2])

    for frequent_record in frequent_visitor_records:
        frequent_encodings.extend(frequent_record[2])

    for recent_record in recent_visitor_records:
        recent_encodings.extend(recent_record[2])

    recent_visitors_matches = face_recognition.compare_faces(recent_encodings, face_encoding)
    if True in recent_visitors_matches:  # Search for a match in recent visitors
        match_index = recent_visitors_matches.index(True)
        return recent_visitor_records[match_index], "recent visitor"
    else:  # Search for a match in frequent visitors
        frequent_visitors_matches = face_recognition.compare_faces(frequent_encodings, face_encoding)
        if True in frequent_visitors_matches:
            match_index = frequent_visitors_matches.index(True)
            return frequent_visitor_records[match_index], "frequent visitor"
        else:  # Search for a match in database records
            database_matches = face_recognition.compare_faces(db_encodings, face_encoding)
            if True in database_matches:  # If a match was found in known_face_encodings
                match_index = database_matches.index(True)
                return faces_records[match_index], "database match"
            else:
                return False


def process_frame(frames_to_process_queue, processed_frames_queue, unknowns_to_process_queue, faces_records,
                  recent_visitor_records, frequent_visitor_records, notifications, Global,):
    while not Global.is_exit:
        unknowns_processing_full = Global.processing_unknowns >= (Global.no_workers / 2)
        if not unknowns_to_process_queue.empty() and not unknowns_processing_full:  # Process an unknown record
            Global.processing_unknowns += 1
            process_unknowns(unknowns_to_process_queue)
            Global.processing_unknowns -= 1
        elif not frames_to_process_queue.empty():
            for idx, visitor_record in enumerate(recent_visitor_records): # Remove any visitors that are no longer recent
                if visitor_record[3] < (datetime.now(tz) - timedelta(minutes=10)):
                    del recent_visitor_records[idx]
                else:
                    break

            frame_tuple = frames_to_process_queue.get()
            frame_idx = frame_tuple[0]
            frame = frame_tuple[1]
            time_read = frame_tuple[2]
            rgb_frame = frame[:, :, ::-1]

            # Find face locations and face encodings within the frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_names = []
            match_types = []

            # Process each found face
            for face_encoding, face_location in zip(face_encodings, face_locations):
                encoding_match = match_search(face_encoding, faces_records, recent_visitor_records, frequent_visitor_records)
                if not encoding_match:  # If a match wasn't found in the database
                    # Assign a name and a face_id
                    match_type = "unknown"
                    name = "Unknown"
                    face_id = str(uuid.uuid4())

                    # Add a new records to working lists
                    record_tuple = (face_id, name, [face_encoding])
                    recent_tuple = (face_id, name, [face_encoding], time_read)
                    faces_records.append(record_tuple)
                    recent_visitor_records.append(recent_tuple)

                    # Add new record to the queue to be added to the database
                    process_unknown_tuple = (face_id, rgb_frame, face_location, [face_encoding], time_read)
                    unknowns_to_process_queue.put(process_unknown_tuple)

                    # Add a new notification to the notification queue
                    notification_tuple = (datetime.now(tz), "Unknown face detected")
                    notifications.put(notification_tuple)
                else:
                    face_record = encoding_match[0]
                    match_type = encoding_match[1]
                    name = face_record[1]

                    if match_type != "recent visitor":
                        face_id = face_record[0]
                        encoding = face_record[2]

                        # Add a new visitor record to the working list
                        recent_visitor_tuple = (face_id, name, encoding, time_read)
                        recent_visitor_records.append(recent_visitor_tuple)

                        # Add a new visitor record to the database
                        records.add_visit_record(face_id, time_read)

                        # Add a new notification to the notification queue
                        notification_text = "New visitor: " + str(name)
                        notification_tuple = (datetime.now(tz), notification_text)
                        notifications.put(notification_tuple)

                # Save information needed to produce an output frame
                face_names.append(name)
                match_types.append(match_type)

            # Edit existing frame to produce an output frame
            draw_detection(frame, face_locations, face_names, match_types)

            # Add the output frame to the queue to be displayed
            processed_frame_tuple = (frame_idx, frame, time_read)
            processed_frames_queue.put(processed_frame_tuple)

    print("process stopped")


def process_unknowns(unknowns_to_process_queue):
    if not unknowns_to_process_queue.empty():
        unknown_face_tuple = unknowns_to_process_queue.get()
        face_id = unknown_face_tuple[0]
        frame = unknown_face_tuple[1]
        face_location = unknown_face_tuple[2]
        face_encoding = unknown_face_tuple[3]
        time_read = unknown_face_tuple[4]

        # Detect age and gender of the selected face record
        detected_age = fae.detect_age(frame, face_location)
        detected_gender = fae.detect_gender(frame, face_location)

        # Add new face and visit records to the database
        records.add_face_record(face_id, "Unknown", face_encoding, detected_age, detected_gender, frame, face_location)
        records.add_visit_record(face_id, time_read)


def start_worker_processes(frames_to_process_queue, processed_frames_queue, unknowns_to_process_queue,
                           faces_records, recent_visitor_records, frequent_visitor_records, notifications, Global, no_workers):
    p = []
    for worker_id in range(no_workers):
        p.append(Process(target=process_frame, args=(frames_to_process_queue, processed_frames_queue,
                                                     unknowns_to_process_queue, faces_records, recent_visitor_records,
                                                     frequent_visitor_records, notifications, Global,)))
        p[worker_id].daemon = True
        p[worker_id].start()


def get_frame(idx, Global, camera_id, frames_to_process_queue):
    frame_rate = 2
    prev = 0
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)  # Video capture
    while not Global.is_exit:
        time_elapsed = time.time() - prev
        ret, frame = cap.read()  # Return a single frame

        if time_elapsed > 1./frame_rate:
            prev = time.time()
            frames_to_process_queue.put((camera_id, frame, datetime.now(tz)))



def capture_and_display(camera_ids, faces_records, recent_visitor_records, frequent_visitor_records, notifications, Global):
    no_workers = os.cpu_count() - 2

    frames_to_process_queue = Queue()
    processed_frames_queue = Queue()
    unknowns_to_process_queue = Queue()

    start_worker_processes(frames_to_process_queue, processed_frames_queue, unknowns_to_process_queue,
                           faces_records, recent_visitor_records, frequent_visitor_records, notifications,
                           Global, no_workers)

    t = []
    # Create a separate thread to capture and display frames for each connected camera
    for index, camera_id in enumerate(camera_ids):
        t.append(threading.Thread(target=get_frame, args=(index, Global, camera_id, frames_to_process_queue,)))
        t[index].start()
        notification_tuple = (datetime.now(tz), "Starting camera")
        notifications.put(notification_tuple)

    while not Global.is_exit:
        if not processed_frames_queue.empty():

            frame_to_display = processed_frames_queue.get()
            frame_idx = frame_to_display[0]
            frame = frame_to_display[1]
            time_read = frame_to_display[2]
            preview_name = "Camera " + str(frame_idx)
            frame_delay = "frame delay: " + str(datetime.now(tz) - time_read)
            time_text = "time: " + str(time_read)

            # Edit the frame to include the time_read and frame_delay
            cv2.putText(frame, time_text, (5, 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, frame_delay, (5, 40), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            # Display the frame
            cv2.imshow(preview_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            Global.is_exit = True

    cv2.destroyAllWindows()

    print("cap disp done")