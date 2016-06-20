'''
Created on Dec 23, 2015

@author: Angus
'''

import mysql.connector

def GetBasicStatistics(course_id):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    # 1. # engaged learners
    sql = "SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\"" 
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "# learners is:\t" + str(results[0][0])
    
    # 2. Completion rate
    sql = "SELECT CONCAT(ROUND(COUNT(course_user.course_user_id) / (SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\")*100, 2), \"%\") FROM course_user, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T WHERE course_user.course_user_id=T.course_user_id AND course_user.certificate_status=\"downloadable\""
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Completion rate is:\t" + str(results[0][0])
    
    # 3. Avg. time watching video material (in  min.)
    sql = "SELECT ROUND(SUM(observations.duration) / (SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") / 60, 2) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\""
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Avg. time watching video material (in  min.) is:\t" + str(results[0][0])
    
    # 4. % Learners who tried at least one question
    sql = "SELECT CONCAT(ROUND(COUNT(DISTINCT(submissions.course_user_id))/(SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\")*100,2),\"%\") FROM submissions, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T WHERE submissions.course_user_id=T.course_user_id"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "% Learners who tried at least one question is:\t" + str(results[0][0])
    
    # 5. Avg. # questions learners attempted to solve
    sql = "SELECT ROUND(COUNT(assessments.assessment_id)/(SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\"),2) FROM assessments, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T1 WHERE assessments.course_user_id=T1.course_user_id"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Avg. # questions learners attempted to solve is:\t" + str(results[0][0])
    
    # 6. Avg. # questions answered correctly
    sql = "SELECT ROUND(COUNT(assessments.assessment_id)/(SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\"),2) FROM assessments, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T1 WHERE assessments.course_user_id=T1.course_user_id AND assessments.grade!=0"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Avg. # questions answered correctly is:\t" + str(results[0][0])
    
    # 7. Avg. accuracy of learners' answers
    sql = "SELECT CONCAT(ROUND(SUM(T3.Accuracy) / (SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\")*100,2),\"%\")  FROM ( SELECT COUNT(assessments.assessment_id)/T2.Num_attempts AS Accuracy FROM assessments, (SELECT assessments.course_user_id, COUNT(assessments.assessment_id) AS Num_attempts  FROM assessments, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T1 WHERE assessments.course_user_id=T1.course_user_id GROUP BY assessments.course_user_id ) AS T2 WHERE assessments.course_user_id=T2.course_user_id AND assessments.max_grade!=0 GROUP BY assessments.course_user_id ) AS T3"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Avg. accuracy of learners' answers is:\t" + str(results[0][0])
    
    # 8. # Forum posts
    sql = "SELECT COUNT(collaborations.collaboration_id) FROM collaborations, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T WHERE collaborations.course_user_id=T.course_user_id"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "# Forum posts is:\t" + str(results[0][0])
    
    # 9. % Learners who posted at least once
    sql = "SELECT CONCAT(ROUND(COUNT(DISTINCT(collaborations.course_user_id)) / ((SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\")) * 100, 2), \"%\") FROM collaborations, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T WHERE collaborations.course_user_id=T.course_user_id"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "% Learners who posted at least once is:\t" + str(results[0][0])
    
    # 10. Avg. # posts per learner
    sql = "SELECT ROUND(COUNT(collaborations.collaboration_id) / (SELECT COUNT(DISTINCT(observations.course_user_id)) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\"), 2) FROM collaborations, (SELECT DISTINCT(observations.course_user_id) FROM observations, global_user WHERE observations.course_user_id=global_user.course_user_id AND global_user.course_id=\"" + course_id + "\") AS T1 WHERE collaborations.course_user_id=T1.course_user_id"
    
    cursor.execute(sql)
    results = cursor.fetchall()
    print "Avg. # posts per learner:\t" + str(results[0][0])



##############################
course_id = "course-v1:DelftX+EX101x+3T2015"
GetBasicStatistics(course_id)
print "Finished."