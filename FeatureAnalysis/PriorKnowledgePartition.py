'''
Created on Jan 27, 2016

@author: Angus
'''

import mysql.connector, os, json, csv, numpy, datetime
import matplotlib.pyplot as plt

def PriorKnowledgePartition(course_path, personality_path, survey_path):
    
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
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
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
        update_learner_personality_map[learner] = learner_personality_map[learner]
        update_learner_personality_map[learner]["prior_knowledge"] = survey_learner_map[learner]
    
    learner_personality_map.clear()
    learner_personality_map = update_learner_personality_map.copy()
            
    print "# personality learners is:\t" + str(len(learner_personality_map))
    
    '''
    # Histogram
    value_array = []
    bins = []
    for i in range(5,75):
        if i % 5 == 0:
            bins.append(i)
    for learner in learner_personality_map.keys():
        value_array.append(learner_personality_map[learner]["prior_knowledge"])
            
    plt.hist(value_array, bins, alpha=0.5)
    plt.show()
    '''
    '''
    # Plot of the distribution of the time learners spent in filling out the questionnaire
    plt.hist(concept_distribution_array, label=["Pivot Tables", "Named Ranges", "Array Formulas", "Graph Databases", "Python"])
    plt.legend()
    plt.show()
    '''
    
    # Course material usage
    
    # Query registration time
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
            learner_personality_map[learner]["new_posts"] = None
    
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
            learner_personality_map[learner]["reply"] = None
            
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
            learner_personality_map[learner]["forum"] = None
            
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
            
    # 13. Final score
    sql = "SELECT course_user.course_user_id, course_user.certificate_status, course_user.final_grade FROM course_user"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_certificate_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        status = result[1]
        grade = result[2]
        learner_certificate_map[learner] = {"status": status, "grade": grade}
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_certificate_map.keys():
            learner_personality_map[learner]["certification"] = "notpassing"
            learner_personality_map[learner]["grade"] = 0
            continue
        
        status = learner_certificate_map[learner]["status"]
        grade = learner_certificate_map[learner]["grade"]
        
        learner_personality_map[learner]["certification"] = status
        learner_personality_map[learner]["grade"] = grade
        
    # 14. # videos skipped
    sql = "SELECT observations.course_user_id, observations.resource_id FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_videos_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        video_id = result[1]
        if learner not in learner_videos_map.keys():
            learner_videos_map[learner] = set()
        learner_videos_map[learner].add(video_id)
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_videos_map.keys():
            learner_personality_map[learner]["skip_videos"] = 60
            continue
        
        num_skip_videos = 60 - len(learner_videos_map[learner])
        learner_personality_map[learner]["skip_videos"] = num_skip_videos
        
    # 15. # videos sped up
    sql = "SELECT observations.course_user_id, observations.resource_id FROM observations WHERE observations.times_speedUp != 0"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_speed_up_videos_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        video_id = result[1]
        if learner not in learner_speed_up_videos_map.keys():
            learner_speed_up_videos_map[learner] = set()
        learner_speed_up_videos_map[learner].add(video_id)
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_speed_up_videos_map.keys():
            learner_personality_map[learner]["speed_up_videos"] = 0
            continue
        
        num_speed_up_videos = len(learner_speed_up_videos_map[learner])
        learner_personality_map[learner]["speed_up_videos"] = num_speed_up_videos
    
    # 15. Maximum/Avg/STD session time
    sql = "SELECT sessions.course_user_id, sessions.duration FROM sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_sessions_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        if learner not in learner_sessions_map.keys():
            learner_sessions_map[learner] = []
        learner_sessions_map[learner].append(duration)
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_sessions_map.keys():
            learner_personality_map[learner]["max_session_time"] = 0
            learner_personality_map[learner]["avg_session_time"] = 0
            learner_personality_map[learner]["std_session_time"] = 0
            continue
        
        max = numpy.max(learner_sessions_map[learner])
        avg = numpy.average(learner_sessions_map[learner])
        std = numpy.std(learner_sessions_map[learner])
        
        learner_personality_map[learner]["max_session_time"] = max
        learner_personality_map[learner]["avg_session_time"] = avg
        learner_personality_map[learner]["std_session_time"] = std
    
    
    # 16. Avg/STD quiz time
    sql = "SELECT quiz_sessions.course_user_id, quiz_sessions.duration FROM quiz_sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    learner_quiz_sessions_map = {}
    for result in results:
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        if learner not in learner_quiz_sessions_map.keys():
            learner_quiz_sessions_map[learner] = []
        learner_quiz_sessions_map[learner].append(duration)
    
    for learner in learner_personality_map.keys():
        
        if learner not in learner_quiz_sessions_map.keys():
            learner_personality_map[learner]["avg_quiz_time"] = 0
            learner_personality_map[learner]["std_quiz_time"] = 0
            continue
        
        avg = numpy.average(learner_quiz_sessions_map[learner])
        std = numpy.std(learner_quiz_sessions_map[learner])
        
        learner_personality_map[learner]["avg_quiz_time"] = avg
        learner_personality_map[learner]["std_quiz_time"] = std
    
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
    
    
            
    # Partition
    
    bins = 2
    
    '''
    # (1) Equal version
    sorted_learner_personality_map = sorted(learner_personality_map.items(), key=lambda learner_personality_map: learner_personality_map[1]["prior_knowledge"])              
    length = len(sorted_learner_personality_map)
    for i in range(bins):
        
        output_path = course_path + "prior_knowledge/partition_" + str(i)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", "video_response_average", "question_response_average"])
        
        start = length / bins * i
        end = length / bins * (i + 1)
        
        if i == bins - 1:
            end = length
        
        for j in range(start, end):
            tuple = sorted_learner_personality_map[j]
            
            array = []        
            array.append(tuple[1]["result"]["Extroversion"])
            array.append(tuple[1]["result"]["Agreeableness"])
            array.append(tuple[1]["result"]["Conscientiousness"])
            array.append(tuple[1]["result"]["Neuroticism"])
            array.append(tuple[1]["result"]["Openness"])
        
            array.append(tuple[1]["video_time"])
            array.append(tuple[1]["quiz_time"])
            array.append(tuple[1]["questions"])
            array.append(tuple[1]["new_posts"])
            array.append(tuple[1]["reply"])
            array.append(tuple[1]["forum"])
            array.append(tuple[1]["forum_time"])
            array.append(tuple[1]["forum_login"])
            array.append(tuple[1]["forum_friends"])
        
            array.append(tuple[1]["time_on_site"])
        
            array.append(tuple[1]["video_response_average"])
            array.append(tuple[1]["question_response_average"])       
            
            writer.writerow(array)
    
        output_file.close()
    
    '''
    # (2) Interval version
    
    ###################################################################
    active_learners_map = {}
    for i in range(10):
        active_path = course_path + "active_learners/" + str(i)
        active_file = open(active_path, "r")
        lines = active_file.readlines()
        for line in lines:
            id = line.replace("\n", "")
            if id not in active_learners_map.keys():
                active_learners_map[id] = 0
            active_learners_map[id] += 1
        active_file.close()
    ###################################################################
    
    bin_array = []
    bin_array.append([5, 30])
    bin_array.append([30, 76])
    
    for i in range(bins):
        
        output_path = course_path + "prior_knowledge/partition_" + str(i)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "forum_login", "forum_friends", "time_on_site", "video_response_average", "question_response_average", "final_score", "skip_videos", "speed_up_videos", "max_session_time", "avg_session_time", "std_session_time", "avg_quiz_time", "std_quiz_time", "std_videos"])
        
        
        id_output_path = course_path + "prior_knowledge/partition_id_" + str(i)
        id_output_file = open(id_output_path, "w")
        
        num_learners = 0
        
        for learner in learner_personality_map.keys():
            
            ##########################################
            #if active_learners_map[learner] < 4:
            #    continue
            ##########################################
            
            prior_knowledge = learner_personality_map[learner]["prior_knowledge"]
            
            start = bin_array[i][0]
            end = bin_array[i][1]
            
            if prior_knowledge >= start and prior_knowledge < end:
                
                num_learners += 1
            
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
                
                array.append(learner_personality_map[learner]["grade"])
                
                '''
                array.append(learner_personality_map[learner]["skip_videos"])
                array.append(learner_personality_map[learner]["speed_up_videos"])
                
                array.append(learner_personality_map[learner]["max_session_time"])
                array.append(learner_personality_map[learner]["avg_session_time"])
                array.append(learner_personality_map[learner]["std_session_time"])
                
                array.append(learner_personality_map[learner]["avg_quiz_time"])
                array.append(learner_personality_map[learner]["std_quiz_time"])
                array.append(learner_personality_map[learner]["std_videos"])
                '''
                
                writer.writerow(array)
                
                id_output_file.write(learner + "\n")
    
        output_file.close()
        id_output_file.close()
        print "# learners is:\t" + str(num_learners)

    
    
    
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                            
                            
                        
course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"                       
personality_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/personality_scores"
survey_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/survey/"
PriorKnowledgePartition(course_path, personality_path, survey_path)
print "Finished."