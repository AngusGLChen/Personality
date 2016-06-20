import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import os, json, csv, time,datetime, operator, mysql.connector

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

def getNextDay(current_day_string):
    format="%Y-%m-%d";
    current_day = datetime.datetime.strptime(current_day_string,format)
    oneday = datetime.timedelta(days=1)
    next_day = current_day + oneday   
    return str(next_day)[0:10]

def cmp_datetime(a_datetime, b_datetime):
    if a_datetime < b_datetime:
        return -1
    elif a_datetime > b_datetime:
        return 1
    else:
        return 0 

def CalculateTotalNumEvents(path):
    
    # Connect to the database
    connection = mysql.connector.connect(user='root', password='admin', host='127.0.0.1', database='Personality')
    cursor = connection.cursor()
    
    total_num = 0
    
    # Course information
    global_course_id = ""
    course_start_date = ""
    course_end_date = ""
    
    # Processing course_structure data
    metadata_files = os.listdir(path)           
    for file in metadata_files:             
        if "course_structure" in file: 
            
            # To extract course_id     
            course_id_array = file.split("-")
            global_course_id = "course-v1:" + course_id_array[0] + "+" + course_id_array[1] + "+" + course_id_array[2]
                       
            fp = open(path + file,"r")            
            lines = fp.readlines()
            jsonLine = ""   
            for line in lines:
                line = line.replace("\n","")
                jsonLine += line    
            
            jsonObject = json.loads(jsonLine)
            for record in jsonObject:
                if jsonObject[record]["category"] == "course":
                    # To obtain the course_start_date
                    course_start_date = jsonObject[record]["metadata"]["start"]
                    course_start_date = course_start_date[0:course_start_date.index("T")]
                    # To obtain the course_end_date
                    course_end_date = jsonObject[record]["metadata"]["end"]
                    course_end_date = course_end_date[0:course_end_date.index("T")]        
                    
    # Processing events data 
    current_date = course_start_date   
    course_end_next_date = getNextDay(course_end_date)
    
    log_files = os.listdir(path)
    
    while True:
        
        if current_date == course_end_next_date:
            break;
        
        for file in log_files:           
            if current_date in file:
                
                print file
                fp = open(path + file,"r")
                lines = fp.readlines()
                
                total_num += len(lines)
                        
        print total_num
        current_date = getNextDay(current_date)
                

course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/"
CalculateTotalNumEvents(course_path)
print "Finished."

