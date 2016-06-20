'''
Created on Jan 3, 2016

@author: Angus
'''

import json

import numpy as np
import statsmodels
import statsmodels.api as sm
from regressors import regressors, stats



def RegressionAnalysis(path):
    
    # Read personality & demographic data
    input_file = open(path + "personality_results", "r")
    jsonLine = input_file.read()
    data_map = json.loads(jsonLine)
    input_file.close()
    
    learner_set = set()
    
    for learner in data_map.keys():
        learner_set.add(learner)
        
    #####################################################
    # 1. Y: video_time
    #    X: Gender, Age, Education, Personality
    
    Y = []
    X = []
    
    for learner in data_map.keys():
        
        Y.append(data_map[learner]["video_time"])
        
        X_array = []
        
        if data_map[learner]["gender"] == "f":
            X_array.append(1)
        else:
            X_array.append(0)
        
        X_array.append(data_map[learner]["age"])
        
        if data_map[learner]["education"] == "Bachelor":
            X_array.append(1)
            X_array.append(0)
        
        if data_map[learner]["education"] == "Graduate":
            X_array.append(0)
            X_array.append(1)
            
        if data_map[learner]["education"] == "Others":
            X_array.append(0)
            X_array.append(0)
            
        X_array.append(data_map[learner]["result"]["Agreeableness"])
        X_array.append(data_map[learner]["result"]["Neuroticism"])
        X_array.append(data_map[learner]["result"]["Extroversion"])
        X_array.append(data_map[learner]["result"]["Conscientiousness"])
        X_array.append(data_map[learner]["result"]["Openness"])
        
        X.append(X_array)
    
    print "Linear regression..."
    model = sm.OLS(Y, X).fit()
    print model.summary()
    
    print 
    
    for i in range(len(model.params)):
        print str(round(model.params[i], 3)) + " (" + str(round(model.bse[i], 3)) + ") " + str(round(model.pvalues[i], 3)) 
    
    print 
    print "PCA regression..."
    pcr = regressors.PCR(n_components=10, regression_type='ols')
    pcr.fit(X, Y)
    
    print pcr.beta_coef_

    
    

        
    
        
        
    
        
        
        
####################################################     
path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/"
RegressionAnalysis(path)
        
    
    
