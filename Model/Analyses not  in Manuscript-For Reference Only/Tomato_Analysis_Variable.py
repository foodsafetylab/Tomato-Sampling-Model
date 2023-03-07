# -*- coding: utf-8 -*-
"""
Created on Mon Sep 19 08:50:33 2022

@author: Gustavo Reyes
"""

#Second Tomato Analysis

#%%
import sys
sys.path
sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility_L_T\Model')
#%%
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
import DepInputz

import T_Inputz
import Dictionariez_T

from multiprocessing import Process
from multiprocessing import Pool
#%%
def Get_Power(df, Weight_After, Weight_Before, CFU_avail, Tot_Iter): 
    Total_Rej = sum((df[Weight_After]-df[Weight_Before])>0 )
    Total_Avail = (sum(df[ CFU_avail]>0))
    Power =  sum((df[Weight_After]-df[Weight_Before])>0 )/ Tot_Iter
    return [Total_Rej,Total_Avail,Power]


def get_powers_scenarios (df, Tot_Iter):
    A=Get_Power(df = df, 
              Weight_After = "PHS 1 Weight Rejected Aft", 
              Weight_Before = "PHS 1 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 1",
              Tot_Iter = Tot_Iter
              )

    B=Get_Power(df = df, 
              Weight_After = "PHS 2 Weight Rejected Aft", 
              Weight_Before = "PHS 2 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 2",
              Tot_Iter = Tot_Iter
              )

    C= Get_Power(df = df, 
              Weight_After = "PHS 3 Weight Rejected Aft", 
              Weight_Before = "PHS 3 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 3",
              Tot_Iter = Tot_Iter
              )
    return [A,B,C]

def Power_DF_Creation(Column_Names, Niterations):
    Outputs_Df =pd.DataFrame(np.NaN, index= range(Niterations), columns =Column_Names)
    return Outputs_Df

