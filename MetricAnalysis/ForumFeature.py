'''
Created on Jan 26, 2016

@author: Angus
'''

import mysql.connector, json

def ForumFeatureAnalysis(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    personality_path = path + "personality_scores"
    personality_file = open(personality_path, "r")
    learner_personality_map = json.loads(personality_file.read())
    personality_file.close()
    
    # Forum posts
    sql = "SELECT collaborations.course_user_id FROM collaborations"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    num_posts = 0
    post_learner_map = {}
    for result in results:        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        if learner in learner_personality_map.keys():
            num_posts += 1
            if learner not in post_learner_map.keys():
                post_learner_map[learner] = 0
            post_learner_map[learner] += 1
    
    print "# posts is:\t" + str(num_posts)
    print "# learners is:\t" + str(len(post_learner_map))
    
    num_5_posts = 0
    for learner in post_learner_map.keys():
        if post_learner_map[learner] > 5:
            num_5_posts += 1
            
    print "# 5 posts is:\t" + str(num_5_posts)
    
    
    
    
    



path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
ForumFeatureAnalysis(path)
print "Finished."
