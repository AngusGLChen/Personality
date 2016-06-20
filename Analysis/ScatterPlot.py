'''
Created on Jan 20, 2016

@author: Angus
'''

import csv
import matplotlib.pyplot as plt

def ScatterPlotAnalysis(path):
    
    # Read data
    file = open(path, "r")
    reader = csv.reader(file)
    
    header = reader.next()
    
    data = []
    for i in range(len(header)):
        data.append([])

    for row in reader:
        for i in range(len(row)):
            data[i].append(row[i])
            
    for i in range(5):
        for j in range(5, len(header)):
            x_name = header[i]
            y_name = header[j]
            
            x = data[i]
            y = data[j]
            
            print x_name + "\tvs.\t" + y_name
            
            plt.scatter(x, y)
            plt.show()
    
        
        
        
path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_results_completers"
ScatterPlotAnalysis(path)
print "Finished."