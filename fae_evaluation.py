import os
import tqdm
import facial_attribute_analysis as fae
import re
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

prefix_txt = "landmarks."
prefix_img = "coarse_tilt_aligned_face."
cwd = os.getcwd()+"/"
textfiles = ['fold_0_data.txt', 'fold_1_data.txt', 'fold_2_data.txt', 'fold_3_data.txt', 'fold_4_data.txt']

classes = ["(0, 2)", "(4, 6)", "(8, 12)", "(15, 20)", "(25, 32)", "(38, 43)", "(48, 53)", "(60, 100)"]
# Fix age instances that do not match classes
classes_to_fix = {'35': classes[5], '3': classes[0], '55': classes[7], '58': classes[7],
                  '22': classes[3], '13': classes[2], '45': classes[5], '36': classes[5],
                  '23': classes[4], '57': classes[7], '56': classes[6], '2': classes[0],
                  '29': classes[4], '34': classes[4], '42': classes[5], '46': classes[6],
                  '32': classes[4], '(38, 48)': classes[5], '(38, 42)': classes[5],
                  '(8, 23)': classes[2], '(27, 32)': classes[4]}

none_count = 0


def return_five_cross_validation(textfile):
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
        landmark_txt_path = line[0]+"/"+prefix_txt+line[2]+"."+line[1][:-3]+"txt"
        if line[3] == "None" or not(re.match(line[4], r"f|m")):
            none_count += 1
            continue
        else:
            folder.append([img_path]+[landmark_txt_path]+line[3:5]+[line[-2]])
            if folder[-1][1] in classes_to_fix:
                folder[-1][1] = classes_to_fix[folder[-1][1]]
    return folder


all_folders = []
for textfile in textfiles:
    folder = return_five_cross_validation(textfile)
    all_folders.extend(folder)

print("Total no. of records:", len(all_folders))
print("A sample:", all_folders[0][0])
print("Records without an age group or without gender:", none_count)

all_records = return_five_cross_validation(textfile)
photo_path = r"C:/Users/Iva/Desktop/Adience-dataset/faces"


def gender_actuals():
    actuals = []
    for idx in range(0, len(all_folders)):
        actual_gender = all_folders[idx][3]
        actuals.append(actual_gender)
    return actuals


def gender_predictions():
    predictions = []
    for idx in tqdm.tqdm(range(0, len(all_folders))):
        file_path = photo_path + "/" + str(all_folders[idx][0])
        predicted_gender = fae.detect_gender(file_path)
        predictions.append(predicted_gender)
    return predictions


def age_actuals():
    actuals = []
    for idx in range(0, len(all_folders)):
        actual_age = all_folders[idx][2]
        actuals.append(actual_age)
    return actuals


def age_predictions():
    predictions = []
    for idx in tqdm.tqdm(range(0, len(all_folders))):
        file_path = photo_path + "/" + str(all_folders[idx][0])
        predicted_gender = fae.detect_age(file_path)
        predictions.append(predicted_gender)
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
def get_bool_for(item, input_list):
    new_list = []
    for idx in input_list:
        if idx == item:
            new_list.append(True)
        else:
            new_list.append(False)
    return new_list


# Compare lists to print confusion matrix
def get_confusion_matrix(actuals_list, predictions_list):
    cm = confusion_matrix(actuals_list, predictions_list)
    tn, fp, fn, tp = cm.ravel()

    return tn, tp, fp, fn


def run_tests(actuals_list, predictions_list):
    # Test for: accuracy, precision, recall, f1
    accuracy = 100 * accuracy_score(actuals_list, predictions_list)
    precision = 100 * precision_score(actuals_list, predictions_list)
    recall = 100 * recall_score(actuals_list, predictions_list)
    f1 = 100 * f1_score(actuals_list, predictions_list)

    return accuracy, precision, recall, f1
