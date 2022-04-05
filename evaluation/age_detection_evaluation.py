import evaluation.adience_evaluation_functions as func
import evaluation.evaluation_tests as tests

textfiles = ['fold_0_data.txt', 'fold_1_data.txt', 'fold_2_data.txt', 'fold_3_data.txt', 'fold_4_data.txt']
age_group_regex_list = ["^[(](0, 2)[)]", "^[(](4, 6)[)]", "^[(](8, 12)[)]", "^[(](15, 20)[)]", "^[(](25, 32)[)]",
                        "^[(](38, 43)[)]", "^[(](48, 53)[)]", "^[(](60, 100)[)]"]

for age_group_regex in age_group_regex_list:
    print(age_group_regex)
    all_folders = func.include_all_textfiles(textfiles, age_group_regex)
    all_folders = all_folders[0:1000]

    age_actuals = func.age_actuals(all_folders)
    age_predictions = func.age_predictions(all_folders)

    # Remove instances where face detection failed
    new_age_predictions = func.remove_failed_items(age_predictions, age_predictions)
    new_age_actuals = func.remove_failed_items(age_predictions, age_actuals)

    print("\nAGE PREDICTION EVALUATION:")
    print("MAE:",
          tests.mean_absolute_error(new_age_actuals,
                                    new_age_predictions)[0])
    print("CORRECTLY CLASSIFIED:",
          tests.mean_absolute_error(new_age_actuals,
                                    new_age_predictions)[1])
