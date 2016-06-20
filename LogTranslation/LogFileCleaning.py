'''
Created on Dec 21, 2015

@author: Angus
'''

import os
import json
    
def LogFileCleaning(path):
    
    files = os.listdir(path)
    for file in files:
        # Processing events log data
        if "events" in file:
            print file
        
            # Output clear-out file
            clear_out_path = os.path.dirname(os.path.dirname(path)) + "/Clear-out/EX101x-3T2015/" + file
            if os.path.isfile(clear_out_path):
                os.remove(clear_out_path)
        
            clear_out_file = open(clear_out_path, 'wb')
        
            fp = open(path + "/" + file,"r")   
            for line in fp:
                jsonObject = json.loads(line)            
                if "EX101x" in jsonObject["context"]["course_id"] and "3T2015" in jsonObject["context"]["course_id"]:
                    clear_out_file.write(line)
                
            clear_out_file.close()         


####################################################    
path = "/Volumes/NETAC/EdX/EX101x-3T2015/"
LogFileCleaning(path)
print "Finished."       

