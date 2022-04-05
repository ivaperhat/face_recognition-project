import evaluation.adience_evaluation_functions as func
import evaluation.evaluation_tests as tests

textfiles = ['fold_0_data.txt', 'fold_1_data.txt', 'fold_2_data.txt', 'fold_3_data.txt', 'fold_4_data.txt']
age_group_regex_list = ["^[(](0, 2)[)]", "^[(](4, 6)[)]", "^[(](8, 12)[)]", "^[(](15, 20)[)]", "^[(](25, 32)[)]",
                        "^[(](38, 43)[)]", "^[(](48, 53)[)]", "^[(](60, 100)[)]"]

for age_group_regex in age_group_regex_list:
    print(age_group_regex)
    all_folders = func.include_all_textfiles(textfiles, age_group_regex)
    all_folders = all_folders[0:2]

    gender_actuals = func.gender_actuals(all_folders)
    gender_predictions = func.gender_predictions(all_folders)

    # Remove instances where face detection failed
    new_gender_predictions = func.remove_failed_items(gender_predictions, gender_predictions)
    new_gender_actuals = func.remove_failed_items(gender_predictions, gender_actuals)

    male_predictions = func.get_bool_list('m', new_gender_predictions)
    male_actuals = func.get_bool_list('m', new_gender_actuals)
    female_predictions = func.get_bool_list('f', new_gender_predictions)
    female_actuals = func.get_bool_list('f', new_gender_actuals)

    male_tests = tests.run_tests(male_actuals, male_predictions)
    female_tests = tests.run_tests(female_actuals, female_predictions)

    print("GENDER PREDICTION EVALUATION: MALE")
    print("ACCURACY:", male_tests[0])
    print("PRECISION:", male_tests[1])
    print("RECALL:", male_tests[2])
    print("F1:", male_tests[3])

    print("\nGENDER PREDICTION EVALUATION: FEMALE")
    print("ACCURACY:", female_tests[0])
    print("PRECISION:", female_tests[1])
    print("RECALL:", female_tests[2])
    print("F1:", female_tests[3])