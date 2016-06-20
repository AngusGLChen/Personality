'''
Created on Jan 23, 2016

@author: Angus
'''

'''
Created on Jan 21, 2016

@author: Angus
'''

import mysql.connector, json, datetime, os, csv
import matplotlib.pyplot as plt

def QueryWeeklyCourseMetrics(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    personality_path = path + "personality_scores"
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
    # Query registration time
    enrolment_path = os.path.dirname(os.path.dirname(path)) + "/DelftX-EX101x-3T2015-student_courseenrollment-prod-analytics.sql"
    enrolment_file = open(enrolment_path, "r")
    enrolment_file.readline()
    lines = enrolment_file.readlines()
            
    for line in lines:
        record = line.split("\t")
        global_user_id = record[1]        
        time = record[3]
        
        format="%Y-%m-%d %H:%M:%S"
        time = datetime.datetime.strptime(time,format)
        
        if global_user_id in learner_personality_map.keys():
            learner_personality_map[global_user_id]["register_time"] = time
            
    
    # 1. Course start/end time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    course_end_time = ""
    time_array = []
    
    for result in results:        
        course_start_time = result[0]
        course_end_time = result[1]
        
    reserved_course_start_time = course_start_time
        
    while course_start_time < course_end_time:
        course_start_time += datetime.timedelta(days=7)
        time_array.append(course_start_time)
    
    # 2. Certification
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
    for learner in learner_personality_map.keys():
        
        if learner not in learner_certificate_map.keys():
            num_unmatched_ids += 1
            learner_personality_map[learner]["certification"] = "notpassing"
            learner_personality_map[learner]["grade"] = 0
            continue
        
        status = learner_certificate_map[learner]["status"]
        grade = learner_certificate_map[learner]["grade"]
        
        learner_personality_map[learner]["certification"] = status
        learner_personality_map[learner]["grade"] = grade
        
        if status == "downloadable":
            num_completers += 1
            completer_map[learner] = learner_personality_map[learner]
    
    # Filter out non-completers       
    # learner_personality_map.clear()
    # learner_personality_map = completer_map.copy()
    
    print "# unmatched ids is:\t" + str(num_unmatched_ids)
    print "# selected completers is:\t" + str(num_completers) + "\n"
    
    # 3. Video-watching time
    sql = "SELECT observations.course_user_id, observations.duration, observations.end_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["video_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["video_time"][i] += duration
                    
                
    # 4. Quiz-solving time
    sql = "SELECT quiz_sessions.course_user_id, quiz_sessions.duration, quiz_sessions.end_time FROM quiz_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["quiz_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["quiz_time"][i] += duration
                    
            
    # 5. Questions
    sql = "SELECT submissions.course_user_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["questions"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["questions"][i] += 1
                    
            
    # 6. New posts
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations WHERE collaborations.collaboration_type=\"CommentThread_discussion\" or collaborations.collaboration_type=\"CommentThread_question\""
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["new_posts"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["new_posts"][i] += 1
                    
    
    # 7. Reply
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations WHERE collaborations.collaboration_type=\"Comment\" or collaborations.collaboration_type=\"Comment_Reply\""
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["reply"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["reply"][i] += 1
                    
        
    # 8. New posts + Reply
    sql = "SELECT collaborations.course_user_id, collaborations.collaboration_timestamp FROM collaborations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["forum"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["forum"][i] += 1
                    
       
    # 9. Forum-browsing time
    sql = "SELECT forum_sessions.course_user_id, forum_sessions.duration, forum_sessions.end_time FROM forum_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["forum_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["forum_time"][i] += duration
                    
                
    # 10. Forum login
    sql = "SELECT forum_sessions.course_user_id, forum_sessions.end_time FROM forum_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["forum_login"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["forum_login"][i] += 1
    
    # 11. Total time on-site
    sql = "SELECT sessions.course_user_id, sessions.duration, sessions.end_time FROM sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(0)
            else:
                value_array.append(None)
        learner_personality_map[learner]["time_on_site"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        if learner in learner_personality_map.keys():
            
            for i in range(len(time_array)):
                if end_time < time_array[i]:
                    learner_personality_map[learner]["time_on_site"][i] += duration
                     
        
    #####################################################################################
    '''
    # Query registration time
    enrolment_path = os.path.dirname(os.path.dirname(path)) + "/DelftX-EX101x-3T2015-student_courseenrollment-prod-analytics.sql"
    enrolment_file = open(enrolment_path, "r")
    enrolment_file.readline()
    lines = enrolment_file.readlines()
            
    for line in lines:
        record = line.split("\t")
        global_user_id = record[1]        
        time = record[3]
        
        format="%Y-%m-%d %H:%M:%S"
        time = datetime.datetime.strptime(time,format)
        
        if global_user_id in learner_personality_map.keys():
            learner_personality_map[global_user_id]["register_time"] = time
    
    
    # Filter based on registration time
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        time = learner_personality_map[learner]["register_time"]
        
        if time < reserved_course_start_time:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    learner_personality_map.clear()
    learner_personality_map = selected_learner_personality_map.copy()            
    
    print "# effective records is:\t" + str(len(learner_personality_map)) + "\n"
    '''
                
    for week in range(len(time_array)):
        
        output_path = path + "ten_weeks/all_learners/data_week_" + str(week)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "time_on_site"])
                
        week = int(week)
        for learner in learner_personality_map.keys():
            
            array = []
       
            array.append(learner_personality_map[learner]["result"]["Extroversion"])
            array.append(learner_personality_map[learner]["result"]["Agreeableness"])
            array.append(learner_personality_map[learner]["result"]["Conscientiousness"])
            array.append(learner_personality_map[learner]["result"]["Neuroticism"])
            array.append(learner_personality_map[learner]["result"]["Openness"])
        
            array.append(learner_personality_map[learner]["video_time"][week])
            array.append(learner_personality_map[learner]["quiz_time"][week])
            array.append(learner_personality_map[learner]["questions"][week])
            array.append(learner_personality_map[learner]["new_posts"][week])
            array.append(learner_personality_map[learner]["reply"][week])
            array.append(learner_personality_map[learner]["forum"][week])
            array.append(learner_personality_map[learner]["forum_time"][week])
            array.append(learner_personality_map[learner]["forum_login"][week])
        
            array.append(learner_personality_map[learner]["time_on_site"][week])
    
            writer.writerow(array)
            
        output_file.close()








path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
QueryWeeklyCourseMetrics(path)
print "Finished."