def Get_Contam_Sampling(df, Type, Mass, Spread):
    A=pd.DataFrame({"Cont":df["CFU_Avail Pick 1"],
                  "Pick": 1,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    B=pd.DataFrame({"Cont":df["CFU_Avail Pick 2"],
                  "Pick": 2,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    C=pd.DataFrame({"Cont":df["CFU_Avail Pick 3"],
                  "Pick": 3,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    Dfout = pd.concat([A,B,C])
    return (Dfout)

def Get_Prev_Sampling(df, Type, Mass, Spread):
    A=pd.DataFrame({"Cont":df["Prev_Avail Pick 1"],
                  "Pick": 1,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    B=pd.DataFrame({"Cont":df["Prev_Avail Pick 2"],
                  "Pick": 2,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    C=pd.DataFrame({"Cont":df["Prev_Avail Pick 3"],
                  "Pick": 3,
                  "Type" : Type,
                  "Mass": Mass,
                  "Cont Type": Spread
                  })
    Dfout = pd.concat([A,B,C])
    return (Dfout)


#%% Contamination progression thruhgout system No Sampling
 
def Analysis_Loop(HA_Iterations,Loop_Iterations,Hazard_Mean, Hazard_SD, Samp_Plan, Tom_Per_Sample, Cont_Scen, Type, Mass, Spread , Samp_Method, N_Replicates ):
    Hazard_Iterations = HA_Iterations


    Powers_df = Power_DF_Creation(Column_Names = ["Power_Pick_1", "Power_Pick_2", "Power_Pick_3"],
                                  Niterations = Hazard_Iterations )
    Progression_df = Dictionariez_T.Output_DF_Creation(Column_Names =Dictionariez_T.Col_Days, 
                                                       Niterations = 0)
    Progression_df["HI"] = np.nan

    Samp_Point_df = Power_DF_Creation(Column_Names = ["Cont", "Pick", "Type", "Mass", "Cont Type", "HI"],
                                  Niterations = 0)
    
    #Progression Days
    Progression_df_Prev = Dictionariez_T.Output_DF_Creation(Column_Names =Dictionariez_T.Col_Days, 
                                                       Niterations = 0)
    Progression_df_Prev["HI"] = np.nan
    
    Progression_df_Prev_Proc = Dictionariez_T.Output_DF_Creation(Column_Names =Dictionariez_T.Proc_Steps, 
                                                                                Niterations = 0)
    Progression_df_Prev_Proc["HI"] = np.nan
    
    Prev_Point_df = Power_DF_Creation(Column_Names = ["Cont", "Pick", "Type", "Mass", "Cont Type", "HI"],
                                  Niterations = 0)
    
    Exposure_df = Power_DF_Creation(Column_Names = ["Total CFU"],Niterations = 0 )
    Exposure_df["HI"] = np.nan
    
    for i in range(Hazard_Iterations):
        np.random.seed(100+i)
        random.seed(100+i)
        Random_Haz = int(np.random.normal(Hazard_Mean,Hazard_SD))
        print(Random_Haz)
        Inputz_T.Iteration_Number = Loop_Iterations
        Inputz_T.Total_Hazard= Random_Haz
        Scen_T.Tomatoes_per_sample = Tom_Per_Sample
        Scen_T.Samp_Plan = Samp_Plan
        Scen_T.Cont_Scenario = Cont_Scen
        Scen_T.Samp_Method = Samp_Method
        Scen_T.N_Replicates = N_Replicates
        reload(DepInputz)
        Outs = MainModel.Main_Loop(random_seed=i*20)
        #powers
        Powers_df.at[i,"Power_Pick_1"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[0][2]
        Powers_df.at[i,"Power_Pick_2"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[1][2]
        Powers_df.at[i,"Power_Pick_3"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[2][2]
        
        #progression
        Progression_Temp = Outs[1]
        Progression_Temp["HI"] =i
        Progression_df=pd.concat([Progression_df,Progression_Temp]) 
        
        #
        Samp_Point = Get_Contam_Sampling(df = Outs[0], Type = Type,Mass = Mass, Spread= Spread)
        Samp_Point["HI"] = i
        Samp_Point_df = pd.concat([Samp_Point_df,Samp_Point])
        
        #Prevprog
        Progression_Prev = Outs[4]
        Progression_Prev["HI"] = i
        Progression_df_Prev=pd.concat([Progression_df_Prev,Progression_Prev]) 
        
        #Prevprog
        Progression_Prev_Prog = Outs[3]
        Progression_Prev_Prog["HI"] = i 
        Progression_df_Prev_Proc=pd.concat([Progression_df_Prev_Proc,Progression_Prev_Prog]) 

        #PrevSampling
        Prev_Point = Get_Prev_Sampling(df = Outs[0], Type = Type,Mass = Mass, Spread= Spread)
        Prev_Point["HI"] = i
        Prev_Point_df = pd.concat([Prev_Point_df,Prev_Point])
        
        Expa =pd.DataFrame({
            "Total CFU": Outs[0]["Total CFU"],
            "HI": i})

        
        Exposure_df=pd.concat([Exposure_df,Expa])
        
        
    return [Powers_df,Progression_df,Samp_Point_df,Progression_df_Prev,Progression_df_Prev_Proc,Prev_Point_df,Exposure_df]

#%%
Outs_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)


Outs_1A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_1B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_1C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 100, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_1D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 2,
              N_Replicates = 20
              )

Outs_1E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_2A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_2B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 ,
              N_Replicates = 0)

Outs_2C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 100, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_2D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 2,
              N_Replicates = 20
              )

Outs_2E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_3A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_3B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_3C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 100, 
              Cont_Scen =1, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_3D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 2,
              N_Replicates = 20
              )

Outs_3E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_4A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_4B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 ,
              N_Replicates = 0)

Outs_4C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 100, 
              Cont_Scen =1, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_4D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 2,
              N_Replicates = 20
              )

Outs_4E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


###
#Single Cont
Outs_0_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 ,
              N_Replicates = 0)


Outs_1A_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 ,
              N_Replicates = 0)


Outs_1B_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 ,
              N_Replicates = 0)

Outs_1C_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 100, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_1D_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 2,
              N_Replicates = 20)

Outs_1E_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )


Outs_2A_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)


Outs_2B_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_2C_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 100, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 1,
              N_Replicates = 0)

Outs_2D_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 2,
              N_Replicates = 20)

Outs_2E_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_3A_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1, 
              N_Replicates = 0 )


Outs_3B_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 , 
              N_Replicates = 0)

Outs_3C_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 100, 
              Cont_Scen =2, 
              Type ="RS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1, 
              N_Replicates = 0 )

Outs_3D_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 2, 
              N_Replicates = 20)

Outs_3E_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

Outs_4A_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 , 
              N_Replicates = 0)


Outs_4B_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 , 
              N_Replicates = 0)

Outs_4C_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 100, 
              Cont_Scen =2, 
              Type ="PPS", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1 , 
              N_Replicates = 0)

Outs_4D_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform" ,
              Samp_Method  = 2, 
              N_Replicates = 20)

