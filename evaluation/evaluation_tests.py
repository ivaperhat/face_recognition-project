from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Compare lists to print confusion matrix
def get_confusion_matrix(actuals_list, predictions_list):
    cm = confusion_matrix(actuals_list, predictions_list)
    tn, fp, fn, tp = cm.ravel()

    return tn, tp, fp, fn

# Test for: accuracy, precision, recall, f1
def run_tests(actuals_list, predictions_list):
    accuracy = 100 * accuracy_score(actuals_list, predictions_list)
    precision = 100 * precision_score(actuals_list, predictions_list)
    recall = 100 * recall_score(actuals_list, predictions_list)
    f1 = 100 * f1_score(actuals_list, predictions_list)

    return accuracy, precision, recall, f1

def mean_absolute_error(actuals_list, predictions_list):
    index = 0
    sum = 0
    correct = 0
    for idx in predictions_list:
        actual_touple = eval(actuals_list[index])

        if actual_touple[0] <= idx <= actual_touple[1]:
            correct += 1
        elif idx < actual_touple[0]:
            sum += abs(actual_touple[0] - idx)
        elif idx > actual_touple[1]:
            sum += abs(idx - actual_touple[1])
        index += 1
    return sum/index, correct