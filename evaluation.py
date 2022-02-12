from sklearn.datasets import fetch_lfw_pairs
import tqdm
import os
import matplotlib.pyplot as plt
import main as fr
import face_recognition
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

lfw = fetch_lfw_pairs(subset='test', color=True, resize=1)

pairs = lfw.pairs
labels = lfw.target
target_names = lfw.target_names

predictions = []
actuals = []

for idx in tqdm.tqdm(range(0, 3)):
    pair = pairs[idx]
    img1 = pair[0]
    img2 = pair[1]

    plt.imshow(img1 / 255)
    plt.savefig('fig1.jpg')
    plt.imshow(img2 / 255)
    plt.savefig('fig2.jpg')

    fig1_array = face_recognition.load_image_file('fig1.jpg')
    fig2_array = face_recognition.load_image_file('fig2.jpg')

    face_encodings1 = fr.get_face_encodings(fig1_array)
    face_encodings2 = fr.get_face_encodings(fig2_array)

    if isinstance(face_encodings1, bool) or isinstance(face_encodings2, bool):
        prediction = False
    else:
        result = fr.face_match(face_encodings1, face_encodings2)

        if result:
            prediction = True
        else:
            prediction = False

    predictions.append(prediction)

    actual = True if labels[idx] == 1 else False
    actuals.append(actual)

# Remove figure files
os.remove('fig1.jpg')
os.remove('fig2.jpg')

# Create arrays from lists
actuals_array = np.array(actuals)
predictions_array = np.array(predictions)

# Test for: accuracy, precision, recall, f1
accuracy = 100 * accuracy_score(actuals_array, predictions_array)
precision = 100 * precision_score(actuals_array, predictions_array)
recall = 100 * recall_score(actuals_array, predictions_array)
f1 = 100 * f1_score(actuals_array, predictions_array)

print("accuracy: ", accuracy)
print("precision: ", precision)
print("recall: ", recall)
print("f1 =", f1)

# Test for: true negatives, true positives, false positives, false negatives
cm = confusion_matrix(actuals_array, predictions_array)
tn, fp, fn, tp = cm.ravel()

print("true negative: ", tn)
print("true positive: ", tp)
print("false positive: ", fp)
print("false negative: ", fn)
