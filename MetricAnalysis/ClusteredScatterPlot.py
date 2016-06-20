'''
Created on Jan 25, 2016

@author: Angus
'''

import csv
import matplotlib.pyplot as plt
from scipy.interpolate import spline

import numpy as np
import scipy as sp
import scipy.stats

def mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * sp.stats.t._ppf((1+confidence)/2., n-1)
    return m, m-h, m+h

def DrawClusterScatterPlot(path):
    
    path = path + "whole_course_all_learners"
    file = open(path, "r")
    reader = csv.reader(file)
    
    header = reader.next()
    num_bins = 10
    
    data = []
    for i in range(len(header)):
        data.append([])

    for row in reader:
        for i in range(len(row)):
            data[i].append(row[i])
            
    for i in range(5, len(header)):
                
        y_name = header[i]
        y_values = data[i]
        
        for j in range(5):
            
            array = []
                        
            x_name = header[j]
            x_values = data[j]
            
            print x_name + "\tvs.\t" + y_name
            for k in range(len(x_values)):
                if y_values[k] != "":
                    array.append((float(x_values[k]), float(y_values[k])))
            
            array = sorted(array, key=lambda array: array[0])
            
            x_mean_array = []
            y_mean_array = []
            
            length = len(array)
            for m in range(num_bins):
                start = length / num_bins * m
                end = length / num_bins * (m + 1)
                sum = 0
                count = 0
                for n in range(start, end):
                    if array[n][1] != "":
                        sum += float(array[n][1]) / 60
                        count += 1
                sum /= count
                
                x_mean_array.append(m)
                y_mean_array.append(sum)
            
            update_x_mean_array = []
            update_y_mean_array = []
            
            for m in range(num_bins):
                update_x_mean_array.append(x_mean_array[m])
                update_y_mean_array.append(y_mean_array[m]) 
                
            #plt.plot(x_mean_array, y_mean_array)
            #plt.plot(update_x_mean_array, update_y_mean_array)

            x_sm = np.array(update_x_mean_array)
            y_sm = np.array(update_y_mean_array)

            x_smooth = np.linspace(x_sm.min(), x_sm.max(), 200)
            y_smooth = spline(update_x_mean_array, update_y_mean_array, x_smooth)
          
            plt.plot(x_smooth, y_smooth)
        
        plt.legend(['Extroversion', 'Agreeableness', 'Conscientiousness', 'Neuroticism', 'Openness'], loc='best')
        
        plt.show()
                
            
def DrawClusterScatterPlotEqualInterval(path):
    
    path = path + "whole_course_all_learners"
    file = open(path, "r")
    reader = csv.reader(file)
    
    header = reader.next()
    num_bins = 10
    
    data = []
    for i in range(len(header)):
        data.append([])

    for row in reader:
        for i in range(len(row)):
            data[i].append(row[i])
            
    for i in range(5, len(header)):
                
        y_name = header[i]
        y_values = data[i]
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel(y_name)
        
        for j in range(5):
            
            array = []
                        
            x_name = header[j]
            x_values = data[j]
            
            print x_name + "\tvs.\t" + y_name
            for k in range(len(x_values)):
                if y_values[k] != "":
                    array.append((float(x_values[k]), float(y_values[k])))
            
            x_mean_array = []
            y_mean_array = []
            count_array = []
            
            for m in range(num_bins):
                x_mean_array.append(40/num_bins*(m+1))
                y_mean_array.append(0)
                count_array.append(0)
                
            for m in range(len(array)):
                personality_value = array[m][0]
                metric_value = array[m][1]
                
                n = 0
                while n < num_bins:
                    if personality_value <= x_mean_array[n]:
                        y_mean_array[n] += metric_value
                        count_array[n] += 1
                        break
                    n += 1
            
            for m in range(num_bins):
                if count_array[m] > 0:
                    y_mean_array[m] /= float(count_array[m])
            
            update_x_mean_array = []
            update_y_mean_array = []
            

            for m in range(num_bins):
                if count_array[m] >= 50:
                    update_x_mean_array.append(x_mean_array[m])
                    update_y_mean_array.append(y_mean_array[m])
                    
            x_sm = np.array(update_x_mean_array)
            y_sm = np.array(update_y_mean_array)

            x_smooth = np.linspace(x_sm.min(), x_sm.max(), 200)
            y_smooth = spline(update_x_mean_array, update_y_mean_array, x_smooth)
          
            plt.plot(x_smooth, y_smooth)
        
        plt.legend(['Extroversion', 'Agreeableness', 'Conscientiousness', 'Neuroticism', 'Openness'], loc='best')
        
        plt.show()
        
def DrawClusterScatterPlotEqualInterval95(path):
    
    path = path + "whole_course_all_learners"
    file = open(path, "r")
    reader = csv.reader(file)
    
    header = reader.next()
    num_bins = 10
    
    data = []
    for i in range(len(header)):
        data.append([])

    for row in reader:
        for i in range(len(row)):
            data[i].append(row[i])
            
    for i in range(5, len(header)):
                
        y_name = header[i]
        y_values = data[i]
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel(y_name)
        
        for j in range(5):
            
            array = []
                        
            x_name = header[j]
            x_values = data[j]
            
            print x_name + "\t" + y_name
            
            if y_name in ["new_posts"]:
                break
             
            
            for k in range(len(x_values)):
                if y_values[k] != "":
                    array.append((float(x_values[k]), float(y_values[k])))
            
            x_mean_array = []
            y_mean_array = []
            count_array = []
            
            for m in range(num_bins):
                x_mean_array.append(40/num_bins*(m+1))
                y_mean_array.append([])
                count_array.append(0)
                
            for m in range(len(array)):
                personality_value = array[m][0]
                metric_value = array[m][1]
                
                n = 0
                while n < num_bins:
                    if personality_value <= x_mean_array[n]:
                        y_mean_array[n].append(metric_value)
                        break
                    n += 1
            
            for m in range(num_bins):
                
                if len(y_mean_array[m]) < 30:
                    y_mean_array[m] = 0
                    count_array[m] = 0
                    continue
                
                mean, lower_bound, upper_bound = mean_confidence_interval(y_mean_array[m], 0.95)
                
                sum = 0
                count = 0
                for n in range(len(y_mean_array[m])):
                    if y_mean_array[m][n] > lower_bound and y_mean_array[m][n] < upper_bound:
                        sum += y_mean_array[m][n]
                        count += 1
                
                if count > 0:
                    y_mean_array[m] = sum / count
                else:
                    y_mean_array[m] = 0
                count_array[m] = count
            
            update_x_mean_array = []
            update_y_mean_array = []
            
            for m in range(num_bins):
                if count_array[m] > 0:
                    update_x_mean_array.append(x_mean_array[m])
                    update_y_mean_array.append(y_mean_array[m])
                    
            x_sm = np.array(update_x_mean_array)
            y_sm = np.array(update_y_mean_array)

            x_smooth = np.linspace(x_sm.min(), x_sm.max(), 200)
            print count_array
            print update_y_mean_array
            y_smooth = spline(update_x_mean_array, update_y_mean_array, x_smooth)
          
            plt.plot(x_smooth, y_smooth)
        
        plt.legend(['Extroversion', 'Agreeableness', 'Conscientiousness', 'Neuroticism', 'Openness'], loc='best')
        
        plt.show()      
            
            
            






path = "/Volumes/NETAC/EdX/Clear-out/EX101x-3T2015/personality_analysis/"
#DrawClusterScatterPlot(path)
DrawClusterScatterPlotEqualInterval(path)
print "Finished."