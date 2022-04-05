import threading
import os
import urllib
import numpy as np
import tkinter as tk
import multiprocessing
from multiprocessing import Manager, Process, Queue
import face_analysis.manage_records as rec
from PIL import Image, ImageTk
import cv2
from tkinter import font as tkfont, messagebox
import face_analysis.worker_processes as worker
import socket


def is_connected():  # Check for internet connection
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        pass
    return False


# Get a resized ImageTk image from an URL
def img_from_url(url, size):
    url_response = urllib.request.urlopen(url)
    img_array = np.array(bytearray(url_response.read()), dtype=np.uint8)
    img = cv2.imdecode(img_array, -1)
    blue, green, red = cv2.split(img)
    img = cv2.merge((red, green, blue))
    img_resized = cv2.resize(img, size)
    im = Image.fromarray(img_resized)
    return ImageTk.PhotoImage(image=im) # Return the resized image as an ImageTk object


def view_face_record(controller, face_id):
    if rec.face_record_exists(face_id):
        selected_page = controller.get_page("PageFaceRecord")

        selected_page.inputtxt.delete("1.0", "end")
        selected_page.inputtxt.insert("1.0", face_id)

        inp = selected_page.inputtxt.get(1.0, "end-1c")
        record = rec.get_face_record(face_id)
        name = record[0]
        img_id = record[2]
        age = record[3]
        gender = record[4]

        # Get the URL to the image stored in the AWS S3 bucket
        url = r"https://face-recognition-faces.s3.amazonaws.com/" + img_id
        face_imgtk = img_from_url(url, (150, 150))

        selected_page.img_label.config(image=face_imgtk)
        selected_page.img_label.image = face_imgtk

        selected_page.img_label.grid(column=0, row=2, rowspan=4, sticky=tk.W, padx=0, pady=0)
        selected_page.id_label.grid(column=1, row=2, sticky=tk.W, padx=0, pady=0)
        selected_page.name_label.grid(column=1, row=3, sticky=tk.W, padx=0, pady=0)
        selected_page.age_label.grid(column=1, row=4, sticky=tk.W, padx=0, pady=0)
        selected_page.gender_label.grid(column=1, row=5, sticky=tk.W, padx=0, pady=0)

        selected_page.id_label.config(text=inp)
        selected_page.name_label.config(text=name)
        selected_page.age_label.config(text=age)
        selected_page.gender_label.config(text=gender)

        selected_page.edit_label.grid(column=0, row=6, sticky=tk.W, padx=0, pady=0)
        selected_page.name_input_label.grid(column=0, row=7, sticky=tk.W, padx=0, pady=0)
        selected_page.name_input.grid(column=0, row=8, sticky=tk.W, padx=0, pady=0)
        selected_page.set_name_btn.grid(column=1, row=8, sticky=tk.W, padx=0, pady=0)
        selected_page.delete_btn.grid(column=0, row=9, sticky=tk.W, padx=0, pady=0)

        selected_page.name_input.delete("1.0", "end")

        controller.show_frame("PageFaceRecord")
    else:
        # Show a message box in case the selected record does not exist
        messagebox.showinfo(title="Failed", message="Record does not exist.")

class UIApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica',
                                      size=18, weight="bold", slant="italic")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageCameras, PageFaces,
                  PageFaceRecord, PageVisits):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def get_page(self, page_class):
        return self.frames[page_class]

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.config(width=460, height=100)

        label = tk.Label(self, text="Start page", font=controller.title_font)
        label.grid(row=0, column=0, pady=(5, 0), padx=(200, 0), sticky='news')

        button1 = tk.Button(self, text="Go to Cameras",
                            command=lambda: controller.show_frame("PageCameras"))
        button2 = tk.Button(self, text="Face Records List",
                            command=lambda: controller.show_frame("PageFaces"))
        button3 = tk.Button(self, text="Search Face Records",
                            command=lambda: controller.show_frame("PageFaceRecord"))
        button4 = tk.Button(self, text="Visits Records List",
                            command=lambda: controller.show_frame("PageVisits"))
        button1.grid(row=1, column=0, pady=(5, 0), padx=(200, 0), sticky='news')
        button2.grid(row=2, column=0, pady=(5, 0), padx=(200, 0), sticky='news')
        button3.grid(row=3, column=0, pady=(5, 0), padx=(200, 0), sticky='news')
        button4.grid(row=4, column=0, pady=(5, 0), padx=(200, 0), sticky='news')



