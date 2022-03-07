import uuid
import time
import cv2
import threading
import face_recognition
from datetime import datetime
import numpy as np
import data_access.connection as conn
import data_access.db_records as records
import face_analysis.recognition_functions as fr
import face_analysis.facial_attribute_analysis as fae


class editDatabase(threading.Thread):
    def __init__(self, frame, name, face_encodings):
        threading.Thread.__init__(self)
        self.frame = frame
        self.name = name
        self.face_encodings = face_encodings
    def run(self):
        edit_records(self.frame, self.name, self.face_encodings)


def edit_records(frame, name, face_encodings):
    records.add_record_from_encodings(name, face_encodings)
    print(fae.detect_gender(frame))
    print(fae.detect_age(frame))
    conn.connection.commit()


class camThread(threading.Thread):
    def __init__(self, previewName, camID):
        threading.Thread.__init__(self)
        self.previewName = previewName
        self.camID = camID
    def run(self):
        print("Starting " + self.previewName)
        camPreview(self.previewName, self.camID)


def draw_detection(frame, face_locations, face_names):
    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


def camPreview(previewName, camID):
    cv2.namedWindow(previewName)
    cam = cv2.VideoCapture(camID)
    if cam.isOpened():
        ret, frame = cam.read()
    else:
        ret = False

    while ret:
        ret, frame = cam.read()

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        if len(face_locations) > 0:
            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # If a match was found in known_face_encodings
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]

                if name == "Unknown":
                    name = str(uuid.uuid4())
                    known_face_encodings.extend([face_encoding])
                    known_face_names.append(name)
                    addRecordThread = editDatabase(frame, name, [face_encoding])
                    addRecordThread.start()

                face_names.append(name)

            draw_detection(frame, face_locations, face_names)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, str(datetime.now()), (50, 50), font, 1, (0, 255, 255), 2, cv2.LINE_4)

        cv2.imshow(previewName, frame)

        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break

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