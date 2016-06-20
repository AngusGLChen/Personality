'''
Created on Jan 23, 2016

@author: Angus
'''

import mysql.connector, json, datetime, os, csv, numpy
import matplotlib.pyplot as plt

def QueryWeeklyCourseMetrics(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    # Personality scores
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
    
    # Query resource timestamp
    resource_path = os.path.dirname(os.path.dirname(path)) + "/DelftX-EX101x-3T2015-course_structure-prod-analytics.json"
    resource_file = open(resource_path, "r")
    jsonLine = resource_file.read()
    
    children_parent_map = {}  
    resource_time_map = {}
    resource_without_time = []    
            
    jsonObject = json.loads(jsonLine)
    for record in jsonObject:
        if jsonObject[record]["category"] == "course":
            # To obtain the course_start_date
            course_start_date = jsonObject[record]["metadata"]["start"]
            course_start_date = course_start_date[0:course_start_date.index("T")]
            # To obtain the course_end_date
            course_end_date = jsonObject[record]["metadata"]["end"]
            course_end_date = course_end_date[0:course_end_date.index("T")]
        else:
            resourse_id = record
                    
            # Children to parent relation                    
            for child in jsonObject[resourse_id]["children"]:
                children_parent_map[child] = resourse_id                                     
                                                
            # Time information about resources
            if "start" in jsonObject[resourse_id]["metadata"]:
                resource_start_time = jsonObject[resourse_id]["metadata"]["start"]
                resource_time_map[resourse_id] = resource_start_time
            else:
                resource_without_time.append(resourse_id)
                
    # To determine the start_time for all resource 
    for resource in resource_without_time:
                
        resource_start_time = ""
                             
        while resource_start_time == "":                     
            resource_parent = children_parent_map[resource]
            while not resource_time_map.has_key(resource_parent):
                resource_parent = children_parent_map[resource_parent]
            resource_start_time = resource_time_map[resource_parent]
                
            resource_time_map[resource] = resource_start_time
            
    # To determine the relevant week for all resource
    for resource in resource_time_map:
                
        resource_start_time = resource_time_map[resource]          
                
        format="%Y-%m-%d %H:%M:%S"
        resource_start_time = resource_start_time.replace("T", " ").replace("Z", "")
        resource_start_time = datetime.datetime.strptime(resource_start_time,format) 
        resource_time_map[resource] = resource_start_time 
        
    # Partition ids
    partition_id_set = set()
    id_path = path + "prior_knowledge/partition_id_1"
    id_file = open(id_path, "r")
    lines = id_file.readlines()
    for line in lines:
        id = line.replace("\n", "")
        partition_id_set.add(id)
    
        
    update_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        if learner in partition_id_set:
            update_learner_personality_map[learner] = learner_personality_map[learner]
            
    learner_personality_map.clear()
    learner_personality_map = update_learner_personality_map
    
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
                
    # 9. Forum interaction friends
    sql = "SELECT collaborations.collaboration_id, collaborations.collaboration_type, collaborations.course_user_id, collaborations.collaboration_parent_id, collaborations.collaboration_thread_id, collaborations.collaboration_timestamp FROM collaborations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    forum_map = {}
    thread_learners_map = {}
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(set())
            else:
                value_array.append(None)
        learner_personality_map[learner]["forum_friends"] = value_array
    
    for result in results:
        collaboration_id = result[0]
        type = result[1]    
        learner = result[2].replace("course-v1:DelftX+EX101x+3T2015_", "")
        parent_id = result[3]
        thread_id = result[4]
        time = result[5]
          
        forum_map[collaboration_id] = {"type": type, "learner": learner, "parent_id": parent_id, "thread_id":thread_id, "time": time}
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["CommentThread_discussion", "CommentThread_question"]:
            learner = forum_map[collaboration_id]["learner"]
            time = forum_map[collaboration_id]["time"]
            thread_learners_map[collaboration_id] = set()            
            thread_learners_map[collaboration_id].add((learner, time))
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["Comment"]:
            thread_id = forum_map[collaboration_id]["thread_id"]
            learner = forum_map[collaboration_id]["learner"]
            time = forum_map[collaboration_id]["time"]
            thread_learners_map[thread_id].add((learner, time))
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["Comment_Reply"]:
            parent_id = forum_map[collaboration_id]["parent_id"]
            thread_id = forum_map[parent_id]["thread_id"]
            learner = forum_map[collaboration_id]["learner"]
            time = forum_map[collaboration_id]["time"]
            thread_learners_map[thread_id].add((learner, time))
            
    for thread_id in thread_learners_map.keys():
        
        for tuple in thread_learners_map[thread_id]:
            
            learner = tuple[0]
            time = tuple[1]
            
            if learner in learner_personality_map.keys():
            
                for i in range(len(time_array)):
                    if time < time_array[i]:
                        for pair in thread_learners_map[thread_id]:
                            friend = pair[0]
                            learner_personality_map[learner]["forum_friends"][i].add(friend)
            
    for learner in learner_personality_map.keys():
        for i in range(len(time_array)):
            if learner_personality_map[learner]["forum_friends"][i] != None:
                learner_personality_map[learner]["forum_friends"][i] = len(learner_personality_map[learner]["forum_friends"][i])
    
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
                
    # 11. Video time response
    sql = "SELECT observations.course_user_id, observations.resource_id, observations.start_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append([])
            else:
                value_array.append(None)
        learner_personality_map[learner]["video_response"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        resource_id = "block-v1:DelftX+EX101x+3T2015+type@video+block@" + result[1]
        time = result[2]
        
        if learner in learner_personality_map.keys():
            
            release_time = resource_time_map[resource_id]
            time_difference = (time - release_time).days * 24 * 60 * 60 + (time - release_time).seconds
            
            for i in range(len(time_array)):
                if time < time_array[i]:
                    learner_personality_map[learner]["video_response"][i].append(time_difference)
                    
    for learner in learner_personality_map.keys():
        for i in range(len(time_array)):
            if learner_personality_map[learner]["video_response"][i] != None:
                if len(learner_personality_map[learner]["video_response"][i]) == 0:
                    learner_personality_map[learner]["video_response"][i] = 0
                else:
                    learner_personality_map[learner]["video_response"][i] = numpy.average(learner_personality_map[learner]["video_response"][i])
    
    # 12. Question time response
    sql = "SELECT submissions.course_user_id, submissions.problem_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append([])
            else:
                value_array.append(None)
        learner_personality_map[learner]["question_response"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        resource_id = result[1]
        time = result[2]
        
        
        if learner in learner_personality_map.keys():
            
            release_time = resource_time_map[resource_id]
            time_difference = (time - release_time).days * 24 * 60 * 60 + (time - release_time).seconds
            
            for i in range(len(time_array)):
                if time < time_array[i]:
                    learner_personality_map[learner]["question_response"][i].append(time_difference)
                    
    for learner in learner_personality_map.keys():
        for i in range(len(time_array)):
            if learner_personality_map[learner]["question_response"][i] != None:
                if len(learner_personality_map[learner]["question_response"][i]) == 0:
                    learner_personality_map[learner]["question_response"][i] = 0
                else:
                    learner_personality_map[learner]["question_response"][i] = numpy.average(learner_personality_map[learner]["video_response"][i])
    
    
    #####################################################################################         
    for week in range(len(time_array)):
        
        output_path = path + "prior_knowledge/ten_weeks/partition_1/" + str(week)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", "video_response", "question_response"])
                
        week = int(week)
        
        #############################################
        active_learners_set = set()
            
        active_path = path + "active_learners/" + str(week)
        active_file = open(active_path, "r")
        lines = active_file.readlines()
        for line in lines:
            id = line.replace("\n", "")
            active_learners_set.add(id)
        active_file.close()
        #############################################
        
        for learner in learner_personality_map.keys():
            
            array = []
            
            if learner not in active_learners_set:
                continue
       
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
            array.append(learner_personality_map[learner]["forum_friends"][week])
        
            array.append(learner_personality_map[learner]["time_on_site"][week])
            array.append(learner_personality_map[learner]["video_response"][week])
            array.append(learner_personality_map[learner]["question_response"][week])
    
            writer.writerow(array)
            
        output_file.close()
    







path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
QueryWeeklyCourseMetrics(path)
print "Finished."

