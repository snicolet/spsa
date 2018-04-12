# -*- coding: utf-8 -*-
"""
Optimizer fot game coeeficients using the SPSA algorithm.
Author: Stéphane Nicolet
"""

import random
import math
import array
from subprocess import Popen, PIPE
import sys
import spsa

def engine_score(theta):
    
    minibatch = 6                             # size of the mini-matches used to get an evaluation
    seed      = random.randint(1, 100000000)  # a random seed
    
    print(seed)

    command = "python chess-match.py "
    args = " " + str(minibatch) + " " + str(seed) + " "
    for (name, value) in theta.items():
        args +=  " " + name + " " + str(value) + " "
    
    process = Popen(command + args, shell = True, stdout = PIPE)
    output = process.communicate()[0]
    
    if process.returncode != 0:
        print('Could not execute command: %s' % (command + args))
        return -10000
    
    return float(output)





       
theta0 = {}

def read_parameters(s):
   global theta0
   
   s = ' '.join(s.split())
   
   print("s = " + s)
   list = s.split(' ')
   n = len(list)
   
   theta0 = {}
   
   for k in range(0 , n // 2):
      name  = list[ 2*k ]
      value = float(list[ 2*k + 1])
      theta0[name] = value
      
   print("read_parameters :  theta0 = " + str(theta0))
   
   return theta0
   


def goal_function(**args):

    global theta0
    
    theta = {}
    for (name, value) in theta0.items():
       ## print(name)
       ## print(value)
       v = args[name]
       theta[name] = v
       
    regularization = spsa.regulizer(spsa.difference(theta, theta0), 0.0001, 0.5)
    score = engine_score(theta)
    
    result = -score + regularization
    
    print("**args = " + str(args))
    print("goal   = " + str(result))
    
    return result



###### Examples

if __name__ == "__main__":


    theta0 = read_parameters("singular_A   20   singular_B  0 ")
    
    optimizer = spsa.SPSA_minimization(goal_function, theta0, 10000)
    
    minimum = optimizer.run()
    print("minimum = ", minimum)
    


