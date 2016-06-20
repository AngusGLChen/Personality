'''
Created on Jan 20, 2016

@author: Angus
'''

import csv, datetime, pylab, numpy, math, os, json, mysql.connector
import matplotlib.pyplot as plt
from sets import Set

def CollectPersonalityData(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    # 0. Query the set of learners' id in database
    edx_learner_id_set = set()
    sql = "SELECT global_user.global_user_id FROM global_user"
    
    # Active learners
    sql = "SELECT global_user.global_user_id FROM global_user, (SELECT DISTINCT(observations.course_user_id) FROM observations) AS T WHERE global_user.course_user_id = T.course_user_id"
        
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        learner_id = str(result[0])
        edx_learner_id_set.add(learner_id)
    print "# edx learners is:\t" + str(len(edx_learner_id_set)) + "\n"
    
    # 1. Read id file
    id_path = path + "course-v1_DelftX+EX101x+3T2015-anon-ids.csv"
    id_file = open(id_path, "r")
    id_reader = csv.reader(id_file)
    
    id_map = {}
    
    row_num = 0
    for row in id_reader:
        row_num += 1
        if row_num > 1:
            edx_id = str(row[0])
            qualtrics_id = str(row[1])
            
            if edx_id in edx_learner_id_set:
                id_map[qualtrics_id] = edx_id
    
    print "Processing anon-ids.csv ..."
    print "# data records from anon-ids file:\t" + str(row_num)
    print "# effective data records is:\t" + str(len(id_map)) + "\n"
    
    # 2. Read result file
    result_path = path + "20150526_PersonalityQuestionaire.csv"
    result_file = open(result_path, "r")
    result_reader = csv.reader(result_file)
    
    learner_index = 25    
    start_time_index = 7
    end_time_index = 8
    
    question_start_index = 38
    question_end_index = 87
    
    learner_personality_map = {}
    num_unmatched_ids = 0
    
    row_num = 0
    respondent_set = set()
    for row in result_reader:
        row_num += 1
        if row_num > 2:
            
            learner = row[learner_index]
            
            if learner == "":
                continue
            
            start_time = row[start_time_index]
            end_time = row[end_time_index]
            
            format="%Y-%m-%d %H:%M:%S"
            start_time = datetime.datetime.strptime(start_time,format)
            end_time = datetime.datetime.strptime(end_time,format)
            
            duration = round((end_time - start_time).days * 24 * 60 + (end_time - start_time).seconds / float(60), 2)      
            
            result_array = []
            mark = True
            
            if learner in id_map.keys():
                
                respondent_set.add(learner)
            
                for i in range(question_start_index, question_end_index + 1):
                    if row[i] == "":
                        mark = False
                        break
                    else:
                        result_array.append(int(row[i]) + 3)
            
                if mark:      
                    learner = id_map[learner]
                    if learner not in learner_personality_map.keys():
                        learner_personality_map[learner] = {"result": result_array, "duration": duration}
    
    full_duration_array = []
    for learner in learner_personality_map.keys():
        full_duration_array.append(learner_personality_map[learner]["duration"])
        
    lower_bound = 3
    upper_bound = 12
    
    # Threshold version
    duration_array = []
    for element in full_duration_array:
        duration_array.append(element)

    print "# repondents is:\t" + str(len(duration_array))
    
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        duration = learner_personality_map[learner]["duration"]
        if duration >= lower_bound and duration <= upper_bound:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    print "# remaining repondents is:\t" + str(len(selected_learner_personality_map))
            
    for learner in selected_learner_personality_map.keys():
        array = selected_learner_personality_map[learner]["result"]
        E = 20 + array[0] - array[5] + array[10] - array[15] + array[20] - array[25] + array[30] - array[35] + array[40] - array[45]
        A = 14 - array[1] + array[6] - array[11] + array[16] - array[21] + array[26] - array[31] + array[36] + array[41] + array[46]
        C = 14 + array[2] - array[7] + array[12] - array[17] + array[22] - array[27] + array[32] - array[37] + array[42] + array[47]
        N = 38 - array[3] + array[8] - array[13] + array[18] - array[23] - array[28] - array[33] - array[38] - array[43] - array[48]
        O = 8  + array[4] - array[9] + array[14] - array[19] + array[24] - array[29] + array[34] + array[39] + array[44] + array[49]
        
        selected_learner_personality_map[learner]["result"] = {"Extroversion": E, "Agreeableness": A, "Conscientiousness": C, "Neuroticism": N, "Openness": O}
        
    # 1. Certification
    completer_map = {}
    
    sql = "SELECT course_user.course_user_id, course_user.certificate_status, course_user.final_grade FROM course_user"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_certificate_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        status = result[1]
        grade = result[2]
        learner_certificate_map[learner] = {"status": status, "grade": grade}
    
    num_unmatched_ids = 0
    num_completers = 0
    for learner in selected_learner_personality_map.keys():
        
        if learner not in learner_certificate_map.keys():
            num_unmatched_ids += 1
            selected_learner_personality_map[learner]["certification"] = "notpassing"
            selected_learner_personality_map[learner]["grade"] = 0
            continue
        
        status = learner_certificate_map[learner]["status"]
        grade = learner_certificate_map[learner]["grade"]
        
        selected_learner_personality_map[learner]["certification"] = status
        selected_learner_personality_map[learner]["grade"] = grade
        
        if status == "downloadable":
            num_completers += 1
            completer_map[learner] = selected_learner_personality_map[learner]
    
    # Filter out non-completers       
    selected_learner_personality_map.clear()
    selected_learner_personality_map = completer_map.copy()
    
    print "# unmatched ids is:\t" + str(num_unmatched_ids)
    print "# selected completers is:\t" + str(num_completers) + "\n"
    
    # 2. Course start/end time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    course_end_time = ""
    
    time_array = []
    
    for result in results:        
        course_start_time = result[0]
        course_end_time = result[1]
        
    while course_start_time < course_end_time:
        course_start_time += datetime.timedelta(days=7)
        time_array.append(course_start_time)

    # 3. Video-watching time
    sql = "SELECT observations.course_user_id, observations.duration, observations.finish_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["video_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        finish_time = result[2]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["video_time"][i] += duration
                    break
                
    # 4. Quiz-solving time
    sql = "SELECT quiz_sessions.course_user_id, quiz_sessions.duration, quiz_sessions.end_time FROM quiz_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["quiz_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        finish_time = result[2]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["quiz_time"][i] += duration
                    break
            
    # 5. Questions
    sql = "SELECT submissions.course_user_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["questions"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        finish_time = result[1]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["questions"][i] += 1
                    break    
            
    # 6. New posts
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations WHERE collaborations.collaboration_type=\"CommentThread_discussion\" or collaborations.collaboration_type=\"CommentThread_question\""
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["new_posts"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        finish_time = result[1]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["new_posts"][i] += 1
                    break
    
    # 7. Reply
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations WHERE collaborations.collaboration_type=\"Comment\" or collaborations.collaboration_type=\"Comment_Reply\""
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["reply"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        finish_time = result[1]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["reply"][i] += 1
                    break
        
    # 8. New posts + Reply
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["forum"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        finish_time = result[1]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["forum"][i] += 1
                    break
       
    # 9. Forum-browsing time
    sql = "SELECT forum_sessions.course_user_id, forum_sessions.duration, forum_sessions.end_time FROM forum_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["forum_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        finish_time = result[2]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["forum_time"][i] += duration
                    break
    
    # 10. Total time on-site
    sql = "SELECT sessions.course_user_id, sessions.duration, sessions.start_time FROM sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in selected_learner_personality_map.keys():
        value_array = []
        for i in range(len(time_array)):
            value_array.append(0)
        selected_learner_personality_map[learner]["time_on_site"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        finish_time = result[2]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    selected_learner_personality_map[learner]["time_on_site"][i] += duration
                    break    

    #####################################################################################
    
    print "# effective records is:\t" + str(len(selected_learner_personality_map)) + "\n"

    output_path = os.path.dirname(os.path.dirname(path)) + "/personality_results_active_learners_week"
    output_file = open(output_path, "w")
    writer = csv.writer(output_file)
    output_file.write(json.dumps(selected_learner_personality_map))
    
    '''
    #writer.writerow(["gender_female", "age", "education_bachelor", "education_graduate", "Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "time_on_site"])
    #writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "time_on_site"])
    for learner in selected_learner_personality_map.keys():
        
        record = selected_learner_personality_map[learner]
        
        array = []
        
        array.append(selected_learner_personality_map[learner]["result"]["Extroversion"])
        array.append(selected_learner_personality_map[learner]["result"]["Agreeableness"])
        array.append(selected_learner_personality_map[learner]["result"]["Conscientiousness"])
        array.append(selected_learner_personality_map[learner]["result"]["Neuroticism"])
        array.append(selected_learner_personality_map[learner]["result"]["Openness"])
        
        array.append(selected_learner_personality_map[learner]["video_time"])
        array.append(selected_learner_personality_map[learner]["quiz_time"])
        array.append(selected_learner_personality_map[learner]["questions"])
        array.append(selected_learner_personality_map[learner]["new_posts"])
        array.append(selected_learner_personality_map[learner]["reply"])
        array.append(selected_learner_personality_map[learner]["forum"])
        array.append(selected_learner_personality_map[learner]["forum_time"])
        
        array.append(selected_learner_personality_map[learner]["time_on_site"])
    
        writer.writerow(array)
    '''
    
    output_file.close()
    
def SelectActiveLearners(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    # 0. Query the set of learners' id in database
    edx_learner_id_set = set()
    sql = "SELECT global_user.global_user_id FROM global_user"
    
    # Active learners
    sql = "SELECT global_user.global_user_id FROM global_user, (SELECT DISTINCT(observations.course_user_id) FROM observations) AS T WHERE global_user.course_user_id = T.course_user_id"
        
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        learner_id = str(result[0])
        edx_learner_id_set.add(learner_id)
    print "# edx learners is:\t" + str(len(edx_learner_id_set)) + "\n"
    
    # 1. Read id file
    id_path = path + "course-v1_DelftX+EX101x+3T2015-anon-ids.csv"
    id_file = open(id_path, "r")
    id_reader = csv.reader(id_file)
    
    id_map = {}
    
    row_num = 0
    for row in id_reader:
        row_num += 1
        if row_num > 1:
            edx_id = str(row[0])
            qualtrics_id = str(row[1])
            
            if edx_id in edx_learner_id_set:
                id_map[qualtrics_id] = edx_id
    
    print "Processing anon-ids.csv ..."
    print "# data records from anon-ids file:\t" + str(row_num)
    print "# effective data records is:\t" + str(len(id_map)) + "\n"
    
    # 2. Read result file
    result_path = path + "20150526_PersonalityQuestionaire.csv"
    result_file = open(result_path, "r")
    result_reader = csv.reader(result_file)
    
    learner_index = 25    
    start_time_index = 7
    end_time_index = 8
    
    question_start_index = 38
    question_end_index = 87
    
    learner_personality_map = {}
    
    row_num = 0
    respondent_set = set()
    for row in result_reader:
        row_num += 1
        if row_num > 2:
            
            learner = row[learner_index]
            
            if learner == "":
                continue
            
            start_time = row[start_time_index]
            end_time = row[end_time_index]
            
            format="%Y-%m-%d %H:%M:%S"
            start_time = datetime.datetime.strptime(start_time,format)
            end_time = datetime.datetime.strptime(end_time,format)
            
            duration = round((end_time - start_time).days * 24 * 60 + (end_time - start_time).seconds / float(60), 2)      
            
            result_array = []
            mark = True
            
            if learner in id_map.keys():
                
                respondent_set.add(learner)
            
                for i in range(question_start_index, question_end_index + 1):
                    if row[i] == "":
                        mark = False
                        break
                    else:
                        result_array.append(int(row[i]) + 3)
            
                if mark:      
                    learner = id_map[learner]
                    if learner not in learner_personality_map.keys():
                        learner_personality_map[learner] = {"result": result_array, "duration": duration}
    
    full_duration_array = []
    for learner in learner_personality_map.keys():
        full_duration_array.append(learner_personality_map[learner]["duration"])
        
    lower_bound = 3
    upper_bound = 12
    
    # Threshold version
    duration_array = []
    for element in full_duration_array:
        duration_array.append(element)

    print "# repondents is:\t" + str(len(duration_array))
    
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        duration = learner_personality_map[learner]["duration"]
        if duration >= lower_bound and duration <= upper_bound:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    print "# remaining repondents is:\t" + str(len(selected_learner_personality_map))
            
    active_learner_map = {}
    
    # 1. Certification
    completer_map = {}
    
    sql = "SELECT course_user.course_user_id, course_user.certificate_status, course_user.final_grade FROM course_user"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_certificate_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        status = result[1]
        grade = result[2]
        learner_certificate_map[learner] = {"status": status, "grade": grade}
    
    num_unmatched_ids = 0
    num_completers = 0
    for learner in selected_learner_personality_map.keys():
        
        if learner not in learner_certificate_map.keys():
            num_unmatched_ids += 1
            selected_learner_personality_map[learner]["certification"] = "notpassing"
            selected_learner_personality_map[learner]["grade"] = 0
            continue
        
        status = learner_certificate_map[learner]["status"]
        grade = learner_certificate_map[learner]["grade"]
        
        selected_learner_personality_map[learner]["certification"] = status
        selected_learner_personality_map[learner]["grade"] = grade
        
        if status == "downloadable":
            num_completers += 1
            completer_map[learner] = selected_learner_personality_map[learner]
    
    # Filter out non-completers       
    selected_learner_personality_map.clear()
    selected_learner_personality_map = completer_map.copy()
    
    print "# unmatched ids is:\t" + str(num_unmatched_ids)
    print "# selected completers is:\t" + str(num_completers) + "\n"
    
    # 2. Course start/end time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    course_end_time = ""
    
    time_array = []
    
    for result in results:        
        course_start_time = result[0]
        course_end_time = result[1]
        
    while course_start_time < course_end_time:
        course_start_time += datetime.timedelta(days=7)
        time_array.append(course_start_time)
        
    for i in range(len(time_array)):
        active_learner_map[i] = set()        

    # 3. Video-watching time
    sql = "SELECT observations.course_user_id, observations.duration, observations.finish_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        finish_time = result[2]
        
        if learner in selected_learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if finish_time < time_array[i]:
                    active_learner_map[i].add(learner)
                    break
                
    for week in active_learner_map.keys():
        array = []
        for learner in active_learner_map[week]:
            array.append(learner)
        active_learner_map[week] = array
        print str(week) + "\t" + str(len(active_learner_map[week]))
                
    # Output
    output_path = os.path.dirname(os.path.dirname(path)) + "/active_completers_week"
    output_file = open(output_path, "w")
    output_file.write(json.dumps(active_learner_map))
    output_file.close()
    
def GenerateDataByWeek(path):
    
    # 1. Read personality results
    personality_path = path + "personality_results_active_learners_week"
    personality_file = open(personality_path, "r")
    personality_results_map = json.loads(personality_file.read())
    personality_file.close()
    
    # 2. Read active learners by week
    active_learners_path = path + "active_completers_week"
    active_learners_file = open(active_learners_path, "r")
    active_learners_map = json.loads(active_learners_file.read())
    active_learners_file.close()
    
    # 3. Generate the data by week
    for week in active_learners_map.keys():
        
        output_path = path + "data_week_" + str(week)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "time_on_site"])
          
        #learners = active_learners_map[week]
        learners = personality_results_map.keys()
                
        week = int(week)
        for learner in learners:
            
            array = []
       
            array.append(personality_results_map[learner]["result"]["Extroversion"])
            array.append(personality_results_map[learner]["result"]["Agreeableness"])
            array.append(personality_results_map[learner]["result"]["Conscientiousness"])
            array.append(personality_results_map[learner]["result"]["Neuroticism"])
            array.append(personality_results_map[learner]["result"]["Openness"])
        
            array.append(personality_results_map[learner]["video_time"][week])
            array.append(personality_results_map[learner]["quiz_time"][week])
            array.append(personality_results_map[learner]["questions"][week])
            array.append(personality_results_map[learner]["new_posts"][week])
            array.append(personality_results_map[learner]["reply"][week])
            array.append(personality_results_map[learner]["forum"][week])
            array.append(personality_results_map[learner]["forum_time"][week])
        
            array.append(personality_results_map[learner]["time_on_site"][week])
    
            writer.writerow(array)
            
        output_file.close()
    
            
        
    

  

###################################################################################

# 1. Select all learner
path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_questionnaire_data/"
# CollectPersonalityData(path)

# 2. Select active learners per week
# SelectActiveLearners(path)

# 3. Generate data by week
path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/"
GenerateDataByWeek(path)

print "Finished."


























