'''
Created on Jan 21, 2016

@author: Angus
'''

import os, mysql.connector, csv, datetime, json, numpy
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def CleanPersonalityData(path):
    
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
    
    learner_index = 25
    
    start_time_index = 7
    end_time_index = 8
    
    question_start_index = 38
    question_end_index = 87
    
    learner_personality_map = {}
    
    row_num = 0
    respondent_set = set()
    for row in result_reader:
        row_num += 1
        
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
    print "# effective data records is:\t" + str(len(learner_personality_map))
    
    # 3. Filter results
    full_duration_array = []
    for learner in learner_personality_map.keys():
        full_duration_array.append(learner_personality_map[learner]["duration"])
    
    # Threshold version
    lower_bound = 3
    upper_bound = 12
    selected_duration_array = []
    for element in full_duration_array:
        if element >= lower_bound and element <= upper_bound:
            selected_duration_array.append(element)
    print "# remaining repondents is:\t" + str(len(selected_duration_array)) + "\n"
    
    
    # Plot of the distribution of the time learners spent in filling out the questionnaire
    fig, ax = plt.subplots(figsize=(9, 5))
    bins = numpy.arange(0,21,1)
    _, bins, patches = plt.hist(full_duration_array, bins, normed=True, color=['#3782CC'],)
    
    xlabels = numpy.array(bins[1:], dtype='|S4')
    xlabels[-1] = '20'
    
    N_labels = len(xlabels)
    
    plt.xticks(1*numpy.arange(N_labels) + 1)
    ax.set_xticklabels(xlabels)
    plt.setp(patches, linewidth=0.5)
    
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:3.0f}%'.format(x*100) for x in vals])
    
    ax.set_ylabel('Percentage')
    ax.set_xlabel('Time used to complete the questionnaire (in min.)')
    
    plt.show()
    
    
    selected_learner_personality_map = {}
    for learner in learner_personality_map.keys():
        duration = learner_personality_map[learner]["duration"]
        if duration >= lower_bound and duration <= upper_bound:
            selected_learner_personality_map[learner] = learner_personality_map[learner]
    
    # 4. Calculate the personality scores
    print "Testing"
    personality_result_map = {}
    for learner in selected_learner_personality_map.keys():
        array = selected_learner_personality_map[learner]["result"]
        # print array
        # print
        E = 20 + array[0] - array[5] + array[10] - array[15] + array[20] - array[25] + array[30] - array[35] + array[40] - array[45]
        A = 14 - array[1] + array[6] - array[11] + array[16] - array[21] + array[26] - array[31] + array[36] + array[41] + array[46]
        C = 14 + array[2] - array[7] + array[12] - array[17] + array[22] - array[27] + array[32] - array[37] + array[42] + array[47]
        N = 38 - array[3] + array[8] - array[13] + array[18] - array[23] - array[28] - array[33] - array[38] - array[43] - array[48]
        O = 8  + array[4] - array[9] + array[14] - array[19] + array[24] - array[29] + array[34] + array[39] + array[44] + array[49]
        
        personality_result_map[learner] = [E, A, C, N, O]
        selected_learner_personality_map[learner]["result"] = {"Extroversion": E, "Agreeableness": A, "Conscientiousness": C, "Neuroticism": N, "Openness": O}
    
    # 5. Get learners' registration time
    # 5.1 Course start/mid time
    sql = "SELECT courses.course_start_time, courses.course_end_time FROM courses"
    cursor.execute(sql)
    results = cursor.fetchall()
    
    course_start_time = ""
    for result in results:        
        course_start_time = result[0]
        
    course_mid_time = course_start_time + datetime.timedelta(days=28)
    
    # 5.2 Learners' enrollment time
    enrolment_path = os.path.dirname(os.path.dirname(path)) + "/DelftX-EX101x-3T2015-student_courseenrollment-prod-analytics.sql"
    enrolment_file = open(enrolment_path, "r")
    enrolment_file.readline()
    lines = enrolment_file.readlines()
    
    learner_register_time_map = {}
            
    for line in lines:
        record = line.split("\t")
        global_user_id = record[1]        
        time = record[3]
        
        format="%Y-%m-%d %H:%M:%S";
        time = datetime.datetime.strptime(time,format)
        
        learner_register_time_map[global_user_id] = time
        
        if global_user_id in selected_learner_personality_map.keys():
            selected_learner_personality_map[global_user_id]["register_time"] = str(time)
            
    # 5.3 Analysis
    num_before_start_time = 0
    num_before_mid_time = 0
    num_before_end_time = 0
    for learner in selected_learner_personality_map.keys():
        
        time = learner_register_time_map[learner]
        if time < course_start_time:
            num_before_start_time += 1
        else:
            if time < course_mid_time:
                num_before_mid_time += 1
            else:
                num_before_end_time += 1
                
        # Filter
        # if time > course_start_time:
        #     personality_result_map.pop(learner)
      
    print "Enrolment time distribution:\t" + str(num_before_start_time) + "\t" + str(num_before_mid_time) + "\t" + str(num_before_end_time) + "\n"
    
           
    
    # 6. Analyze personality results
    personality_score_array = [[], [], [], [], []]
    for learner in personality_result_map.keys():
        for i in range(len(personality_score_array)):
            personality_score_array[i].append(personality_result_map[learner][i])
    
    
    # Histogram
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
    
    fig, ax = plt.subplots(figsize=(9, 5))   
    plt.hist([mean_array[0], mean_array[1], mean_array[2], mean_array[3], mean_array[4]], label=[label_array[0], label_array[1], label_array[2], label_array[3], label_array[4]], alpha=0.5)
    
    ax.set_ylabel('# learners')
    ax.set_xlabel('Personality scores')
    
    plt.legend(loc='upper left')    
    plt.show()
    
    
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
    
    output_path = os.path.dirname(os.path.dirname(path)) + "/personality_analysis/personality_scores"
    output_file = open(output_path, "w")
    output_file.write(json.dumps(selected_learner_personality_map))
    output_file.close()






































path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_questionnaire_data/"
#path = "/Users/Angus/Downloads/2015_12_14_Questionnaire_data/"
CleanPersonalityData(path)
print "Finished."
