'''
Created on Jan 26, 2016

@author: Angus
'''

import mysql.connector, json, csv

def SpacingFeatureAnalysis(course_path, personality_path, survey_path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    # 0. Query the set of ACTIVE learners' id in database
    edx_learner_id_set = set()
    sql = "SELECT global_user.global_user_id FROM global_user, (SELECT DISTINCT(observations.course_user_id) FROM observations) AS T WHERE global_user.course_user_id = T.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        learner_id = str(result[0])
        edx_learner_id_set.add(learner_id)
    print "# edx active learners is:\t" + str(len(edx_learner_id_set)) + "\n"
    
    # 1. Read personality scores
    personality_path = course_path + "personality_scores"
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
    #######################
    # 2. Gather survey data
    
    survey_learner_map = {}
    
    survey_id_path = survey_path + "edX_user_id/course-v1_DelftX+EX101x+3T2015-anon-ids.csv"
    survey_id_file = open(survey_id_path, "r")
    id_reader = csv.reader(survey_id_file)
    
    id_map = {}
    id_reader.next()
    
    for row in id_reader:
        edx_id = str(row[0])
        qualtrics_id = str(row[1])
            
        if edx_id in edx_learner_id_set:
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
                        
            # Unweighted version
            # prior_score = pivot_table + named_ranges + array_formulas + database + python 
            
            # Weighted version            
            prior_score = pivot_table * 1 + named_ranges * 2 + array_formulas * 3 + database * 4 + python * 5        
            
            survey_learner_map[learner] = prior_score
            
    print "# survey learners is:\t" + str(len(survey_learner_map))
    
    update_learner_personality_map = {}    
    for learner in survey_learner_map.keys():
        prior_score = survey_learner_map[learner]
        
        #if prior_score >= 5 and prior_score < 30:
        if prior_score >= 30 and prior_score < 76:
            update_learner_personality_map[learner] = learner_personality_map[learner]
            update_learner_personality_map[learner]["prior_knowledge"] = survey_learner_map[learner]
    
    learner_personality_map.clear()
    learner_personality_map = update_learner_personality_map.copy()
            
    print "# personality learners is:\t" + str(len(learner_personality_map))    
    
    #########################################################################################################################################
    sql = "SELECT sessions.course_user_id, COUNT(sessions.session_id), SUM(sessions.duration) FROM sessions GROUP BY sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_session_map = {}
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        num_sessions = result[1]
        duration = result[2]
        if learner in learner_personality_map.keys():
            learner_session_map[learner] = {"number": num_sessions, "duration": duration}
            
    sorted_learner_session_map = sorted(learner_session_map.items(), key=lambda learner_session_map: learner_session_map[1])
    
    bins = 2
    length = len(sorted_learner_session_map)
    
    for i in range(bins):
        
        output_path = course_path + "spacing/data_bin_" + str(i)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "num_sessions"])  
        
        start = length / bins * i
        end = length / bins * (i + 1)
        
        for j in range(start, end):
            
            learner = sorted_learner_session_map[j][0]
            
            array = []        
            array.append(learner_personality_map[learner]["result"]["Extroversion"])
            array.append(learner_personality_map[learner]["result"]["Agreeableness"])
            array.append(learner_personality_map[learner]["result"]["Conscientiousness"])
            array.append(learner_personality_map[learner]["result"]["Neuroticism"])
            array.append(learner_personality_map[learner]["result"]["Openness"])
                        
            num_sessions = sorted_learner_session_map[j][1]["number"]
            array.append(num_sessions)
            
            writer.writerow(array)
    
        output_file.close()
            
    
    
        
    
course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"                       
personality_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/personality_scores"
survey_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/survey/"
SpacingFeatureAnalysis(course_path, personality_path, survey_path)
print "Finished."