'''
Created on May 7, 2016

@author: Angus
'''

import csv
from sklearn import gaussian_process
from sklearn.ensemble import RandomForestRegressor
from scipy.stats.stats import pearsonr

def Prediction(data_path):
    
    personality_dimensions = ["Agreeableness", "Conscientiousness", "Extroversion", "Neuroticism", "Openness"]
    
    for dimension in personality_dimensions:
        
        print dimension
        
        for file_num in range(10):
            
            samples = []
            
            file_path = data_path + dimension + "_" + str(file_num) + ".csv"
            file = open(file_path, "r")
            reader = csv.reader(file)
            reader.next()
            for row in reader:
                array = []
                for element in row:
                    if element == "nan":
                        array.append(0)
                    else:
                        array.append(float(element))
                samples.append(array)
            
            actual_result = []
            gaussian_result = []
            forest_result = []
                
            for fold in range(10):
                
                traning = {}
                traning["X"] = []
                traning["Y"] = []
                
                testing = {}
                testing["X"] = []
                testing["Y"] = []
                
                for i in range(len(samples)):
                    array = samples[i]
                    if ((i % 10) == fold):
                        testing["X"].append(array[0:-2])
                        testing["Y"].append(array[-1])
                    else:
                        traning["X"].append(array[0:-2])
                        traning["Y"].append(array[-1])
                        
                # Gaussian process regression
                gp = gaussian_process.GaussianProcess()
                gp.fit(traning["X"], traning["Y"])
                gaussian_values = gp.predict(testing["X"], eval_MSE=False)
                
                # RandomForest Regressor
                rf = RandomForestRegressor(random_state=0, n_estimators=100)
                rf.fit(traning["X"], traning["Y"])
                forest_values = rf.predict(testing["X"])
            
                for element in testing["Y"]:
                    actual_result.append(element)
                
                for elment in gaussian_values:
                    gaussian_result.append(element)
                    
                for element in forest_values:
                    forest_result.append(element)
                
                
           
            gaussian_correlation = pearsonr(actual_result, gaussian_result)
            forest_correlation = pearsonr(actual_result, forest_result)  
            print str(gaussian_correlation[0]) + "\t" + str(gaussian_correlation[1]) + "\t" + str(forest_correlation[0]) + "\t" + str(forest_correlation[1])
            
        print
                
            
        
    
                    
                
                
            
            
        
    
    
    
    
    
data_path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/prediction/"
Prediction(data_path)
print "Finished."