Outs_4E_01= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "1 Tomato", 
              Spread  = "Uniform",
              Samp_Method  = 1,
              N_Replicates = 0 )

#%% Sampling Plan Power Analysis
def get_Powers(df,Mass,Type):
    a=df.melt()
    a["Type"] = Type
    a["Mass"] = Mass
    return a 

Power_1A =get_Powers(df = Outs_1A[0], Mass = "2 tomatoes",Type =  "Preharvest")
Power_1B =get_Powers(df = Outs_1B[0], Mass = "6 tomatoes",Type =   "Preharvest")
Power_1C =get_Powers(df = Outs_1C[0], Mass = "20 x 5 tomatoes",Type =   "Preharvest")
Power_1D =get_Powers(df = Outs_1D[0], Mass = "20 Tomato Mash",Type =   "Preharvest")
Power_1E =get_Powers(df = Outs_1E[0], Mass = "20 Tomatoes",Type =   "Preharvest")

Power_2A =get_Powers(df = Outs_2A[0], Mass = "2 tomatoes",Type =  "Harvest")
Power_2B =get_Powers(df = Outs_2B[0], Mass = "6 tomatoes",Type =  "Harvest")
Power_2C =get_Powers(df = Outs_2C[0], Mass = "20 x 5 tomatoes",Type =  "Harvest")
Power_2D =get_Powers(df = Outs_2D[0], Mass = "20 Tomato Mash",Type =   "Harvest")
Power_2E =get_Powers(df = Outs_2E[0], Mass = "20 Tomatoes",Type =   "Harvest")

Power_3A =get_Powers(df = Outs_3A[0], Mass = "2 tomatoes",Type =  "Receiving")
Power_3B =get_Powers(df = Outs_3B[0], Mass = "6 tomatoes",Type =  "Receiving")
Power_3C =get_Powers(df = Outs_3C[0], Mass = "20 x 5 tomatoes",Type =  "Receiving")
Power_3D =get_Powers(df = Outs_3D[0], Mass = "20 Tomato Mash",Type =   "Receiving")
Power_3E =get_Powers(df = Outs_3E[0], Mass = "20 Tomatoes",Type =   "Receiving")


Power_4A =get_Powers(df = Outs_4A[0], Mass = "2 tomatoes",Type =  "Packed Product")
Power_4B =get_Powers(df = Outs_4B[0], Mass = "6 tomatoes",Type =   "Packed Product")
Power_4C =get_Powers(df = Outs_4C[0], Mass = "20 x 5 tomatoes",Type =   "Packed Product")
Power_4D =get_Powers(df = Outs_4D[0], Mass = "20 Tomato Mash",Type =   "Packed Product")
Power_4E =get_Powers(df = Outs_4E[0], Mass = "20 Tomatoes",Type =   "Packed Product")




Powers_Out = pd.concat([Power_1A, Power_1B, Power_1C,Power_1D,Power_1E,
                        Power_2A, Power_2B, Power_2C,Power_2D,Power_2E,
                        Power_3A, Power_3B, Power_3C,Power_3D,Power_3E,
                        Power_4A, Power_4B, Power_4C,Power_4D,Power_4E])

Powers_Out.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out2.csv")
###########################################################################

Power_1A_01 =get_Powers(df = Outs_1A_01[0], Mass = "2 tomatoes",Type =   "Preharvest")
Power_1B_01 =get_Powers(df = Outs_1B_01[0], Mass = "6 tomatoes",Type =   "Preharvest")
Power_1C_01 =get_Powers(df = Outs_1C_01[0], Mass = "20 x 5 tomatoes",Type =   "Preharvest")
Power_1D_01 =get_Powers(df = Outs_1D_01[0], Mass = "20 Tomato Mash",Type =   "Preharvest")
Power_1E_01 =get_Powers(df = Outs_1E_01[0], Mass = "20 Tomatoes",Type =   "Preharvest")

Power_2A_01 =get_Powers(df = Outs_2A_01[0], Mass = "2 tomatoes",Type =  "Harvest")
Power_2B_01 =get_Powers(df = Outs_2B_01[0], Mass = "6 tomatoes",Type =  "Harvest")
Power_2C_01 =get_Powers(df = Outs_2C_01[0], Mass = "20 x 5 tomatoes",Type =  "Harvest")
Power_2D_01 =get_Powers(df = Outs_2D_01[0], Mass = "20 Tomato Mash",Type =   "Harvest")
Power_2E_01 =get_Powers(df = Outs_2E_01[0], Mass = "20 Tomatoes",Type =   "Harvest")

