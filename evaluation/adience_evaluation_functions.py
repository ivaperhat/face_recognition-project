import tqdm
import face_analysis.facial_attribute_analysis as fae
import re
from PIL import Image
import face_recognition
from numpy import asarray

prefix_img = "coarse_tilt_aligned_face."
photo_path = r"C:/Users/Iva/Desktop/Adience-dataset/faces"

classes = ["(0, 2)", "(4, 6)", "(8, 12)", "(15, 20)", "(25, 32)", "(38, 43)", "(48, 53)", "(60, 100)"]
# Fix age instances that do not match classes
classes_to_fix = {'35': classes[5], '3': classes[0], '55': classes[7], '58': classes[7],
                  '22': classes[3], '13': classes[2], '45': classes[5], '36': classes[5],
                  '23': classes[4], '57': classes[7], '56': classes[6], '2': classes[0],
                  '29': classes[4], '34': classes[4], '42': classes[5], '46': classes[6],
                  '32': classes[4], '(38, 48)': classes[5], '(38, 42)': classes[5],
                  '(8, 23)': classes[2], '(27, 32)': classes[4]}

none_count = 0

def return_three_cross_validation(textfile, age_group_regex):
    gender_regex = "^[fm]{1}$"

    global none_count
    # one big folder list
    folder = []
    # start processing txt
    with open(textfile) as text:
        lines = text.readlines()
    for line in lines[1:]:
        line = line.strip().split("\t")
        # real image path from folder
        img_path = line[0]+"/"+prefix_img+line[2]+"."+line[1]
        if line[3] == "None" or (re.match(gender_regex, line[4]) is None):
            none_count += 1
            continue
        else:
            if re.match(age_group_regex, line[3]):
                folder.append([img_path]+line[3:5])
                if folder[-1][1] in classes_to_fix:
                    folder[-1][1] = classes_to_fix[folder[-1][1]]
    return folder


def include_all_textfiles(textfiles, age_group_regex):
    all_folders = []
    for textfile in textfiles:
        folder = return_three_cross_validation(textfile, age_group_regex)
        all_folders.extend(folder)
    return all_folders


def gender_actuals(all_folders):
    actuals = []
    for idx in range(0, len(all_folders)):
        actual_gender = all_folders[idx][2]
        actuals.append(actual_gender)
    return actuals


def gender_predictions(all_folders):
    predictions = []
    for idx in tqdm.tqdm(range(0, len(all_folders))):
        file_path = photo_path + "/" + str(all_folders[idx][0])

        image = Image.open(file_path)
        img_array = asarray(image)

        face_locations = face_recognition.face_locations(img_array)

        if len(face_locations) > 0:
            face_location = face_locations[0]
            predicted_gender = fae.detect_gender(img_array, face_location)
            predictions.append(predicted_gender)
        else:
            predictions.append(False)
    return predictions


def age_actuals(all_folders):
    actuals = []
    for idx in range(0, len(all_folders)):
        actual_age = all_folders[idx][1]
        actuals.append(actual_age)
    return actuals


def age_predictions(all_folders):
    predictions = []
    for idx in tqdm.tqdm(range(0, len(all_folders))):
        file_path = photo_path + "/" + str(all_folders[idx][0])

        image = Image.open(file_path)
        img_array = asarray(image)

        face_locations = face_recognition.face_locations(img_array)

        if len(face_locations) > 0:
            face_location = face_locations[0]
            predicted_gender = fae.detect_age(img_array, face_location)
            predictions.append(predicted_gender)
        else:
            predictions.append(False)
    return predictions


# Remove items where face detection failed
def remove_failed_items(failed_indexes_list, list_to_edit):
    new_list = []

    failed_indexes = [i for i, val in enumerate(failed_indexes_list) if not val]
    index = 0
    for idx in list_to_edit:
        if index not in failed_indexes:
            new_list.append(idx)
        index = index + 1

    return new_list


# Replace item with bool 'True,' replace other items with bool 'False'
def get_bool_list(item, input_list):
    new_list = []
    for idx in input_list:
        if idx == item:
            new_list.append(True)
        else:
            new_list.append(False)
    return new_list
