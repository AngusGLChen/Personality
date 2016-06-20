'''
Created on Jan 21, 2016

@author: Angus
'''

import mysql.connector, json, datetime, os, csv, numpy
import matplotlib.pyplot as plt


def QueryCourseMetrics(path):
    
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
    
    # 1. Course start/end time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    for result in results:        
        course_start_time = result[0]
    
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
    sql = "SELECT observations.course_user_id, ROUND(SUM(observations.duration) / 60, 2) FROM observations GROUP BY observations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            video_time = result[1]
            learner_personality_map[learner]["video_time"] = video_time
            
    for learner in learner_personality_map.keys():
        if "video_time" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["video_time"] = 0
            
    # 4. Quiz-solving time
    sql = "SELECT quiz_sessions.course_user_id, ROUND(SUM(quiz_sessions.duration) / 60, 2) FROM quiz_sessions GROUP BY quiz_sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            quiz_time = result[1]
            learner_personality_map[learner]["quiz_time"] = quiz_time
            
    for learner in learner_personality_map.keys():
        if "quiz_time" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["quiz_time"] = 0
            
    # 5. Questions
    sql = "SELECT submissions.course_user_id, COUNT(*) FROM submissions GROUP BY submissions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            num_questions = result[1]
            learner_personality_map[learner]["questions"] = num_questions
            
    for learner in learner_personality_map.keys():
        if "questions" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["questions"] = 0
            
    # 4. New posts
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations WHERE collaborations.collaboration_type=\"CommentThread_discussion\" or collaborations.collaboration_type=\"CommentThread_question\" GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            num_posts = result[1]
            learner_personality_map[learner]["new_posts"] = num_posts
            
    for learner in learner_personality_map.keys():
        if "new_posts" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["new_posts"] = 0
    
    # 5. Reply
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations WHERE collaborations.collaboration_type=\"Comment\" or collaborations.collaboration_type=\"Comment_Reply\" GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            num_reply = result[1]
            learner_personality_map[learner]["reply"] = num_reply
            
    for learner in learner_personality_map.keys():
        if "reply" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["reply"] = 0
            
    # 6. New posts + Reply
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            num_forum = result[1]
            learner_personality_map[learner]["forum"] = num_forum
            
    for learner in learner_personality_map.keys():
        if "forum" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["forum"] = 0
            
    # 7. Forum-browsing time
    sql = "SELECT forum_sessions.course_user_id, ROUND(SUM(forum_sessions.duration) / 60, 2) FROM forum_sessions GROUP BY forum_sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            forum_time = result[1]
            learner_personality_map[learner]["forum_time"] = forum_time
            
    for learner in learner_personality_map.keys():
        if "forum_time" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["forum_time"] = 0
            
    # 8. # Forum login
    sql = "SELECT forum_sessions.course_user_id, COUNT(*) FROM forum_sessions GROUP BY forum_sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            forum_login = result[1]
            learner_personality_map[learner]["forum_login"] = forum_login
            
    for learner in learner_personality_map.keys():
        if "forum_login" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["forum_login"] = 0
     
    # 9. Forum interaction friends
    sql = "SELECT collaborations.collaboration_id, collaborations.collaboration_type, collaborations.course_user_id, collaborations.collaboration_parent_id, collaborations.collaboration_thread_id FROM collaborations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    forum_map = {}
    thread_learners_map = {}
    
    for result in results:
        collaboration_id = result[0]
        type = result[1]    
        learner = result[2].replace("course-v1:DelftX+EX101x+3T2015_", "")
        parent_id = result[3]
        thread_id = result[4]
          
        forum_map[collaboration_id] = {"type": type, "learner": learner, "parent_id": parent_id, "thread_id":thread_id}
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["CommentThread_discussion", "CommentThread_question"]:
            learner = forum_map[collaboration_id]["learner"]
            thread_learners_map[collaboration_id] = set()            
            thread_learners_map[collaboration_id].add(learner)
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["Comment"]:
            thread_id = forum_map[collaboration_id]["thread_id"]
            learner = forum_map[collaboration_id]["learner"]
            thread_learners_map[thread_id].add(learner)
            
    for collaboration_id in forum_map.keys():
        if forum_map[collaboration_id]["type"] in ["Comment_Reply"]:
            parent_id = forum_map[collaboration_id]["parent_id"]
            thread_id = forum_map[parent_id]["thread_id"]
            learner = forum_map[collaboration_id]["learner"]
            thread_learners_map[thread_id].add(learner)
    
    forum_friends_map = {}
    for thread_id in thread_learners_map.keys():
        
        for learner in thread_learners_map[thread_id]:
            if learner not in forum_friends_map.keys():
                forum_friends_map[learner] = set()
            for friend in thread_learners_map[thread_id]:
                forum_friends_map[learner].add(friend)    
            
    for learner in learner_personality_map.keys():
        if "forum_friends" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["forum_friends"] = 0
        if learner in forum_friends_map.keys():
            learner_personality_map[learner]["forum_friends"] = len(forum_friends_map[learner])
    
    # 10. Total time on-site
    sql = "SELECT sessions.course_user_id, ROUND(SUM(sessions.duration) / 60, 2) FROM sessions GROUP BY sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")        
        if learner in learner_personality_map.keys():
            time_on_site = result[1]
            learner_personality_map[learner]["time_on_site"] = time_on_site
            
    for learner in learner_personality_map.keys():
        if "time_on_site" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["time_on_site"] = 0 
            
    # 11. Video time response
    sql = "SELECT observations.course_user_id, observations.resource_id, observations.start_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    video_reponse_map = {}
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        resource_id = "block-v1:DelftX+EX101x+3T2015+type@video+block@" + result[1]
        time = result[2]
        
        if learner in learner_personality_map.keys():
            
            release_time = resource_time_map[resource_id]            
            register_time = learner_personality_map[learner]["register_time"]
            
            if register_time > release_time:
                release_time = register_time
                
            time_difference = (time - release_time).days * 24 * 60 * 60 + (time - release_time).seconds
            
            if learner not in video_reponse_map.keys():
                video_reponse_map[learner] = []
            video_reponse_map[learner].append(time_difference)
                    
    for learner in learner_personality_map.keys():
        if "video_response_average" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["video_response_average"] = None
        if learner in video_reponse_map.keys():
            average = numpy.average(video_reponse_map[learner])
            learner_personality_map[learner]["video_response_average"] = average       
            
    # 12. Question time response
    sql = "SELECT submissions.course_user_id, submissions.problem_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    question_reponse_map = {}
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        resource_id = result[1]
        time = result[2]
        
        if learner in learner_personality_map.keys():
            
            release_time = resource_time_map[resource_id]            
            register_time = learner_personality_map[learner]["register_time"]
            
            if register_time > release_time:
                release_time = register_time
                
            time_difference = (time - release_time).days * 24 * 60 * 60 + (time - release_time).seconds
            
            if learner not in question_reponse_map.keys():
                question_reponse_map[learner] = []
            question_reponse_map[learner].append(time_difference)
                    
    for learner in learner_personality_map.keys():
        if "question_response_average" not in learner_personality_map[learner].keys():
            learner_personality_map[learner]["question_response_average"] = None
        if learner in question_reponse_map.keys():
            average = numpy.average(question_reponse_map[learner])
            learner_personality_map[learner]["question_response_average"] = average
        
    #####################################################################################
    '''
    # Filter based on registration time
    format="%Y-%m-%d %H:%M:%S"
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        time = learner_personality_map[learner]["register_time"]        
        # time = datetime.datetime.strptime(time,format)
        
        if time < course_start_time:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    learner_personality_map.clear()
    learner_personality_map = selected_learner_personality_map.copy()            
    
            
    print "# effective records is:\t" + str(len(learner_personality_map)) + "\n"
    '''
    '''
    # Boxplot
    personality_score_array = [[], [], [], [], []]
    for learner in selected_learner_personality_map.keys():
        personality_score_array[0].append(selected_learner_personality_map[learner]["result"]["Extroversion"])
        personality_score_array[1].append(selected_learner_personality_map[learner]["result"]["Agreeableness"])
        personality_score_array[2].append(selected_learner_personality_map[learner]["result"]["Conscientiousness"])
        personality_score_array[3].append(selected_learner_personality_map[learner]["result"]["Neuroticism"])
        personality_score_array[4].append(selected_learner_personality_map[learner]["result"]["Openness"])
        
    fig = plt.figure(1, figsize=(9, 6))
    ax = fig.add_subplot(111)
    bp = ax.boxplot(personality_score_array)
    
    for box in bp['boxes']:
        box.set( color='#7570b3', linewidth=2)
        #box.set( facecolor = '#1b9e77' )        
    for whisker in bp['whiskers']:
        whisker.set(color='#7570b3', linewidth=2)        
    for cap in bp['caps']:
        cap.set(color='#7570b3', linewidth=2)
    for median in bp['medians']:
        median.set(color='#ff3300', linewidth=2)        
    for flier in bp['fliers']:
        flier.set(marker='o', color='#7570b3', alpha=0.5)        
    ax.set_xticklabels(["E", "A", "C", "N", "O"])   
    plt.show()
    '''
    
    
    output_path = path + "/whole_course_all_learners"
    output_file = open(output_path, "w")
    writer = csv.writer(output_file)
    writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", "video_response_average", "question_response_average"])
    
    for learner in learner_personality_map.keys():
        
        array = []        
        array.append(learner_personality_map[learner]["result"]["Extroversion"])
        array.append(learner_personality_map[learner]["result"]["Agreeableness"])
        array.append(learner_personality_map[learner]["result"]["Conscientiousness"])
        array.append(learner_personality_map[learner]["result"]["Neuroticism"])
        array.append(learner_personality_map[learner]["result"]["Openness"])
        
        array.append(learner_personality_map[learner]["video_time"])
        array.append(learner_personality_map[learner]["quiz_time"])
        array.append(learner_personality_map[learner]["questions"])
        array.append(learner_personality_map[learner]["new_posts"])
        array.append(learner_personality_map[learner]["reply"])
        array.append(learner_personality_map[learner]["forum"])
        array.append(learner_personality_map[learner]["forum_time"])
        array.append(learner_personality_map[learner]["forum_login"])
        array.append(learner_personality_map[learner]["forum_friends"])
        
        array.append(learner_personality_map[learner]["time_on_site"])
        
        array.append(learner_personality_map[learner]["video_response_average"])
        array.append(learner_personality_map[learner]["question_response_average"])       
        
        
        writer.writerow(array)
    
    output_file.close()
    








path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
QueryCourseMetrics(path)
print "Finished."
