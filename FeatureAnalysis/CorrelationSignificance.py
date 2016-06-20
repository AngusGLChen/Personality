'''
Created on Mar 7, 2016

@author: Angus
'''

import os
from scipy.stats.stats import pearsonr

def GenerateCorrelationSignificance(path):
    
    result_path = path + "prediction_correlation"
    files = os.listdir(result_path)
    
    format_path = path + "prediction_correlation_format"
    
    for file in files:
        input_path = result_path + "/" + file
        input_file = open(input_path, "r")
        input_file.readline()
        lines = input_file.readlines()
        
        output_path = format_path + "/" + file
        output_file = open(output_path, "w")
        output_file.write("truth,prediction\n")
        
        truth = []
        prediction = []
        
        for line in lines:
            
            while "  " in line:
                line = line.replace("  ", " ")
            
            
            array = line.split(" ")
            
            
            
            if len(array) == 1:
                continue
            
            
            
            truth.append(float(array[2]))
            prediction.append(float(array[3]))
            
            output_file.write(array[2] + "," + array[3] + "\n")
        
        print
        result = pearsonr(truth, prediction)
        significance = result[1]
        if significance < 0.05:
            print result
            print file
            
        output_file.close()
        
            
            
    
    
course_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
GenerateCorrelationSignificance(course_path)
print "Finished."
    

