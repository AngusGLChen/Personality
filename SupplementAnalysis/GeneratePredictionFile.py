'''
Created on Feb 25, 2016

@author: Angus
'''

import mysql.connector, os, json, csv, numpy, datetime
import matplotlib.pyplot as plt

def GenerateWekaFile(course_path, personality_path, survey_path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
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
    
    # 3. Query registration time
    enrolment_path = os.path.dirname(os.path.dirname(course_path)) + "/DelftX-EX101x-3T2015-student_courseenrollment-prod-analytics.sql"
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
    resource_path = os.path.dirname(os.path.dirname(course_path)) + "/DelftX-EX101x-3T2015-course_structure-prod-analytics.json"
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
    
    
    
                
    # 14. # videos skipped
    sql = "SELECT resources.resource_id, resources.relevant_week FROM resources WHERE resources.resource_type = \"video\""
    cursor.execute(sql)
    results = cursor.fetchall()
    
    video_num_array = []
    for i in range(len(time_array)):
        video_num_array.append(0)
    
    for result in results:
        resource_id = result[0]
        week = result[1] - 1
        for i in range(len(video_num_array)):
            if week <= i:
                video_num_array[i] += 1
                
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(set())
            else:
                value_array.append(None)
        learner_personality_map[learner]["skip_videos"] = value_array
    
    sql = "SELECT observations.course_user_id, observations.resource_id, observations.end_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        video_id = result[1]
        time = result[2]
        
        for i in range(len(time_array)):
            if time < time_array[i]:
                if learner in learner_personality_map.keys():
                    learner_personality_map[learner]["skip_videos"][i].add(video_id)
    
    for learner in learner_personality_map.keys():
        for i in range(len(time_array)):
            if learner_personality_map[learner]["skip_videos"][i] == None:
                learner_personality_map[learner]["skip_videos"][i] = 0
            else:
                num_skip_videos = video_num_array[i] - len(learner_personality_map[learner]["skip_videos"][i])
                learner_personality_map[learner]["skip_videos"][i] = num_skip_videos
        
    
    # 15. # videos sped up
    sql = "SELECT observations.course_user_id, observations.resource_id, observations.end_time FROM observations WHERE observations.times_speedUp != 0"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        register_time = learner_personality_map[learner]["register_time"]
        for i in range(len(time_array)):
            if register_time < time_array[i]:
                value_array.append(set())
            else:
                value_array.append(None)
        learner_personality_map[learner]["speed_up_videos"] = value_array
    
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        video_id = result[1]
        end_time = result[2]
        
        for i in range(len(time_array)):
            if end_time < time_array[i]:
                if learner in learner_personality_map.keys():
                    learner_personality_map[learner]["speed_up_videos"][i].add(video_id)
    
    for learner in learner_personality_map.keys():
        for i in range(len(time_array)):
            
            if learner_personality_map[learner]["speed_up_videos"][i] == None:
                learner_personality_map[learner]["speed_up_videos"][i] = 0
            else:
                num_speed_up_videos = video_num_array[i] - len(learner_personality_map[learner]["speed_up_videos"][i])
                learner_personality_map[learner]["speed_up_videos"][i] = num_speed_up_videos
    
    
    # 15. Maximum/Avg/STD session time
    sql = "SELECT sessions.course_user_id, sessions.duration, sessions.end_time FROM sessions"
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
        learner_personality_map[learner]["max_session_time"] = value_array
        learner_personality_map[learner]["avg_session_time"] = value_array
        learner_personality_map[learner]["std_session_time"] = value_array
    
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        for i in range(len(time_array)):
            if end_time < time_array[i]:
                if learner in learner_personality_map.keys():
                    learner_personality_map[learner]["max_session_time"][i].append(duration)
                    learner_personality_map[learner]["avg_session_time"][i].append(duration)
                    learner_personality_map[learner]["std_session_time"][i].append(duration)
                    
    for learner in learner_personality_map.keys():
        
        for i in range(len(time_array)):
            
            if learner_personality_map[learner]["max_session_time"][i] == None:
                learner_personality_map[learner]["max_session_time"][i] = 0
                learner_personality_map[learner]["avg_session_time"][i] = 0
                learner_personality_map[learner]["std_session_time"][i] = 0
            else:
                
                if len(learner_personality_map[learner]["max_session_time"][i]) == 0:
                    max = 0
                    avg = 0
                    std = 0
                else:
                    max = numpy.max(learner_personality_map[learner]["max_session_time"][i])
                
                    avg = numpy.average(learner_personality_map[learner]["avg_session_time"][i])
                    std = numpy.std(learner_personality_map[learner]["std_session_time"][i])
        
                learner_personality_map[learner]["max_session_time"][i] = max
                learner_personality_map[learner]["avg_session_time"][i] = avg
                learner_personality_map[learner]["std_session_time"][i] = std
    
    
    # 16. Avg/STD quiz time
    sql = "SELECT quiz_sessions.course_user_id, quiz_sessions.duration, quiz_sessions.end_time FROM quiz_sessions"
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
        learner_personality_map[learner]["avg_quiz_time"] = value_array
        learner_personality_map[learner]["std_quiz_time"] = value_array
        
    
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        end_time = result[2]
        
        for i in range(len(time_array)):
            if end_time < time_array[i]:
                if learner in learner_personality_map.keys():
                    learner_personality_map[learner]["avg_quiz_time"][i].append(duration)
                    learner_personality_map[learner]["std_quiz_time"][i].append(duration)
    
    for learner in learner_personality_map.keys():
        
        for i in range(len(time_array)):
            
            if learner_personality_map[learner]["avg_quiz_time"][i] == None:
                learner_personality_map[learner]["avg_quiz_time"][i] = 0
                learner_personality_map[learner]["std_quiz_time"][i] = 0
            else:
                
                avg = numpy.average(learner_personality_map[learner]["avg_quiz_time"][i])
                std = numpy.std(learner_personality_map[learner]["std_quiz_time"][i])
        
                learner_personality_map[learner]["avg_quiz_time"][i] = avg
                learner_personality_map[learner]["std_quiz_time"][i] = std
    
    '''
    # 17. STD watching time per week
    sql = "SELECT observations.course_user_id, observations.duration, resources.relevant_week FROM observations, resources WHERE CONCAT(\"block-v1:DelftX+EX101x+3T2015+type@video+block@\", observations.resource_id)=resources.resource_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_videos_week_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        week = result[2]
        
        if learner not in learner_videos_week_map.keys():
            learner_videos_week_map[learner] = [0,0,0,0,0,0,0,0]
        learner_videos_week_map[learner][week - 1] += duration
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_videos_week_map.keys():
            learner_personality_map[learner]["std_videos"] = 0
            continue
        
        std_videos = numpy.std(learner_videos_week_map[learner])
        learner_personality_map[learner]["std_videos"] = std_videos
    '''

    
    #####################################################################################         
    for week in range(len(time_array)):
        
        personality_array = ["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness"]
        
        for personality_dimension in personality_array:
            
            output_path = course_path + "prediction/" + personality_dimension + "_" + str(week) + ".csv"
            output_file = open(output_path, "w")
            writer = csv.writer(output_file)
        
            writer.writerow(["motivation", "prior_knowledge", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", "skip_videos", "speed_up_videos", "max_session_time", "avg_session_time", "std_session_time", "avg_quiz_time", "std_quiz_time", personality_dimension])
            #writer.writerow(["prior_knowledge", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", personality_dimension])
        
            week = int(week)
            
            #############################################
            active_learners_set = set()
            
            active_path = course_path + "active_learners/" + str(week)
            active_file = open(active_path, "r")
            lines = active_file.readlines()
            for line in lines:
                id = line.replace("\n", "")
                active_learners_set.add(id)
            active_file.close()
            #############################################
            
            
            for learner in learner_personality_map.keys():
                
                #if week != len(time_array) - 1:
                #    continue
                
                if learner_personality_map[learner]["register_time"] > time_array[week]:
                    continue
                
                if learner not in active_learners_set:
                    continue
            
                array = []
                
                array.append(learner_personality_map[learner]["motivation"])
            
                array.append(learner_personality_map[learner]["prior_knowledge"])
        
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
                
                
                ####################################################################
                
                if learner_personality_map[learner]["skip_videos"][week] == None:
                    learner_personality_map[learner]["skip_videos"][week] = 0
                if learner_personality_map[learner]["speed_up_videos"][week] == None:
                    learner_personality_map[learner]["speed_up_videos"][week] = 0
                if learner_personality_map[learner]["max_session_time"][week] == None:
                    learner_personality_map[learner]["max_session_time"][week] = 0
                if learner_personality_map[learner]["avg_session_time"][week] == None:
                    learner_personality_map[learner]["avg_session_time"][week] = 0
                if learner_personality_map[learner]["std_session_time"][week] == None:
                    learner_personality_map[learner]["std_session_time"][week] = 0
                if learner_personality_map[learner]["avg_quiz_time"][week] == None:
                    learner_personality_map[learner]["avg_quiz_time"][week] = 0
                if learner_personality_map[learner]["std_quiz_time"][week] == None:
                    learner_personality_map[learner]["std_quiz_time"][week] = 0
                    
                array.append(learner_personality_map[learner]["skip_videos"][week])
                array.append(learner_personality_map[learner]["speed_up_videos"][week])
                
                array.append(learner_personality_map[learner]["max_session_time"][week])
                array.append(learner_personality_map[learner]["avg_session_time"][week])
                array.append(learner_personality_map[learner]["std_session_time"][week])
                
                array.append(learner_personality_map[learner]["avg_quiz_time"][week])
                array.append(learner_personality_map[learner]["std_quiz_time"][week])
                
                # array.append(learner_personality_map[learner]["std_videos"][week])
                       
                ####################################################################
                
                array.append(learner_personality_map[learner]["result"][personality_dimension] * 0.125)
             
                writer.writerow(array)
            
        output_file.close()
    
             
                            
                        
course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"                       
personality_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/personality_scores"
survey_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/survey/"
GenerateWekaFile(course_path, personality_path, survey_path)
print "Finished."
