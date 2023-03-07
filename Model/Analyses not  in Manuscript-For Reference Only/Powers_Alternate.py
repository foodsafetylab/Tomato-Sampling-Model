# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 15:43:30 2022

@author: gareyes3
"""
import sys
sys.path
sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\\reyes\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\Model')


import numpy as np
import pandas as pd
import random 
import math
from numpy.random import Generator, PCG64
rng = Generator(PCG64())
import matplotlib.pyplot as plt
import seaborn as sns
from importlib import reload 

import time
#Own Libraries
import Funz_T
import Inputz_T
import Scen_T
import MainModel
#import DepInputz

import T_Inputz
import Dictionariez_T

from multiprocessing import Process
from multiprocessing import Pool


np.random.seed(100+1)
random.seed(100+1)
Random_Haz = int(np.random.normal(132_000,0))
Scen_T.Iteration_Number = 20
Scen_T.Total_Hazard= Random_Haz
Scen_T.Tomatoes_per_sample = 60
Scen_T.Samp_Plan = 3
Scen_T.Cont_Scenario = 4
Scen_T.Samp_Method = 1
Scen_T.N_Replicates = 60
#reload(DepInputz)
Outs = MainModel.Main_Loop(random_seed=1*105)


def Get_Power_Bins(df, Weight_After, Weight_Before, CFU_avail, Tot_Iter): 
    Total_Rej = sum((df[Weight_After]-df[Weight_Before])>0 )
    Total_Avail = (sum(df[ CFU_avail]>0))
    Power =  Total_Rej/Total_Avail
    return [Total_Rej,Total_Avail,Power]

Get_Power_Bins(df = Outs[0], 
          Weight_After = "PHS 1 Weight Rejected Aft", 
          Weight_Before = "PHS 1 Weight Rejected Bef", 
          CFU_avail = "CFU_Avail Pick 1",
          Tot_Iter = 10
          )

Get_Power_Bins(df = Outs[0], 
          Weight_After = "PHS 2 Weight Rejected Aft", 
          Weight_Before = "PHS 2 Weight Rejected Bef", 
          CFU_avail = "CFU_Avail Pick 2",
          Tot_Iter = 10
          )

Get_Power_Bins(df = Outs[0], 
          Weight_After = "PHS 3 Weight Rejected Aft", 
          Weight_Before = "PHS 3 Weight Rejected Bef", 
          CFU_avail = "CFU_Avail Pick 3",
          Tot_Iter = 10
          )

