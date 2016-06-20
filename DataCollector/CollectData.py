'''
Created on Dec 23, 2015

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
        
    #index = -1
    
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
        
        '''
        # Searching for index
        if row_num == 1:
            question_id_row = row
            for i in range(len(question_id_row)):
                if question_id_row[i] == "Q2.1_30":
                    index = i
                    print "The index of element is:\t" + str(i)
        
        if row_num == 2:
            question_row = row
            print "The question element value is:\t" + str(question_row[index])
            print
            
        if row_num < 50 and row_num > 2:
            print "The element value is:\t" + str(row[index])
        '''
        
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
    
    # Analysis:
    print "# total responses is:\t" + str(len(respondent_set))
    print "# unmatched data records is:\t" + str(num_unmatched_ids)
    print "# effective data records is:\t" + str(len(learner_personality_map)) + "\n"
    
    full_duration_array = []
    for learner in learner_personality_map.keys():
        full_duration_array.append(learner_personality_map[learner]["duration"])
        
    lower_bound = 3
    upper_bound = 12
    
    # Threshold version
    duration_array = []
    for element in full_duration_array:
        #if element >= lower_bound and element <= upper_bound:
        duration_array.append(element)

    print "# repondents is:\t" + str(len(duration_array))

    '''
    # Plot of the distribution of the time learners spent in filling out the questionnaire
    fig, ax = pylab.subplots(figsize=(9, 5))
    bins = numpy.arange(0,21,1)
    _, bins, patches = pylab.hist(duration_array, bins, normed=True, color=['#3782CC'],)
    
    xlabels = numpy.array(bins[1:], dtype='|S4')
    xlabels[-1] = '20'
    
    N_labels = len(xlabels)
    
    pylab.xticks(1*numpy.arange(N_labels) + 1)
    ax.set_xticklabels(xlabels)
    pylab.setp(patches, linewidth=0)
    
    pylab.show()
    '''
    
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        duration = learner_personality_map[learner]["duration"]
        if duration >= lower_bound and duration <= upper_bound:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
            
    print "# remaining repondents is:\t" + str(len(selected_learner_personality_map))
            
    personality_result_map = {}
    for learner in selected_learner_personality_map.keys():
        array = selected_learner_personality_map[learner]["result"]
        E = 20 + array[0] - array[5] + array[10] - array[15] + array[20] - array[25] + array[30] - array[35] + array[40] - array[45]
        A = 14 - array[1] + array[6] - array[11] + array[16] - array[21] + array[26] - array[31] + array[36] + array[41] + array[46]
        C = 14 + array[2] - array[7] + array[12] - array[17] + array[22] - array[27] + array[32] - array[37] + array[42] + array[47]
        N = 38 - array[3] + array[8] - array[13] + array[18] - array[23] - array[28] - array[33] - array[38] - array[43] - array[48]
        O = 8  + array[4] - array[9] + array[14] - array[19] + array[24] - array[29] + array[34] + array[39] + array[44] + array[49]
        
        #personality_result_map[learner] = [E, A, C, N, O]
        selected_learner_personality_map[learner]["result"] = {"Extroversion": E, "Agreeableness": A, "Conscientiousness": C, "Neuroticism": N, "Openness": O}
               
    
    # Analyze personality results
    personality_score_array = [[], [], [], [], []]
    
    # Histogram
    '''  
    for learner in personality_result_map.keys():
        for i in range(len(personality_score_array)):
            personality_score_array[i].append(personality_result_map[learner][i])
    print "Mean of results..."
    statistics_array = []
    for i in range(len(personality_score_array)):
        average = round(numpy.average(personality_score_array[i]), 2)
        std = round(numpy.std(personality_score_array[i]), 2)
        statistics_array.append({"average": average, "std": std})
    
    label_array = []
    label_array.append(u'E ({0} \u00B1 {1})'.format(statistics_array[0]["average"] , statistics_array[0]["std"]))
    label_array.append(u'A ({0} \u00B1 {1})'.format(statistics_array[1]["average"] , statistics_array[1]["std"]))
    label_array.append(u'C ({0} \u00B1 {1})'.format(statistics_array[2]["average"] , statistics_array[2]["std"]))
    label_array.append(u'N ({0} \u00B1 {1})'.format(statistics_array[3]["average"] , statistics_array[3]["std"]))
    label_array.append(u'O ({0} \u00B1 {1})'.format(statistics_array[4]["average"] , statistics_array[4]["std"]))    
    
    mean_array = [[], [], [], [], []]
    for learner in personality_result_map.keys():
        for i in range(len(mean_array)):
            mean_array[i].append(personality_result_map[learner][i])
            
    pylab.hist([mean_array[0], mean_array[1], mean_array[2], mean_array[3], mean_array[4]], label=[label_array[0], label_array[1], label_array[2], label_array[3], label_array[4]], alpha=0.5)
            
    pylab.legend(loc='upper left')    
    pylab.show()
    '''
    
    '''
    # Boxplot
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
    
    
    # 1. Gender/Age/Education
    sql = "SELECT user_pii.course_user_id, user_pii.gender, user_pii.year_of_birth, user_pii.level_of_education FROM user_pii"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    num_empty_gender = 0
    num_empty_age = 0
    num_empty_education = 0
    
    gender_map = {}
    age_map = {}
    
    age_map["<20"] = set()
    age_map["20-30"] = set()
    age_map["30-40"] = set()
    age_map[">40"] = set()
    age_map["Unknown"] = set()
    
    education_map = {}
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner not in selected_learner_personality_map.keys():
            continue
        
        gender = result[1]
        age = result[2]
        education = result[3]
        
        # Gender
        if gender not in ["m", "f"]:
            num_empty_gender += 1
            gender = "Unknown"
        
        if gender not in gender_map.keys():
            gender_map[gender] = set()
        gender_map[gender].add(learner)
            
        # Age
        if age == 0:
            num_empty_age += 1
            age_map["Unknown"].add(learner)
        else:
            age =  2015 - int(age)
        
        if age < 20:
            age_map["<20"].add(learner)
        if age >= 20 and age < 30:
            age_map["20-30"].add(learner)    
        if age >= 30 and age < 40:
            age_map["30-40"].add(learner)
        if age >= 40:
            age_map[">40"].add(learner)
        
        # Education
        if education not in ["p", "m", "b", "a", "hs", "jhs", "el", "none", "other", "p_se", "p_oth"]:
            num_empty_education += 1
            education = "Unknown"
        
        if education in ["p", "p_se", "p_oth", "m"]:
            education = "Graduate"

        if education in ["b", "a"]:
            education = "Bachelor"
                
        if education in ["hs", "jhs", "el", "none", "other"]:
            education = "Others"
                
        if education not in education_map.keys():
            education_map[education] = set()
        education_map[education].add(learner)
        
        # Store demographic information
        selected_learner_personality_map[learner]["gender"] = gender
        selected_learner_personality_map[learner]["age"] = age
        selected_learner_personality_map[learner]["education"] = education
        
        
        if gender in ["m", "f"] and age != 0 and education in ["p", "m", "b", "a", "hs", "jhs", "el", "none", "other", "p_se", "p_oth"]:
            
            selected_learner_personality_map[learner]["gender"] = gender
            
            age = 2015 - int(age)
            selected_learner_personality_map[learner]["age"] = age
            
            
            # Statistics
            if gender not in gender_map.keys():
                gender_map[gender] = set()
            gender_map[gender].add(learner)
            
            if age < 20:
                age_map["<20"].add(learner)
            if age >= 20 and age < 30:
                age_map["20-30"].add(learner)    
            if age >= 30 and age < 40:
                age_map["30-40"].add(learner)
            if age >= 40:
                age_map[">40"].add(learner)
            
            #if education in ["p", "p_se", "p_oth"]:
            #    education = "Doctoral"
            #if education in ["m"]:
            #    education = "Master"
                
            if education in ["p", "p_se", "p_oth", "m"]:
                education = "Graduate"
            
            #if education in ["b"]:
            #    education = "Bachelor"
            #if education in ["a"]:
            #    education = "Associate degree"
            
            if education in ["b", "a"]:
                education = "Bachelor"
                
            if education in ["hs", "jhs", "el", "none", "other"]:
                education = "Others"
                
            if education not in education_map.keys():
                education_map[education] = set()
            education_map[education].add(learner)
            
            selected_learner_personality_map[learner]["education"] = education
        
        
    
    print "# of empty gender data records is:\t" + str(num_empty_gender)
    print "# of empty age data records is:\t" + str(num_empty_age)
    print "# of empty education data records is:\t" + str(num_empty_education)
    print "# of non-empty data records is:\t" + str(len(selected_learner_personality_map)) + "\n"
            
    print "Demographic statistics..."
    print "Gender..."
    for gender in gender_map.keys():
        print gender + "\t" + str(len(gender_map[gender])) + " (" + str(round(len(gender_map[gender])/float(len(selected_learner_personality_map))*100, 2)) + "%)"
    print
    
    print "Age..."
    for age in age_map.keys():
        print age + "\t" + str(len(age_map[age])) + " (" + str(round(len(age_map[age])/float(len(selected_learner_personality_map))*100, 2)) + "%)"
    print
    
    print "Education..."
    for education in education_map.keys():
        print education + "\t" + str(len(education_map[education])) + " (" + str(round(len(education_map[education])/float(len(selected_learner_personality_map))*100, 2)) + "%)"
    print
    
    
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
    # selected_learner_personality_map.clear()
    # selected_learner_personality_map = completer_map.copy()
    
    print "# unmatched ids is:\t" + str(num_unmatched_ids)
    print "# selected completers is:\t" + str(num_completers) + "\n"
    
    '''
    # Boxplot - Completers' personality resultse
    boxplot_completer_personality_results = [[], [], [], [], []]
    for learner in completer_map.keys():
        for i in range(len(boxplot_completer_personality_results)):
            boxplot_completer_personality_results[i].append(personality_result_map[learner][i])

    fig = plt.figure(1, figsize=(9, 6))
    ax = fig.add_subplot(111)
    bp = ax.boxplot(boxplot_completer_personality_results)
    
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
    
    # 3. Video-watching time
    sql = "SELECT observations.course_user_id, ROUND(SUM(observations.duration) / 60, 2) FROM observations GROUP BY observations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            video_time = result[1]
            selected_learner_personality_map[learner]["video_time"] = video_time
            
    for learner in selected_learner_personality_map.keys():
        if "video_time" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["video_time"] = 0
            
    # 4. Quiz-solving time
    sql = "SELECT quiz_sessions.course_user_id, ROUND(SUM(quiz_sessions.duration) / 60, 2) FROM quiz_sessions GROUP BY quiz_sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            quiz_time = result[1]
            selected_learner_personality_map[learner]["quiz_time"] = quiz_time
            
    for learner in selected_learner_personality_map.keys():
        if "quiz_time" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["quiz_time"] = 0
            
    # 5. Questions
    sql = "SELECT submissions.course_user_id, COUNT(*) FROM submissions GROUP BY submissions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            num_questions = result[1]
            selected_learner_personality_map[learner]["questions"] = num_questions
            
    for learner in selected_learner_personality_map.keys():
        if "questions" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["questions"] = 0
            
    # 4. New posts
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations WHERE collaborations.collaboration_type=\"CommentThread_discussion\" or collaborations.collaboration_type=\"CommentThread_question\" GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            num_posts = result[1]
            selected_learner_personality_map[learner]["new_posts"] = num_posts
            
    for learner in selected_learner_personality_map.keys():
        if "new_posts" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["new_posts"] = 0
    
    # 5. Reply
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations WHERE collaborations.collaboration_type=\"Comment\" or collaborations.collaboration_type=\"Comment_Reply\" GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            num_reply = result[1]
            selected_learner_personality_map[learner]["reply"] = num_reply
            
    for learner in selected_learner_personality_map.keys():
        if "reply" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["reply"] = 0
            
    # 6. New posts + Reply
    sql = "SELECT collaborations.course_user_id, COUNT(*) FROM collaborations GROUP BY collaborations.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            num_forum = result[1]
            selected_learner_personality_map[learner]["forum"] = num_forum
            
    for learner in selected_learner_personality_map.keys():
        if "forum" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["forum"] = 0
            
    # 7. Forum-browsing time
    sql = "SELECT forum_sessions.course_user_id, ROUND(SUM(forum_sessions.duration) / 60, 2) FROM forum_sessions GROUP BY forum_sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            forum_time = result[1]
            selected_learner_personality_map[learner]["forum_time"] = forum_time
            
    for learner in selected_learner_personality_map.keys():
        if "forum_time" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["forum_time"] = 0
    
    
    # 8. Total time on-site
    sql = "SELECT sessions.course_user_id, ROUND(SUM(sessions.duration) / 60, 2) FROM sessions GROUP BY sessions.course_user_id"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    for result in results:
        
        learner = result[0].replace("course-v1:DelftX+EX101x+3T2015_", "")
        
        if learner in selected_learner_personality_map.keys():
            time_on_site = result[1]
            selected_learner_personality_map[learner]["time_on_site"] = time_on_site
            
    for learner in selected_learner_personality_map.keys():
        if "time_on_site" not in selected_learner_personality_map[learner].keys():
            selected_learner_personality_map[learner]["time_on_site"] = 0        
    
    
    #####################################################################################
    
    print "# effective records is:\t" + str(len(selected_learner_personality_map)) + "\n"

    output_path = os.path.dirname(os.path.dirname(path)) + "/personality_results_active_learners"
    output_file = open(output_path, "w")
    writer = csv.writer(output_file)
    #output_file.write(json.dumps(selected_learner_personality_map))
    #writer.writerow(["gender_female", "age", "education_bachelor", "education_graduate", "Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "time_on_site"])
    writer.writerow(["Extroversion", "Agreeableness", "Conscientiousness", "Neuroticism", "Openness", "video_time", "quiz_time", "questions", "new_posts", "reply", "forum", "forum_time", "time_on_site"])
    
    for learner in selected_learner_personality_map.keys():
        
        record = selected_learner_personality_map[learner]
        
        array = []
        
        '''
        if selected_learner_personality_map[learner]["gender"] == "f":
            array.append(1)
        else:
            array.append(0)
        
        array.append(selected_learner_personality_map[learner]["age"])
        
        if selected_learner_personality_map[learner]["education"] == "Bachelor":
            array.append(1)
            array.append(0)
        
        if selected_learner_personality_map[learner]["education"] == "Graduate":
            array.append(0)
            array.append(1)
            
        if selected_learner_personality_map[learner]["education"] == "Others":
            array.append(0)
            array.append(0)
        '''
        
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
    
    output_file.close()

  


path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_questionnaire_data/"
CollectPersonalityData(path)
print "Finished."



