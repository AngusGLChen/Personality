'''
Created on Jan 23, 2016

@author: Angus
'''
from IPython.core.tests.test_formatters import numpy

'''
Created on Jan 21, 2016

@author: Angus
'''

import mysql.connector, json, datetime, os, csv

def getDayDiff(beginDate,endDate):  
    format="%Y-%m-%d"  
    bd = datetime.datetime.strptime(beginDate,format)  
    ed = datetime.datetime.strptime(endDate,format)      
    oneday = datetime.timedelta(days=1)  
    count = 0
    while bd != ed:  
        ed = ed - oneday  
        count += 1
    return count

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
            
    # Query resource timestamp
    resource_path = os.path.dirname(os.path.dirname(path)) + "/DelftX-EX101x-3T2015-course_structure-prod-analytics.json"
    resource_file = open(resource_path, "r")
    jsonLine = resource_file.read()
    
    children_parent_map = {}  
    resource_time_map = {}
    rescource_week_map = {}
    week_start_time_map = {}
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
        week = getDayDiff(course_start_date, resource_start_time[0:resource_start_time.index("T")]) / 7 + 1
        rescource_week_map[resource] = week
        
        format="%Y-%m-%d %H:%M:%S"
        resource_start_time = resource_start_time.replace("T", " ").replace("Z", "")
        resource_start_time = datetime.datetime.strptime(resource_start_time,format) 
        resource_time_map[resource] = resource_start_time
        week_start_time_map[week] = resource_start_time   
    
    # 1. Course start/end time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    course_end_time = ""
    
    for result in results:        
        course_start_time = result[0]
        course_end_time = result[1]
    
    '''
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
    '''    
    
    # 3. Video-watching time
    sql = "SELECT observations.course_user_id, observations.duration, observations.resource_id FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        for i in range(8):
            value_array.append(0)
        learner_personality_map[learner]["video_time"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        duration = result[1]
        resource_id = "block-v1:DelftX+EX101x+3T2015+type@video+block@" + result[2]
        
        if learner in learner_personality_map.keys():
            
            week = rescource_week_map[resource_id]
            learner_personality_map[learner]["video_time"][week - 1] += duration
    
    # 4. Questions
    sql = "SELECT submissions.course_user_id, submissions.problem_id FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        value_array = []
        for i in range(8):
            value_array.append(0)
        learner_personality_map[learner]["questions"] = value_array
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        question_id = result[1]
        
        if learner in learner_personality_map.keys():
            
            week = rescource_week_map[question_id]
            learner_personality_map[learner]["questions"][week - 1] += 1    
    
    # 5. Video time response
    sql = "SELECT observations.course_user_id, observations.resource_id, observations.start_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        average_value_array = []
        first_value_array = []
        for i in range(8):
            average_value_array.append([])
            first_value_array.append("")
        learner_personality_map[learner]["video_response_average"] = average_value_array
        learner_personality_map[learner]["video_response_first"] = first_value_array
    
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
            
            week = rescource_week_map[resource_id]
            learner_personality_map[learner]["video_response_average"][week - 1].append(time_difference)
            
            if learner_personality_map[learner]["video_response_first"][week - 1] == "":
                learner_personality_map[learner]["video_response_first"][week - 1] = time
            else:
                if time < learner_personality_map[learner]["video_response_first"][week - 1]:
                    learner_personality_map[learner]["video_response_first"][week - 1] = time
                    
    for learner in learner_personality_map.keys():
        for i in range(len(learner_personality_map[learner]["video_response_average"])):
            
            if len(learner_personality_map[learner]["video_response_average"][i]) == 0:
                learner_personality_map[learner]["video_response_average"][i] = None
                learner_personality_map[learner]["video_response_first"][i] = None
            else:
                average = numpy.average(learner_personality_map[learner]["video_response_average"][i])
                learner_personality_map[learner]["video_response_average"][i] = average
            
                week_start_time = week_start_time_map[i+1]
                learner_personality_map[learner]["video_response_first"][i] = (learner_personality_map[learner]["video_response_first"][i] - week_start_time).days * 24 * 60 * 60 + (learner_personality_map[learner]["video_response_first"][i] - week_start_time).seconds
            
    # 5. Question time response
    sql = "SELECT submissions.course_user_id, submissions.problem_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for learner in learner_personality_map.keys():
        average_value_array = []
        first_value_array = []
        for i in range(8):
            average_value_array.append([])
            first_value_array.append("")
        learner_personality_map[learner]["question_response_average"] = average_value_array
        learner_personality_map[learner]["question_response_first"] = first_value_array
    
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
            
            week = rescource_week_map[resource_id]
            learner_personality_map[learner]["question_response_average"][week - 1].append(time_difference)
            
            if learner_personality_map[learner]["question_response_first"][week - 1] == "":
                learner_personality_map[learner]["question_response_first"][week - 1] = time
            else:
                if time < learner_personality_map[learner]["question_response_first"][week - 1]:
                    learner_personality_map[learner]["question_response_first"][week - 1] = time
                    
    for learner in learner_personality_map.keys():
        for i in range(len(learner_personality_map[learner]["question_response_average"])):
            
            if len(learner_personality_map[learner]["question_response_average"][i]) == 0:
                learner_personality_map[learner]["question_response_average"][i] = None
                learner_personality_map[learner]["question_response_first"][i] = None
            else:
                average = numpy.average(learner_personality_map[learner]["question_response_average"][i])
                learner_personality_map[learner]["question_response_average"][i] = average
            
                week_start_time = week_start_time_map[i+1]
                learner_personality_map[learner]["question_response_first"][i] = (learner_personality_map[learner]["question_response_first"][i] - week_start_time).days * 24 * 60 * 60 + (learner_personality_map[learner]["question_response_first"][i] - week_start_time).seconds
            
    

    
    
    #####################################################################################
    '''
    # Filter based on registration time
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        time = learner_personality_map[learner]["register_time"]
        
        if time < course_start_time:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    learner_personality_map.clear()
    learner_personality_map = selected_learner_personality_map.copy()            
    
    print "# effective records is:\t" + str(len(learner_personality_map)) + "\n"
    '''
                
    for week in range(8):
        
        output_path = path + "eight_weeks/all_learners/data_week_" + str(week)
        output_file = open(output_path, "w")
        writer = csv.writer(output_file)
        writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "questions", "video_response_average", "video_response_first", "question_response_average", "question_response_first"])
                
        for learner in learner_personality_map.keys():
            
            array = []
       
            array.append(learner_personality_map[learner]["result"]["Extroversion"])
            array.append(learner_personality_map[learner]["result"]["Agreeableness"])
            array.append(learner_personality_map[learner]["result"]["Conscientiousness"])
            array.append(learner_personality_map[learner]["result"]["Neuroticism"])
            array.append(learner_personality_map[learner]["result"]["Openness"])
        
            array.append(learner_personality_map[learner]["video_time"][week])
            array.append(learner_personality_map[learner]["questions"][week])
            
            array.append(learner_personality_map[learner]["video_response_average"][week])
            array.append(learner_personality_map[learner]["video_response_first"][week])
            
            array.append(learner_personality_map[learner]["question_response_average"][week])
            array.append(learner_personality_map[learner]["question_response_first"][week])
    
            writer.writerow(array)
            
        output_file.close()








path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
QueryWeeklyCourseMetrics(path)
print "Finished."