Power_3A_01 =get_Powers(df = Outs_3A_01[0], Mass = "2 tomatoes",Type =  "Receiving")
Power_3B_01 =get_Powers(df = Outs_3B_01[0], Mass = "6 tomatoes",Type =  "Receiving")
Power_3C_01 =get_Powers(df = Outs_3C_01[0], Mass = "20 x 5 tomatoes",Type =  "Receiving")
Power_3D_01 =get_Powers(df = Outs_3D_01[0], Mass = "20 Tomato Mash",Type =   "Receiving")
Power_3E_01 =get_Powers(df = Outs_3E_01[0], Mass = "20 Tomatoes",Type =   "Receiving")

Power_4A_01 =get_Powers(df = Outs_4A_01[0], Mass = "2 tomatoes",Type =   "Packed Product")
Power_4B_01 =get_Powers(df = Outs_4B_01[0], Mass = "6 tomatoes",Type =   "Packed Product")
Power_4C_01 =get_Powers(df = Outs_4C_01[0], Mass = "20 x 5 tomatoes",Type =   "Packed Product")
Power_4D_01 =get_Powers(df = Outs_4D_01[0], Mass = "20 Tomato Mash",Type =   "Packed Product")
Power_4E_01 =get_Powers(df = Outs_4E_01[0], Mass = "20 Tomatoes",Type =   "Packed Product")

Powers_Out = pd.concat([Power_1A_01, Power_1B_01, Power_1C_01,Power_1D_01,Power_1E_01,
                        Power_2A_01, Power_2B_01, Power_2C_01,Power_2D_01,Power_2E_01,
                        Power_3A_01, Power_3B_01, Power_3C_01,Power_3D_01,Power_3E_01,
                        Power_4A_01, Power_4B_01, Power_4C_01,Power_4D_01,Power_4E_01])

Powers_Out.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out_PS2.csv")




#%%
#Get Contmaination at sampling points
Contam_Samp_Out = pd.concat([Outs_1A[2], Outs_1B[2], Outs_1C[2],Outs_1D[2],Outs_1E[2],
                        Outs_2A[2], Outs_2B[2], Outs_2C[2],Outs_2D[2],Outs_2E[2],
                        Outs_3A[2], Outs_3B[2], Outs_3C[2],Outs_3D[2],Outs_3E[2],
                        Outs_4A[2], Outs_4B[2], Outs_4C[2],Outs_4D[2],Outs_4E[2]])



Contam_Samp_Out.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Contam_Samp_Out2.csv")

Contam_Samp_OutPS = pd.concat([Outs_1A_01[2], Outs_1B_01[2], Outs_1C_01[2],Outs_1D_01[2],Outs_1E_01[2],
                        Outs_2A_01[2], Outs_2B_01[2], Outs_2C_01[2],Outs_2D_01[2],Outs_2E_01[2],
                        Outs_3A_01[2], Outs_3B_01[2], Outs_3C_01[2],Outs_3D_01[2],Outs_3E_01[2],
                        Outs_4A_01[2], Outs_4B_01[2], Outs_4C_01[2],Outs_4D_01[2],Outs_4E_01[2]])

Contam_Samp_Out.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Contam_Samp_Out_PS2.csv")

#%% Prevalence Progression: 
Prev_Samp_Out = pd.concat([Outs_1A[5], Outs_1B[5], Outs_1C[5],Outs_1D[5],Outs_1E[5],
                        Outs_2A[5], Outs_2B[5], Outs_2C[5],Outs_2D[5],Outs_2E[5],
                        Outs_3A[5], Outs_3B[5], Outs_3C[5],Outs_3D[5],Outs_3E[5],
                        Outs_4A[5], Outs_4B[5], Outs_4C[5],Outs_4D[5],Outs_4E[5]])



Prev_Samp_Out.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Prev_Samp_Out1.csv")

Prev_Samp_OutPS = pd.concat([Outs_1A_01[5], Outs_1B_01[5], Outs_1C_01[5],Outs_1D_01[5],Outs_1E_01[5],
                        Outs_2A_01[5], Outs_2B_01[5], Outs_2C_01[5],Outs_2D_01[5],Outs_2E_01[5],
                        Outs_3A_01[5], Outs_3B_01[5], Outs_3C_01[5],Outs_3D_01[5],Outs_3E_01[5],
                        Outs_4A_01[5], Outs_4B_01[5], Outs_4C_01[5],Outs_4D_01[5],Outs_4E_01[5],])
