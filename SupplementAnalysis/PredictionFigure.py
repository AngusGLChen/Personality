'''
Created on Mar 6, 2016

@author: Angus
'''

import mysql.connector, json, csv
import matplotlib.pyplot as plt

def GeneratePredictionFigures(course_path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    survey_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/survey/"
    
    # 1. Personality scores
    personality_path = course_path + "personality_scores"
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
    # 2. Gather survey data
    
    survey_learner_map = {}
    motivation_learner_map = {}
    
    survey_id_path = survey_path + "edX_user_id/course-v1_DelftX+EX101x+3T2015-anon-ids.csv"
    survey_id_file = open(survey_id_path, "r")
    id_reader = csv.reader(survey_id_file)
    
    id_map = {}
    id_reader.next()
    
    for row in id_reader:
        edx_id = str(row[0])
        qualtrics_id = str(row[1])
            
        if edx_id in learner_personality_map.keys():
            id_map[qualtrics_id] = edx_id
    
    pre_survey_path = survey_path + "Pre/2015T3_EX101x_Pre.csv"
    pre_survey_file = open(pre_survey_path, "r")
    reader = csv.reader(pre_survey_file)
    
    question_ids = reader.next()  
    question_descriptions = reader.next()
    
    for i in range(76,81):
        print question_descriptions[i]
        
    concept_distribution_array = []
    for i in range(5):
        concept_distribution_array.append([])
    
    for row in reader:
        
        if row[10] not in id_map.keys():
            continue
        
        learner = id_map[row[10]]
        
        if learner in learner_personality_map.keys():
            prior_score = 0
            
            complete_mark = True
            for i in range(76,81):
                if row[i] == "":
                    complete_mark = False
                    break
            
            motivation = row[33]
            
            if motivation == "" or motivation == "0":
                complete_mark = False
                
            if not complete_mark:
                continue
            
            pivot_table = float(row[76]) + 3
            array_formulas = float(row[77]) + 3
            python = float(row[78]) + 3
            database = float(row[79]) + 3
            named_ranges = float(row[80]) + 3
            
            concept_distribution_array[0].append(pivot_table)
            concept_distribution_array[1].append(named_ranges)
            concept_distribution_array[2].append(array_formulas)
            concept_distribution_array[3].append(database)
            concept_distribution_array[4].append(python)
            
            # Weighted version            
            prior_score = pivot_table * 1 + named_ranges * 2 + array_formulas * 3 + database * 4 + python * 5        
            
            survey_learner_map[learner] = prior_score
            
            if motivation in ["1", "2", "3", "4"]:
                motivation_learner_map[learner] = 1
                
            
            if motivation in ["5", "6"]:
                motivation_learner_map[learner] = 0
            
    print "# survey learners is:\t" + str(len(survey_learner_map))
    
    update_learner_personality_map = {}    
    for learner in survey_learner_map.keys():
        update_learner_personality_map[learner] = learner_personality_map[learner]
        update_learner_personality_map[learner]["prior_knowledge"] = survey_learner_map[learner]
        update_learner_personality_map[learner]["motivation"] = motivation_learner_map[learner]
    
    learner_personality_map.clear()
    learner_personality_map = update_learner_personality_map.copy()
            
    print "# personality learners is:\t" + str(len(learner_personality_map))
    
    # 1. Active ids per week
    active_learners_array = []
    week_array = []
    for i in range(10):
        active_path = course_path + "active_learners/" + str(i)
        active_file = open(active_path, "r")
        lines = active_file.readlines()
        num = 0
        for line in lines:
            id = line.replace("\n", "")
            if id in learner_personality_map.keys():
                num += 1
        print num
        active_learners_array.append(num)
        active_file.close()
        
        week_array.append(i)
        
    # 2. Prediction results
    prediction_path = course_path + "prediction/supplement_results.csv"
    prediction_file = open(prediction_path, "r")
    for i in range(5):
        
        all_gp_result_array = []
        all_rf_result_array = []
        
        low_prior_gp_result_array = []
        low_prior_rf_result_array = []
        
        high_prior_gp_result_array = []
        high_prior_rf_result_array = []
        
        for j in range(10):
            line = prediction_file.readline()
            array = line.replace("\n", "").split(",")
            
            all_gp_result_array.append(float(array[0]))
            all_rf_result_array.append(float(array[1]))
            
            low_prior_gp_result_array.append(float(array[2]))
            low_prior_rf_result_array.append(float(array[3]))
            
            high_prior_gp_result_array.append(float(array[4]))
            high_prior_rf_result_array.append(float(array[5]))
            
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        
        ax1.plot(week_array, active_learners_array, "--", marker="o", color="r", label="# Active learners")
        ax1.set_ylabel("# Active learners", color="r")
        
        ax1.spines['left'].set_color('red')
        ax1.tick_params(axis='y', colors='red')
        
        ax1.set_xlabel("Week")
            
        ax2.plot(week_array, all_gp_result_array, marker="s", color="#3366CC", label="GP+All")
        ax2.plot(week_array, all_rf_result_array, marker="s", color="#FF9933", label="RF+All")
        
        ax2.plot(week_array, low_prior_gp_result_array, marker="s", color="#CC6699", label="GP+LE")
        ax2.plot(week_array, low_prior_rf_result_array, marker="s", color="#99CC33", label="RF+LE")
        
        ax2.plot(week_array, high_prior_gp_result_array, marker="s", color="#FFCC00", label="GP+HE")
        ax2.plot(week_array, high_prior_rf_result_array, marker="s", color="#9933FF", label="RF+HE")
        
        ax2.set_ylabel("Correlation Coefficient")
        
    
        
        # plt.legend(loc="best")
        ax2.legend(loc='upper center', bbox_to_anchor=(0.5, 1.10), ncol=3, fancybox=True, shadow=True)
        plt.show()
        
        
            
            
        
    
    
    
    
course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
GeneratePredictionFigures(course_path)
print "Finished."
    
    
