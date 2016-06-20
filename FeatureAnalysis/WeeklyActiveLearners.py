'''
Created on Mar 4, 2016

@author: Angus
'''

import mysql.connector, datetime

def GenerateWeeklyActiveLearners(personality_path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
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
        
    while course_start_time < course_end_time:
        course_start_time += datetime.timedelta(days=7)
        time_array.append(course_start_time)
    
    week_active_learners_map = {}
    for i in range(len(time_array)):
        week_active_learners_map[i] = set()
    
    '''
    # 1. Active video learners
    sql = "SELECT observations.course_user_id, observations.end_time FROM observations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        for i in range(len(time_array)):
            if end_time < time_array[i]:
                week_active_learners_map[i].add(learner)
                break
            
    # 2. Active submission learners
    sql = "SELECT submissions.course_user_id, submissions.submission_timestamp FROM submissions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        time = result[1]
        
        for i in range(len(time_array)):
            if time < time_array[i]:
                week_active_learners_map[i].add(learner)
                break
    
    '''
    # 3. Active session learners
    sql = "SELECT sessions.course_user_id, sessions.end_time FROM sessions"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        end_time = result[1]
        
        for i in range(len(time_array)):
            if end_time < time_array[i]:
                week_active_learners_map[i].add(learner)
                break
          
    
            
    for i in range(len(time_array)):
        output_path = personality_path + str(i)
        output_file = open(output_path, "w")
        for learner in week_active_learners_map[i]:
            output_file.write(learner + "\n")
        output_file.close()
    
    
    
    
personality_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/active_learners/"
GenerateWeeklyActiveLearners(personality_path)
print "Finished."
    
        
    