notifications_list = []

class PageCameras(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        def clear_notifications():
            for time_label, text_label in zip(notifications_time_labels, notifications_text_labels):
                time_label.grid_forget()
                text_label.grid_forget()

            # Update notifications frame and set the canvas scrolling region
            frame_notification.update_idletasks()
            frame_canvas.config(width=460, height=100)
            canvas.config(scrollregion=canvas.bbox("all"))

            notifications_list.clear()

        def update_notifications():
            clear_notifications()

            while not Global.is_exit:
                # Update notifications each time a new item appears in the notifications queue
                if not notifications_queue.empty():
                    notifications_list.append(notifications_queue.get())
                    notifications_list_reversed = list(reversed(notifications_list))
                    if len(notifications_list_reversed) > len(notifications_time_labels):
                        while not len(notifications_list_reversed) == len(notifications_time_labels):
                            notifications_time_labels.append(tk.Label(frame_notification, text=""))
                            notifications_text_labels.append(tk.Label(frame_notification, text=""))
                    row = 0
                    for time_label, text_label in zip(notifications_time_labels, notifications_text_labels):
                        time_label.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
                        text_label.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
                        row += 1

                    index = 0
                    for time_label, text_label in zip(notifications_time_labels, notifications_text_labels):
                        if index < len(notifications_list_reversed):
                            notification = notifications_list_reversed[index]
                            time_label.configure(text=str(notification[0])[:19])
                            text_label.configure(text=notification[1])
                            index += 1
                        else:
                            time_label.grid_forget()
                            text_label.grid_forget()

                    # Update notifications frame and set the canvas scrolling region
                    frame_notification.update_idletasks()
                    frame_canvas.config(width=460, height=100)
                    canvas.config(scrollregion=canvas.bbox("all"))


        def start_cameras(Global, camera_ids):
            if Global.is_exit == True:
                Global.is_exit = False

            # Start processes for capturing and displaying camera input
            capture_display = Process(target=worker.capture_and_display, args=(camera_ids, faces_records,
                                                                               recent_visitor_records,
                                                                               frequent_visitor_records,
                                                                               notifications_queue, Global,))
            capture_display.start()

            display_notifications = threading.Thread(target=update_notifications)
            display_notifications.start()

        def stop_cameras(Global):
            Global.is_exit = True

        def available_camera_ports_list():
            index = 0
            arr = []
            while True:
                cap = cv2.VideoCapture(index)
                if not cap.read()[0]:
                    break
                else:
                    arr.append(index)
                cap.release()
                index += 1
            return arr  # List of available camera ports

        def selected_cameras_list():
            selected_checkboxes = []
            selected_cameras = []
            for var in check_buttons_vars:
                selected_checkboxes.append(var.get())

            for camera_id, check in zip(available_cameras, selected_checkboxes):
                if check == 1:
                    selected_cameras.append(camera_id)

            return selected_cameras  # Cameras selected by the user

        def start_btn_func():
            selected_cameras = selected_cameras_list()
            if len(selected_cameras) > 0:
                start_cameras(Global, selected_cameras)
                start_btn['state'] = tk.DISABLED
                stop_btn['state'] = tk.NORMAL

        def stop_btn_func():
            stop_cameras(Global)
            start_btn['state'] = tk.NORMAL
            stop_btn['state'] = tk.DISABLED


        check_buttons_vars = []
        available_cameras = available_camera_ports_list()

        check_buttons = []
        for index, id in enumerate(available_cameras):
            camera_name = "Camera " + str(id)
            check_buttons_vars.append(tk.IntVar())
            check_buttons.append(
                tk.Checkbutton(self, text=camera_name, variable=check_buttons_vars[index], onvalue=1, offvalue=0,
                               command=lambda: print("selected")))

        title_label = tk.Label(self, text="Camera Connections")
        back_btn = tk.Button(self, text="Return to start page", command=lambda: controller.show_frame("StartPage"))
        select_label = tk.Label(self, text="Select cameras to start:")
        start_btn = tk.Button(self, text="Start Cameras", command=lambda: start_btn_func())
        stop_btn = tk.Button(self, text="Stop Cameras", command=lambda: stop_btn_func(), state=tk.DISABLED)

        title_label.grid(column=0, row=0, sticky=tk.W, pady=10)
        back_btn.grid(column=1, row=0, sticky=tk.E, padx=0, pady=10)
        select_label.grid(column=0, row=1, sticky=tk.W, pady=0)

        row = 2
        for chk_btn in check_buttons:
            chk_btn.grid(column=0, row=row)
            row += 1

        start_btn.grid(column=0, row=row, sticky=tk.E, padx=0, pady=10)
        stop_btn.grid(column=1, row=row, sticky=tk.W, padx=0, pady=10)

        row += 1
        notifications_label = tk.Label(self, text="Recent Notifications:")
        clear_notifications_btn = tk.Button(self, text="Clear Notifications", command=clear_notifications)

        notifications_label.grid(row=row, column=0, columnspan=3, pady=(15, 0), sticky=tk.W)
        clear_notifications_btn.grid(row=row, column=1, columnspan=3, pady=(15, 0), sticky=tk.W)

        # Create a frame for the canvas with non-zero row&column weights
        row += 1
        frame_canvas = tk.Frame(self)
        frame_canvas.grid(row=row+1, column=0, columnspan=3, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)

        frame_canvas.grid_propagate(False)
        canvas = tk.Canvas(frame_canvas)
        canvas.grid(row=0, column=0, sticky="news")
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the visits
        frame_notification = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame_notification, anchor='nw')

        notifications_time_labels = []
        notifications_text_labels = []

        index = 0
        notifications_time_labels.append(tk.Label(frame_notification, text=""))
        notifications_text_labels.append(tk.Label(frame_notification, text=""))
        index += 1

        row = 1
        for time, text in zip(notifications_time_labels, notifications_text_labels):
            time.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
            text.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
            row += 1

        # Update notifications frame and set the canvas scrolling region
        frame_notification.update_idletasks()
        frame_canvas.config(width=460, height=100)
        canvas.config(scrollregion=canvas.bbox("all"))