Prev_Samp_OutPS.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Prev_Samp_Out_PS1.csv")


#%% Consumer Exposure
def get_exps(df,Type,ContType, Mass):
    AU= df[6].copy()
    AU["Type"] = Type
    AU["ContType"] = ContType
    AU["Mass"] = Mass
    return AU



Exp_0 = get_exps(Outs_0, "Baseline", "Uniform", "Baseline")
Exp_1A = get_exps(Outs_1A, "Preharvest", "Uniform", "2 Tomatoes")
Exp_1B = get_exps(Outs_1B, "Preharvest", "Uniform", "6 Tomatoes")
Exp_1C = get_exps(Outs_1C, "Preharvest", "Uniform","5 X 20 tomatoes")
Exp_1D = get_exps(Outs_1D, "Preharvest", "Uniform","20 Tomato Mash 20R")
Exp_1E = get_exps(Outs_1E, "Preharvest", "Uniform","20 Tomatoes")

Exp_2A = get_exps(Outs_2A, "Harvest", "Uniform","2 Tomatoes")
Exp_2B = get_exps(Outs_2B, "Harvest", "Uniform","6 Tomatoes")
Exp_2C = get_exps(Outs_2C, "Harvest", "Uniform","5 X 20 tomatoes")
Exp_2D = get_exps(Outs_2D, "Harvest", "Uniform","20 Tomato Mash 20R")
Exp_2E = get_exps(Outs_2E, "Harvest", "Uniform","20 Tomatoes")

Exp_3A = get_exps(Outs_3A, "Receiving", "Uniform","2 Tomatoes")
Exp_3B = get_exps(Outs_3B, "Receiving", "Uniform","6 Tomatoes")
Exp_3C = get_exps(Outs_3C, "Receiving", "Uniform","5 X 20 tomatoes")
Exp_3D = get_exps(Outs_3D, "Receiving", "Uniform","20 Tomato Mash 20R")
Exp_3E = get_exps(Outs_3E, "Receiving", "Uniform","20 Tomatoes")

Exp_4A = get_exps(Outs_4A, "Packed Product", "Uniform","2 Tomatoes")
Exp_4B = get_exps(Outs_4B, "Packed Product", "Uniform","6 Tomatoes")
Exp_4C = get_exps(Outs_4C, "Packed Product", "Uniform","5 X 20 tomatoes")
Exp_4D = get_exps(Outs_4D, "Packed Product", "Uniform","20 Tomato Mash 20R")
Exp_4E = get_exps(Outs_4E, "Packed Product", "Uniform","20 Tomatoes")


Exp_0_01 = get_exps(Outs_0_01, "Baseline", "Point Source", "Baseline")
Exp_1A_01 = get_exps(Outs_1A_01, "Preharvest", "Point Source", "2 Tomatoes")
Exp_1B_01 = get_exps(Outs_1B_01, "Preharvest", "Point Source", "6 Tomatoes")
Exp_1C_01 = get_exps(Outs_1C_01, "Preharvest", "Point Source","5 X 20 tomatoes")
Exp_1D_01 = get_exps(Outs_1D_01, "Preharvest", "Point Source","20 Tomato Mash 20R")
Exp_1E_01 = get_exps(Outs_1E_01, "Preharvest", "Point Source","20 Tomatoes")

Exp_2A_01 = get_exps(Outs_2A_01, "Harvest", "Point Source","2 Tomatoes")
Exp_2B_01 = get_exps(Outs_2B_01, "Harvest", "Point Source","6 Tomatoes")
Exp_2C_01 = get_exps(Outs_2C_01, "Harvest", "Point Source","5 X 20 tomatoes")
Exp_2D_01 = get_exps(Outs_2D_01, "Harvest", "Point Source","20 Tomato Mash 20R")
Exp_2E_01 = get_exps(Outs_2E_01, "Harvest", "Point Source","20 Tomatoes")

Exp_3A_01 = get_exps(Outs_3A_01, "Receiving", "Point Source","2 Tomatoes")
Exp_3B_01 = get_exps(Outs_3B_01, "Receiving", "Point Source","6 Tomatoes")
Exp_3C_01 = get_exps(Outs_3C_01, "Receiving", "Point Source","5 X 20 tomatoes")
Exp_3D_01 = get_exps(Outs_3D_01, "Receiving", "Point Source","20 Tomato Mash 20R")
Exp_3E_01 = get_exps(Outs_3E_01, "Receiving", "Point Source","20 Tomatoes")

