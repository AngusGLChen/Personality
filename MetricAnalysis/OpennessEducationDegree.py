'''
Created on Jan 22, 2016

@author: Angus
'''

import mysql.connector, json

def QueryEducationDegree(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    personality_path = path + "personality_scores"
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
    # 1. Education
    sql = "SELECT user_pii.course_user_id, user_pii.level_of_education FROM user_pii"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    education_map = {}
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        education = result[1]
        
        if learner not in learner_personality_map.keys():
            continue
        
        # Education
        if education not in ["p", "m", "b", "a", "hs", "jhs", "el", "none", "other", "p_se", "p_oth"]:
            education = "Unknown"
        
        if education in ["p", "p_se", "p_oth", "m"]:
            education = "Graduate"

        if education in ["b", "a"]:
            education = "Bachelor"
                
        if education in ["hs", "jhs", "el", "none", "other"]:
            education = "Others"
        
        # Store demographic information
        learner_personality_map[learner]["education"] = education
        
        if education not in education_map.keys():
            education_map[education] = set()
        education_map[education].add(learner)
    
    
    # 2. Personality - Openness
    learner_openness_map = {}
    for learner in learner_personality_map.keys():
        learner_openness_map[learner] = learner_personality_map[learner]["result"]["Openness"]
        
    # 3. Sorting Openness
    sorted_learner_openness_map = sorted(learner_openness_map.items(), key=lambda d: d[1])
    
    # 4. Bins -Analysis
    length = len(sorted_learner_openness_map)
    low_group = {}
    high_group = {}
    
    for i in range(length):
        learner = sorted_learner_openness_map[i][0]
        education = learner_personality_map[learner]["education"]

        if i < length / 2:
            if education not in low_group.keys():
                low_group[education] = 0
            low_group[education] += 1
        else:
            if education not in high_group.keys():
                high_group[education] = 0
            high_group[education] += 1
            
    for education in low_group.keys():
        print education + "\t" + str(round(low_group[education] / float(length) * 2 * 100, 2)) + "%"
    print
    
    for education in high_group.keys():
        print education + "\t" + str(round(high_group[education] / float(length) * 2 * 100, 2)) + "%"
    print
    
    print "---------------------------"
    
    for education in education_map.keys():
        sum = 0
        for learner in education_map[education]:
            sum += learner_personality_map[learner]["result"]["Openness"]
        sum = round(float(sum) / len(education_map[education]), 2)
        print education + "\t" + str(sum)
         
        
        
    
    
    
            
   
    
path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
QueryEducationDegree(path)
print "Finished."