class PageFaces(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        def view_record_btn_func(face_id):
            view_face_record(controller, face_id)

        def refresh_faces():
            face_records = rec.face_records()

            if len(id_labels) < len(face_records):
                while not len(id_labels) == len(face_records):
                    id_labels.append(tk.Label(frame_faces, text=""))
                    name_labels.append(tk.Label(frame_faces, text=""))
                    age_labels.append(tk.Label(frame_faces, text=""))
                    gender_labels.append(tk.Label(frame_faces, text=""))
                    face_id_buttons.append(tk.Button(frame_faces, text="View Record"))

            row = 0
            for id_label, name_label, age_label, gender_label, btn in zip(id_labels, name_labels, age_labels, gender_labels, face_id_buttons):
                id_label.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
                name_label.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
                age_label.grid(column=2, row=row, sticky=tk.W, padx=0, pady=0)
                gender_label.grid(column=3, row=row, sticky=tk.W, padx=0, pady=0)
                btn.grid(column=4, row=row, sticky=tk.W, padx=0, pady=0)
                row += 1

            index = 0
            for id_label, name_label, age_label, gender_label, btn in zip(id_labels, name_labels, age_labels, gender_labels, face_id_buttons):
                if index < len(face_records):
                    face_record = face_records[index]
                    id_label.configure(text=face_record[0])
                    name_label.configure(text=face_record[1])
                    age_label.configure(text=face_record[4])
                    gender_label.configure(text=face_record[5])
                    callback = lambda face_id: lambda: view_record_btn_func(face_id)
                    btn.config(command=callback(face_record[0]))
                    index += 1
                else:
                    id_label.grid_forget()
                    name_label.grid_forget()
                    age_label.grid_forget()
                    gender_label.grid_forget()
                    btn.grid_forget()

            # Update records frame and set the canvas scrolling region
            frame_faces.update_idletasks()
            frame_canvas.config(width=460, height=300)
            canvas.config(scrollregion=canvas.bbox("all"))

        title_label = tk.Label(self, text="Face Records List")
        title_label.grid(column=0, row=0, sticky=tk.W, pady=10)

        back_btn = tk.Button(self, text="Return to start page", command=lambda: controller.show_frame("StartPage"))
        back_btn.grid(column=1, row=0, sticky=tk.E, padx=0, pady=10)

        refresh_btn = tk.Button(self, text="Refresh", command=refresh_faces)
        refresh_btn.grid(column=2, row=0, sticky=tk.E, padx=0, pady=10)

        # Create a frame for the canvas with non-zero row&column weights
        frame_canvas = tk.Frame(self)
        frame_canvas.grid(row=1, column=0, columnspan=3, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        canvas = tk.Canvas(frame_canvas)
        canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the records
        frame_faces = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame_faces, anchor='nw')

        id_labels = []
        name_labels = []
        age_labels = []
        gender_labels = []
        face_id_buttons = []

        face_records = rec.face_records()

        for face_record in face_records:
            id_labels.append(tk.Label(frame_faces, text=face_record[0]))
            name_labels.append(tk.Label(frame_faces, text=face_record[1]))
            age_labels.append(tk.Label(frame_faces, text=face_record[4]))
            gender_labels.append(tk.Label(frame_faces, text=face_record[5]))

            callback = lambda face_id: lambda: view_record_btn_func(face_id)
            face_id_buttons.append(tk.Button(frame_faces, text="View Record", command=callback(face_record[0])))

        row = 1
        for id, name, age, gender, button in zip(id_labels, name_labels, age_labels, gender_labels, face_id_buttons):
            id.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
            name.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
            age.grid(column=2, row=row, sticky=tk.W, padx=0, pady=0)
            gender.grid(column=3, row=row, sticky=tk.W, padx=0, pady=0)
            button.grid(column=4, row=row, sticky=tk.W, padx=0, pady=0)
            row += 1

        # Update records frame and set the canvas scrolling region
        frame_faces.update_idletasks()
        frame_canvas.config(width=480, height=300)
        canvas.config(scrollregion=canvas.bbox("all"))


class PageFaceRecord(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        def search_btn_func():
            face_id = self.inputtxt.get(1.0, "end-1c")
            view_face_record(controller, face_id)

        def set_name_btn_function():
            new_name = self.name_input.get(1.0, "end-1c")
            face_id = self.id_label.cget("text")

            # Change the record name in the Database
            rec.set_name(new_name, face_id)

            self.name_label.config(text=new_name)
            self.name_input.delete("1.0", "end")

            # Set new name in the faces_records Manager.list()
            for index, face_record in enumerate(faces_records):
                if face_record[0] == face_id:
                    as_list = list(face_record)
                    as_list[1] = new_name
                    new_tuple = tuple(as_list)
                    faces_records[index] = new_tuple
                    break

            # Set new name in the recent_visitor_records Manager.list()
            for index, face_record in enumerate(recent_visitor_records):
                if face_record[0] == face_id:
                    as_list = list(face_record)
                    as_list[1] = new_name
                    new_tuple = tuple(as_list)
                    recent_visitor_records[index] = new_tuple
                    break

            # Set new name in the frequent_visitor_records Manager.list()
            for index, face_record in enumerate(frequent_visitor_records):
                if face_record[0] == face_id:
                    as_list = list(face_record)
                    as_list[1] = new_name
                    new_tuple = tuple(as_list)
                    frequent_visitor_records[index] = new_tuple
                    break

        def delete_record_btn_function():
            face_id = self.id_label.cget("text")

            # Delete record from the Database
            rec.delete_record(face_id)

            self.name_input.delete("1.0", "end")

            # Delete record from the faces_records Manager.list()
            for index, face_record in enumerate(faces_records):
                if face_record[0] == face_id:
                    del faces_records[index]
                    break

            # Delete record from the recent_visitor_records Manager.list()
            for index, face_record in enumerate(recent_visitor_records):
                if face_record[0] == face_id:
                    del recent_visitor_records[index]
                    break

            # Delete record from the frequent_visitor_records Manager.list()
            for index, face_record in enumerate(frequent_visitor_records):
                if face_record[0] == face_id:
                    del frequent_visitor_records[index]
                    break

            # Reset the page to no longer display a record
            self.edit_label.grid_forget()
            self.name_input_label.grid_forget()
            self.name_input.grid_forget()
            self.set_name_btn.grid_forget()
            self.delete_btn.grid_forget()
            self.img_label.grid_forget()
            self.id_label.grid_forget()
            self.name_label.grid_forget()
            self.age_label.grid_forget()
            self.gender_label.grid_forget()

        def clear_btn_func():
            self.inputtxt.delete("1.0", "end")


        title_label = tk.Label(self, text="Search Face Records")
        title_label.grid(column=0, row=0, sticky=tk.W, pady=10)

        back_btn = tk.Button(self, text="Return to start page", command=lambda: controller.show_frame("StartPage"))
        back_btn.grid(column=2, row=0, sticky=tk.E, padx=0, pady=0)

        self.inputtxt = tk.Text(self, height=1, width=40)
        self.inputtxt.grid(column=0, columnspan=2, row=1, sticky=tk.W, padx=0, pady=0)
        self.inputtxt.insert(1.0, "")

        search_btn = tk.Button(self, text="Search", command=search_btn_func)
        search_btn.grid(column=2, row=1, sticky=tk.W, padx=0, pady=0)
        clear_btn = tk.Button(self, text="Clear Input", command=clear_btn_func)
        clear_btn.grid(column=3, row=1, sticky=tk.W, padx=0, pady=0)

        url = r"https://monstar-lab.com/global/wp-content/uploads/sites/11/2019/04/male-placeholder-image.jpeg"
        imgtk = img_from_url(url, (150, 150))
        self.img_label = tk.Label(self, image=imgtk)
        self.img_label.image = imgtk

        self.id_label = tk.Label(self, text="")
        self.name_label = tk.Label(self, text="")
        self.age_label = tk.Label(self, text="")
        self.gender_label = tk.Label(self, text="")

        self.edit_label = tk.Label(self, text="Edit this record")
        self.name_input_label = tk.Label(self, text="Enter new name:")
        self.name_input = tk.Text(self, height=1, width=20)
        self.set_name_btn = tk.Button(self, text="Set Name", command=set_name_btn_function)
        self.delete_btn = tk.Button(self, text="Delete this record", command=delete_record_btn_function)


class PageVisits(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        def view_record_btn_func(face_id):
            view_face_record(controller, face_id)

        def refresh_visits():
            visit_records = rec.visit_records()

            if len(visit_face_id_labels) < len(visit_records):
                while not len(visit_face_id_labels) == len(visit_records):
                    visit_face_id_labels.append(tk.Label(frame_visits, text=""))
                    visit_times_labels.append(tk.Label(frame_visits, text=""))
                    visit_btns.append(tk.Button(frame_visits, text="View Record"))

            row = 0
            for face_id_label, time_label, btn in zip(visit_face_id_labels, visit_times_labels, visit_btns):
                face_id_label.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
                time_label.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
                btn.grid(column=2, row=row, sticky=tk.W, padx=0, pady=0)
                row += 1

            index = 0
            for face_id_label, time_label, btn in zip(visit_face_id_labels, visit_times_labels, visit_btns):
                if index < len(visit_records):
                    visit_record = visit_records[index]
                    face_id_label.configure(text=visit_record[2])
                    time_label.configure(text=visit_record[1])
                    callback = lambda face_id: lambda: view_record_btn_func(face_id)
                    btn.config(command=callback(visit_record[2]))
                    index += 1
                else:
                    face_id_label.grid_forget()
                    time_label.grid_forget()
                    btn.grid_forget()

            # Update the visits frame and set a new scroll region
            frame_visits.update_idletasks()
            frame_canvas.config(width=460, height=300)
            canvas.config(scrollregion=canvas.bbox("all"))

        def delete_visit_records_btn():
            rec.delete_all_visit_records()
            refresh_visits()

        title_label = tk.Label(self, text="Visits List")
        title_label.grid(column=0, row=0, sticky=tk.W, pady=10)

        back_btn = tk.Button(self, text="Return to start page", command=lambda: controller.show_frame("StartPage"))
        back_btn.grid(column=2, row=0, sticky=tk.E, padx=0, pady=10)

        refresh_btn = tk.Button(self, text="Refresh", command=refresh_visits)
        refresh_btn.grid(column=2, row=1, sticky=tk.E, padx=0, pady=5)

        remove_visits_btn = tk.Button(self, text="Delete all visit records", command=delete_visit_records_btn)
        remove_visits_btn.grid(column=1, row=1, sticky=tk.E, padx=0, pady=5)

        visit_face_id_labels = []
        visit_times_labels = []
        visit_btns = []

        frame_canvas = tk.Frame(self)
        frame_canvas.grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        frame_canvas.grid_propagate(False)

        # Add a canvas in that frame
        canvas = tk.Canvas(frame_canvas)
        canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the visits
        frame_visits = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame_visits, anchor='nw')

        visit_records = rec.visit_records()

        index = 0
        for visit_record in visit_records:
            visit_face_id_labels.append(tk.Label(frame_visits, text=visit_record[2]))
            visit_times_labels.append(tk.Label(frame_visits, text=visit_record[1]))

            callback = lambda face_id: lambda: view_record_btn_func(face_id)
            visit_btns.append(tk.Button(frame_visits, text="View Record", command=callback(visit_record[2])))
            index += 1

        row = 1
        for face_id, time, btn in zip(visit_face_id_labels, visit_times_labels, visit_btns):
            face_id.grid(column=0, row=row, sticky=tk.W, padx=0, pady=0)
            time.grid(column=1, row=row, sticky=tk.W, padx=0, pady=0)
            btn.grid(column=2, row=row, sticky=tk.E, padx=0, pady=0)
            row += 1

        # Update the visits frame and set a new scroll region
        frame_visits.update_idletasks()
        frame_canvas.config(width=460, height=300)
        canvas.config(scrollregion=canvas.bbox("all"))


if __name__ == '__main__':

    if is_connected():  # If connected to the Internet
        # Create Manager.lists() and a notifications queue to be shared between processes
        faces_records = Manager().list(rec.face_records())
        frequent_visitor_records = Manager().list(rec.frequent_visitors())
        recent_visitor_records = Manager().list(rec.recent_visitors())
        notifications_queue = Queue()
        print("Manager lists created")

        Global = multiprocessing.Manager().Namespace()
        Global.is_exit = False

        Global.processing_unknowns = 0
        Global.no_workers = os.cpu_count() - 2

        app = UIApp()
        app.mainloop()

        Global.is_exit = True

    else:
        messagebox.showerror(title="Connection Failed", message="Internet connection failed.")