Exp_4A_01 = get_exps(Outs_4A_01, "Packed Product", "Point Source","2 Tomatoes")
Exp_4B_01 = get_exps(Outs_4B_01, "Packed Product", "Point Source","6 Tomatoes")
Exp_4C_01 = get_exps(Outs_4C_01, "Packed Product", "Point Source","5 X 20 tomatoes")
Exp_4D_01 = get_exps(Outs_4D_01, "Packed Product", "Point Source","20 Tomato Mash 20R")
Exp_4E_01 = get_exps(Outs_4E_01,  "Packed Product", "Point Source","20 Tomatoes")

Exps = pd.concat([Exp_0,
                  Exp_1A,Exp_1B,Exp_1C,Exp_1D,Exp_1E,
                  Exp_2A,Exp_2B,Exp_2C,Exp_2D,Exp_2E,
                  Exp_3A,Exp_3B,Exp_3C,Exp_3D,Exp_3E,
                  Exp_4A,Exp_4B,Exp_4C,Exp_4D,Exp_4E])



Exps.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Exps.csv")

ExpsPS = pd.concat([Exp_0_01,
                  Exp_1A_01,Exp_1B_01,Exp_1C_01,Exp_1D_01,Exp_1E_01,
                  Exp_2A_01,Exp_2B_01,Exp_2C_01,Exp_2D_01,Exp_2E_01,
                  Exp_3A_01,Exp_3B_01,Exp_3C_01,Exp_3D_01,Exp_3E_01,
                  Exp_4A_01,Exp_4B_01,Exp_4C_01,Exp_4D_01,Exp_4E_01])

ExpsPS.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\ExpsPS.csv")












#%%



#%%
Hazard_Iterations = 10

Powers_df = Power_DF_Creation(Column_Names = ["Power_Pick_1", "Power_Pick_2", "Power_Pick_3"],
                              Niterations = Hazard_Iterations )
Progression_df = Dictionariez_T.Output_DF_Creation(Column_Names =Dictionariez_T.Col_Days, 
                                                   Niterations = 0)
Progression_df["HI"] = np.nan

Samp_Point_df = Power_DF_Creation(Column_Names = ["Cont", "Pick", "Type", "Mass", "Cont Type", "HI"],
                              Niterations = 0)
for i in range(Hazard_Iterations):
    Random_Haz = int(rng.normal(132_000,20_000))
    Inputz_T.Iteration_Number = 10
    Inputz_T.Total_Hazard= Random_Haz
    Scen_T.Tomatoes_per_sample = 1
    Scen_T.Samp_Plan = 1
    Scen_T.Cont_Scenario = 1
    reload(DepInputz)
    Outs = MainModel.Main_Loop()
    #powers
    Powers_df.at[i,"Power_Pick_1"]=get_powers_scenarios(Outs[0],Tot_Iter = Inputz_T.Iteration_Number)[0][2]
    Powers_df.at[i,"Power_Pick_2"]=get_powers_scenarios(Outs[0],Tot_Iter = Inputz_T.Iteration_Number)[1][2]
    Powers_df.at[i,"Power_Pick_3"]=get_powers_scenarios(Outs[0],Tot_Iter = Inputz_T.Iteration_Number)[2][2]
    
    #progression
    Progression_Temp = Outs[1]
    Progression_Temp["HI"] = Random_Haz 
    Progression_df=pd.concat([Progression_df,Progression_Temp]) 
    
    #
    Samp_Point = Get_Contam_Sampling(df = Outs[0], Type = "PH",Mass = "1 Tomato", Spread= "Uniform")
    Samp_Point["HI"] = Random_Haz
    Samp_Point_df = pd.concat([Samp_Point_df,Samp_Point])


def print_range(lrange):
    print('First is {} and last is {}'.format(lrange[0], lrange[1]))


def run_in_parallel():
    ranges = [[0, 10], [10, 20], [20, 30]]
    pool = Pool(processes=len(ranges))
    pool.map(print_range, ranges)


if __name__ == '__main__':
    run_in_parallel()


Hazard_lvl = [32000, 15000]

outs = map(MainModel.Main_Loop,Hazard_lvl)

from multiprocessing.pool import ThreadPool




start_surv_eod = time.time()
pool = ThreadPool()
Scen_T.Tomatoes_per_sample = 8
images = [32_000,2_000, 132_000]
results = pool.map(MainModel.Main_Loop, images)
print(time.time() - start_surv_eod, "Survival eod")

