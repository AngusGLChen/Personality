'''
Created on May 10, 2016

@author: Angus
'''


import numpy as np

def Function():
    #a = np.array([1,2,3,4,5,6,7,8])
    
    x = np.linspace(-10, 10, 5)
    y = np.linspace(15, -15, 6)
    
    print "----------x and y"
    print x
    print y
    print
    
    iy, ix = np.indices([6,5])
    
    print "-------------ix and iy"
    print ix
    print iy
    print
    
    print "test"
    
    print x[ix]
    print
    print y[iy]
    
    #cor = np.column_stack([x[ix].flat, y[iy].flat, ix.flat, iy.flat])
    
    
    
    
    

Function()
print "Finished."

    
    
    
