# -*- coding: utf-8 -*-
"""
Created on Wed Oct  5 10:31:26 2022

@author: gareyes3
"""

#Tomato Analysis to Evaluate sampling plans and contamination scenarios. 

#%%
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

#%% Functions needed to run the nested analyses

#This function extracts power from the outs dataframe located in MainModel
def Get_Power(df, Weight_After, Weight_Before, CFU_avail, Tot_Iter): 
    Total_Rej = sum((df[Weight_After]-df[Weight_Before])>0 )
    Total_Avail = (sum(df[ CFU_avail]>0))
    Power =  sum((df[Weight_After]-df[Weight_Before])>0 )/ Tot_Iter
    return [Total_Rej,Total_Avail,Power]

def Get_Power_Bins(df, Weight_After, Weight_Before, CFU_avail, Tot_Iter): 
    Total_Rej = sum((df[Weight_After]-df[Weight_Before])>0 )
    Total_Avail = (sum(df[ CFU_avail]>0))
    if Total_Avail>0:
        Power =  Total_Rej/Total_Avail
    else: 
        Power = np.nan
    return [Total_Rej,Total_Avail,Power]

#This is another function that extract the powers observed every pick
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

def get_powers_scenarios_Bins (df, Tot_Iter):
    A=Get_Power_Bins(df = df, 
              Weight_After = "PHS 1 Weight Rejected Aft", 
              Weight_Before = "PHS 1 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 1",
              Tot_Iter = Tot_Iter
              )

    B=Get_Power_Bins(df = df, 
              Weight_After = "PHS 2 Weight Rejected Aft", 
              Weight_Before = "PHS 2 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 2",
              Tot_Iter = Tot_Iter
              )

    C= Get_Power_Bins(df = df, 
              Weight_After = "PHS 3 Weight Rejected Aft", 
              Weight_Before = "PHS 3 Weight Rejected Bef", 
              CFU_avail = "CFU_Avail Pick 3",
              Tot_Iter = Tot_Iter
              )
    return [A,B,C]

#Created the power dataframe for the analysis
def Power_DF_Creation(Column_Names, Niterations):
    Outputs_Df =pd.DataFrame(np.NaN, index= range(Niterations), columns =Column_Names)
    return Outputs_Df

#Gets the contamination at each sampling point
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

#Gets the prevalence at each sampling point
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

 
#Puts everything together in a function to run the desired scearios
def Analysis_Loop(HA_Iterations,Loop_Iterations,Hazard_Mean, Hazard_SD, Samp_Plan, Tom_Per_Sample, Cont_Scen, Type, Mass, Spread , Samp_Method, N_Replicates ):
    Hazard_Iterations = HA_Iterations


    Powers_df = Power_DF_Creation(Column_Names = ["Power_Pick_1", "Power_Pick_2", "Power_Pick_3"],
                                  Niterations = Hazard_Iterations )
    
    Powers_df_alt = Power_DF_Creation(Column_Names = ["Power_Pick_1", "Power_Pick_2", "Power_Pick_3"],
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
        print(i, "Hazard Iteration")
        np.random.seed(100+i)
        random.seed(100+i)
        Random_Haz = int(np.random.normal(Hazard_Mean,Hazard_SD))
        Scen_T.Iteration_Number = Loop_Iterations
        Scen_T.Total_Hazard= Random_Haz
        Scen_T.Tomatoes_per_sample = Tom_Per_Sample
        Scen_T.Samp_Plan = Samp_Plan
        Scen_T.Cont_Scenario = Cont_Scen
        Scen_T.Samp_Method = Samp_Method
        Scen_T.N_Replicates = N_Replicates
        #reload(DepInputz)
        Outs = MainModel.Main_Loop(random_seed=i*105)
        #powers
        Powers_df.at[i,"Power_Pick_1"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[0][2]
        Powers_df.at[i,"Power_Pick_2"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[1][2]
        Powers_df.at[i,"Power_Pick_3"]=get_powers_scenarios(Outs[0],Tot_Iter = Loop_Iterations)[2][2]
        
        Powers_df_alt.at[i,"Power_Pick_1"]=get_powers_scenarios_Bins(Outs[0],Tot_Iter = Loop_Iterations)[0][2]
        Powers_df_alt.at[i,"Power_Pick_2"]=get_powers_scenarios_Bins(Outs[0],Tot_Iter = Loop_Iterations)[1][2]
        Powers_df_alt.at[i,"Power_Pick_3"]=get_powers_scenarios_Bins(Outs[0],Tot_Iter = Loop_Iterations)[2][2]
        
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
        
        
    return [Powers_df,Progression_df,Samp_Point_df,Progression_df_Prev,Progression_df_Prev_Proc,Prev_Point_df,Exposure_df,Powers_df_alt]

#%% Uniform Contamination Scenarios: 
#Baseline, Uniform Contamination with no sampling
Outs_100_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "Baseline", 
              Spread  = "100%" ,
              Samp_Method  = 1,
              N_Replicates = 0)

####Preharvest_Sampling
# A 2 tomatoes
start = time.time()
Outs_100_1_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "2 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
print(time.time() - start, "100 Iteration Run Time")

# B 6 tomatoes
Outs_100_1_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "6 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_100_1_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "20 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_100_1_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "60 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_100_1_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "20 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_100_1_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="PH", 
              Mass = "60 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Harvest Sampling
# A 2 tomatoes
Outs_100_2_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "2 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_100_2_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "6 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_100_2_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "20 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_100_2_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "60 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_100_2_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "20 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_100_2_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="H", 
              Mass = "60 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Receiving Sampling
# A 2 tomatoes
Outs_100_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_100_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_100_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_100_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_100_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_100_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_100_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_100_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_100_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_100_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "100%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_100_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_100_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =1, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "100%",
              Samp_Method  = 2,
              N_Replicates = 60 )

#%% 10% Cluster. 
#Baseline, Uniform Contamination with no sampling
Outs_010_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "Baseline", 
              Spread  = "10%" ,
              Samp_Method  = 1,
              N_Replicates = 0)

####Preharvest_Sampling
# A 2 tomatoes
Outs_010_1_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "2 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_010_1_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "6 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_010_1_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "20 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_010_1_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "60 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_010_1_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "20 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_010_1_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="PH", 
              Mass = "60 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Harvest Sampling
# A 2 tomatoes
Outs_010_2_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "2 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_010_2_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "6 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_010_2_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "20 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_010_2_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "60 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_010_2_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "20 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_010_2_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="H", 
              Mass = "60 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Receiving Sampling
# A 2 tomatoes
Outs_010_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_010_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_010_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_010_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_010_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_010_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_010_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_010_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_010_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_010_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "10%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_010_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_010_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =2, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "10%",
              Samp_Method  = 2,
              N_Replicates = 60 )

#%% 1% Cluster. 
#Baseline, Uniform Contamination with no sampling
Outs_001_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "Baseline", 
              Spread  = "1%" ,
              Samp_Method  = 1,
              N_Replicates = 0)

####Preharvest_Sampling
# A 2 tomatoes
Outs_001_1_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "2 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_001_1_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "6 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_001_1_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "20 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_001_1_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "60 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_001_1_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "20 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_001_1_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="PH", 
              Mass = "60 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Harvest Sampling
# A 2 tomatoes
Outs_001_2_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "2 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_001_2_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "6 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_001_2_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "20 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_001_2_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "60 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_001_2_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "20 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_001_2_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="H", 
              Mass = "60 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Receiving Sampling
# A 2 tomatoes
Outs_001_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_001_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_001_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_001_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_001_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_001_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_001_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_001_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_001_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_001_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_001_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_001_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =3, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "1%",
              Samp_Method  = 2,
              N_Replicates = 60 )


#%% 0.1% Cluster. 
#Baseline, Uniform Contamination with no sampling
Outs_0001_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "Baseline", 
              Spread  = "0.1%" ,
              Samp_Method  = 1,
              N_Replicates = 0)

####Preharvest_Sampling
# A 2 tomatoes
Outs_0001_1_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 2, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "2 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_0001_1_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 6, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "6 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_0001_1_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "20 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_0001_1_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "60 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_0001_1_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "20 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_0001_1_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 1, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="PH", 
              Mass = "60 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Harvest Sampling
# A 2 tomatoes
Outs_0001_2_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 2, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "2 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_0001_2_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 6, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "6 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_0001_2_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "20 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_0001_2_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "60 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_0001_2_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "20 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_0001_2_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 2, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="H", 
              Mass = "60 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Receiving Sampling
# A 2 tomatoes
Outs_0001_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_0001_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_0001_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_0001_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_0001_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_0001_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_0001_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_0001_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_0001_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_0001_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "0.1%",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_0001_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_0001_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =4, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "0.1%",
              Samp_Method  = 2,
              N_Replicates = 60 )

#%%
Outputs_100 = [
               Outs_100_1_A,Outs_100_1_B, Outs_100_1_C, Outs_100_1_D, Outs_100_1_E, Outs_100_1_F,
               Outs_100_2_A,Outs_100_2_B, Outs_100_2_C, Outs_100_2_D, Outs_100_2_E, Outs_100_2_F,
               Outs_100_3_A,Outs_100_3_B, Outs_100_3_C, Outs_100_3_D, Outs_100_3_E, Outs_100_3_F,
               Outs_100_4_A,Outs_100_4_B, Outs_100_4_C, Outs_100_4_D, Outs_100_4_E, Outs_100_4_F]

Outputs_010 = [
               Outs_010_1_A,Outs_010_1_B, Outs_010_1_C, Outs_010_1_D, Outs_010_1_E, Outs_010_1_F,
               Outs_010_2_A,Outs_010_2_B, Outs_010_2_C, Outs_010_2_D, Outs_010_2_E, Outs_010_2_F,
               Outs_010_3_A,Outs_010_3_B, Outs_010_3_C, Outs_010_3_D, Outs_010_3_E, Outs_010_3_F,
               Outs_010_4_A,Outs_010_4_B, Outs_010_4_C, Outs_010_4_D, Outs_010_4_E, Outs_010_4_F]

Outputs_001 = [
               Outs_001_1_A,Outs_001_1_B, Outs_001_1_C, Outs_001_1_D, Outs_001_1_E, Outs_001_1_F,
               Outs_001_2_A,Outs_001_2_B, Outs_001_2_C, Outs_001_2_D, Outs_001_2_E, Outs_001_2_F,
               Outs_001_3_A,Outs_001_3_B, Outs_001_3_C, Outs_001_3_D, Outs_001_3_E, Outs_001_3_F,
               Outs_001_4_A,Outs_001_4_B, Outs_001_4_C, Outs_001_4_D, Outs_001_4_E, Outs_001_4_F]

Outputs_0001 = [
               Outs_0001_1_A,Outs_0001_1_B, Outs_0001_1_C, Outs_0001_1_D, Outs_0001_1_E, Outs_0001_1_F,
               Outs_0001_2_A,Outs_0001_2_B, Outs_0001_2_C, Outs_0001_2_D, Outs_0001_2_E, Outs_0001_2_F,
               Outs_0001_3_A,Outs_0001_3_B, Outs_0001_3_C, Outs_0001_3_D, Outs_0001_3_E, Outs_0001_3_F,
               Outs_0001_4_A,Outs_0001_4_B, Outs_0001_4_C, Outs_0001_4_D, Outs_0001_4_E, Outs_0001_4_F]

#%%
Types_L = ["Preharvest","Preharvest","Preharvest","Preharvest","Preharvest","Preharvest",
           "Harvest", "Harvest","Harvest","Harvest","Harvest","Harvest",
           "Receiving","Receiving","Receiving","Receiving","Receiving","Receiving",
           "Packed Product", "Packed Product","Packed Product","Packed Product","Packed Product","Packed Product"]
Mass_L = [
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash"]


def get_Powers(df,Mass,Type):
    a=df.melt()
    a["Type"] = Type
    a["Mass"] = Mass
    return a 

def ger_powers_fromlist(powers_list, Clustering):
    counter_1 = 0
    list_df_powers= []
    for i in powers_list:
        df_out = get_Powers(df =i[0],Mass =Mass_L[counter_1] ,Type = Types_L[counter_1])
        list_df_powers.append(df_out)
        counter_1= counter_1+1
    Powers_df = pd.concat(list_df_powers)
    Powers_df['Cont'] = Clustering
    return Powers_df
    

Powers_all = pd.concat([ger_powers_fromlist(powers_list =Outputs_100 , Clustering = "100%"),
                        ger_powers_fromlist(powers_list =Outputs_010 , Clustering = "10%"),
                        ger_powers_fromlist(powers_list =Outputs_001 , Clustering = "1%"),
                        ger_powers_fromlist(powers_list =Outputs_0001 , Clustering = "0.1%")])

#Powers_all.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out11.csv")
Powers_all.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out_Rep.csv")

##Alternative Power

def ger_powers_fromlist(powers_list, Clustering):
    counter_1 = 0
    list_df_powers= []
    for i in powers_list:
        df_out = get_Powers(df =i[7],Mass =Mass_L[counter_1] ,Type = Types_L[counter_1])
        list_df_powers.append(df_out)
        counter_1= counter_1+1
    Powers_df = pd.concat(list_df_powers)
    Powers_df['Cont'] = Clustering
    return Powers_df
    

Powers_all = pd.concat([ger_powers_fromlist(powers_list =Outputs_100 , Clustering = "100%"),
                        ger_powers_fromlist(powers_list =Outputs_010 , Clustering = "10%"),
                        ger_powers_fromlist(powers_list =Outputs_001 , Clustering = "1%"),
                        ger_powers_fromlist(powers_list =Outputs_0001 , Clustering = "0.1%")])

#Powers_all.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out11.csv")
Powers_all.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out_Rep2B.csv")





#%%
def get_cont_samp(Outs):
    emptylist =[]
    for i in Outs:
       emptylist.append(i[2])
    return pd.concat(emptylist)
   
Samp_Point = pd.concat([
     get_cont_samp(Outs = Outputs_100),
     get_cont_samp(Outs = Outputs_010),
     get_cont_samp(Outs = Outputs_001),
     get_cont_samp(Outs = Outputs_0001)
    ])

#Samp_Point.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\SampPoint11.csv")
Samp_Point.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\SampPoint_Rep.csv")

#%%
def get_Prev_samp(Outs):
    emptylist =[]
    for i in Outs:
       emptylist.append(i[5])
    return pd.concat(emptylist)
   
Samp_Point_Prev = pd.concat([
     get_Prev_samp(Outs = Outputs_100),
     get_Prev_samp(Outs = Outputs_010),
     get_Prev_samp(Outs = Outputs_001),
     get_Prev_samp(Outs = Outputs_0001)
    ])

#Samp_Point_Prev.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\PrevSampPoint11.csv")
Samp_Point_Prev.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\PrevSampPoint_Rep.csv")


#%% Consumer Exposure
Outputs_100 = [Outs_100_0_0,
               Outs_100_1_A,Outs_100_1_B, Outs_100_1_C, Outs_100_1_D, Outs_100_1_E, Outs_100_1_F,
               Outs_100_2_A,Outs_100_2_B, Outs_100_2_C, Outs_100_2_D, Outs_100_2_E, Outs_100_2_F,
               Outs_100_3_A,Outs_100_3_B, Outs_100_3_C, Outs_100_3_D, Outs_100_3_E, Outs_100_3_F,
               Outs_100_4_A,Outs_100_4_B, Outs_100_4_C, Outs_100_4_D, Outs_100_4_E, Outs_100_4_F]

Outputs_010 = [Outs_010_0_0,
               Outs_010_1_A,Outs_010_1_B, Outs_010_1_C, Outs_010_1_D, Outs_010_1_E, Outs_010_1_F,
               Outs_010_2_A,Outs_010_2_B, Outs_010_2_C, Outs_010_2_D, Outs_010_2_E, Outs_010_2_F,
               Outs_010_3_A,Outs_010_3_B, Outs_010_3_C, Outs_010_3_D, Outs_010_3_E, Outs_010_3_F,
               Outs_010_4_A,Outs_010_4_B, Outs_010_4_C, Outs_010_4_D, Outs_010_4_E, Outs_010_4_F]

Outputs_001 = [Outs_001_0_0,
               Outs_001_1_A,Outs_001_1_B, Outs_001_1_C, Outs_001_1_D, Outs_001_1_E, Outs_001_1_F,
               Outs_001_2_A,Outs_001_2_B, Outs_001_2_C, Outs_001_2_D, Outs_001_2_E, Outs_001_2_F,
               Outs_001_3_A,Outs_001_3_B, Outs_001_3_C, Outs_001_3_D, Outs_001_3_E, Outs_001_3_F,
               Outs_001_4_A,Outs_001_4_B, Outs_001_4_C, Outs_001_4_D, Outs_001_4_E, Outs_001_4_F]

Outputs_0001 = [Outs_0001_0_0,
               Outs_0001_1_A,Outs_0001_1_B, Outs_0001_1_C, Outs_0001_1_D, Outs_0001_1_E, Outs_0001_1_F,
               Outs_0001_2_A,Outs_0001_2_B, Outs_0001_2_C, Outs_0001_2_D, Outs_0001_2_E, Outs_0001_2_F,
               Outs_0001_3_A,Outs_0001_3_B, Outs_0001_3_C, Outs_0001_3_D, Outs_0001_3_E, Outs_0001_3_F,
               Outs_0001_4_A,Outs_0001_4_B, Outs_0001_4_C, Outs_0001_4_D, Outs_0001_4_E, Outs_0001_4_F]

Types_L2 = ["Baseline","Preharvest","Preharvest","Preharvest","Preharvest","Preharvest","Preharvest",
           "Harvest", "Harvest","Harvest","Harvest","Harvest","Harvest",
           "Receiving","Receiving","Receiving","Receiving","Receiving","Receiving",
           "Packed Product", "Packed Product","Packed Product","Packed Product","Packed Product","Packed Product"]
Mass_L2 = ["Baseline",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash"]


def get_Exps(df,Mass,Type):
    a=sum(df["Total CFU"])
    b= pd.DataFrame({
        "Total_CFU": a,
        "Type":Type,
        "Mass":Mass},index=[0])
    return b 

def ger_exps_fromlist(exps_list, Clustering):
    counter_1 = 0
    list_df_powers= []
    for i in exps_list:
        df_out = get_Exps(df =i[6],Mass =Mass_L2[counter_1] ,Type = Types_L2[counter_1])
        list_df_powers.append(df_out)
        counter_1= counter_1+1
    Powers_df = pd.concat(list_df_powers)
    Powers_df['Cont'] = Clustering
    return Powers_df

Exps_all = pd.concat([ger_exps_fromlist(exps_list =Outputs_100 , Clustering = "100%"),
                        ger_exps_fromlist(exps_list =Outputs_010 , Clustering = "10%"),
                        ger_exps_fromlist(exps_list =Outputs_001 , Clustering = "1%"),
                        ger_exps_fromlist(exps_list =Outputs_0001 , Clustering = "0.1%")])

#Exps_all.to_csv(path_or_buf = "C:\\Users\\gareyes3\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Exps11.csv")
Exps_all.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Exps_Rep.csv")

#%%
#Additional Scenarios. 

#Harvesting Bucket!


Outs_HB_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =5, 
              Type ="Baseline", 
              Mass = "Baseline", 
              Spread  = "HB" ,
              Samp_Method  = 1,
              N_Replicates = 0)

##Receiving Sampling
# A 2 tomatoes
Outs_HB_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_HB_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_HB_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_HB_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_HB_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "HB",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_HB_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =5, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "HB",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_HB_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_HB_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_HB_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_HB_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "HB",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_HB_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "HB",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_HB_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =5, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "HB",
              Samp_Method  = 2,
              N_Replicates = 60 )


#%% Bin Contamination

Outs_BIN_0_0= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50 ,
              Hazard_Mean = 132_000, 
              Hazard_SD = 0,
              Samp_Plan = 0, 
              Tom_Per_Sample = 2, 
              Cont_Scen =6, 
              Type ="Baseline", 
              Mass = "Baseline", 
              Spread  = "HB" ,
              Samp_Method  = 1,
              N_Replicates = 0)

##Receiving Sampling
# A 2 tomatoes
Outs_BIN_3_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 2, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "2 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_BIN_3_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 6, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "6 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_BIN_3_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "20 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_BIN_3_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "60 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_BIN_3_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 20, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "20 Tomato Mash", 
              Spread  = "BIN",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_BIN_3_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 3, 
              Tom_Per_Sample = 60, 
              Cont_Scen =6, 
              Type ="R", 
              Mass = "60 Tomato Mash", 
              Spread  = "BIN",
              Samp_Method  = 2,
              N_Replicates = 60 )

##Packed Product Sampling
# A 2 tomatoes
Outs_BIN_4_A= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 2, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "2 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )
# B 6 tomatoes
Outs_BIN_4_B= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 6, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "6 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )
# C 20 tomatoes
Outs_BIN_4_C= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "20 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )

# D 60 tomatoes
Outs_BIN_4_D= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "60 Tomatoes", 
              Spread  = "BIN",
              Samp_Method  = 1,
              N_Replicates = 0 )

# E 20 tomato mash
Outs_BIN_4_E= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 20, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "20 Tomato Mash", 
              Spread  = "BIN",
              Samp_Method  = 2,
              N_Replicates = 20 )

# F 60 tomato mash
Outs_BIN_4_F= Analysis_Loop(HA_Iterations = 50,
              Loop_Iterations = 50,
              Hazard_Mean = 132_000, 
              Hazard_SD =0,
              Samp_Plan = 4, 
              Tom_Per_Sample = 60, 
              Cont_Scen =6, 
              Type ="PP", 
              Mass = "60 Tomato Mash", 
              Spread  = "BIN",
              Samp_Method  = 2,
              N_Replicates = 60 )
#%% Powers Additional Plans
Outputs_HB = [ Outs_HB_3_A,Outs_HB_3_B, Outs_HB_3_C, Outs_HB_3_D, Outs_HB_3_E, Outs_HB_3_F,
               Outs_HB_4_A,Outs_HB_4_B, Outs_HB_4_C, Outs_HB_4_D, Outs_HB_4_E, Outs_HB_4_F]

Outputs_BIN = [ Outs_BIN_3_A,Outs_BIN_3_B, Outs_BIN_3_C, Outs_BIN_3_D, Outs_BIN_3_E, Outs_BIN_3_F,
               Outs_BIN_4_A,Outs_BIN_4_B, Outs_BIN_4_C, Outs_BIN_4_D, Outs_BIN_4_E, Outs_BIN_4_F]

Types_L = ["Baseline","Receiving","Receiving","Receiving","Receiving","Receiving","Receiving",
           "Packed Product", "Packed Product","Packed Product","Packed Product","Packed Product","Packed Product"]
Mass_L = [
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash"]


Powers_all_ADD = pd.concat([ger_powers_fromlist(powers_list =Outputs_HB , Clustering = "Harvesting Bucket"),
                        ger_powers_fromlist(powers_list =Outputs_BIN , Clustering = "Harvesting Bin")])

Powers_all_ADD.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\Powers_Out_Additional.csv")

#%%



#%% Total Adulterant Cells System Endpoint
Outputs_HB = [Outs_HB_0_0,
               Outs_HB_3_A,Outs_HB_3_B, Outs_HB_3_C, Outs_HB_3_D, Outs_HB_3_E, Outs_HB_3_F,
               Outs_HB_4_A,Outs_HB_4_B, Outs_HB_4_C, Outs_HB_4_D, Outs_HB_4_E, Outs_HB_4_F]

Outputs_BIN = [Outs_BIN_0_0,
               Outs_BIN_3_A,Outs_BIN_3_B, Outs_BIN_3_C, Outs_BIN_3_D, Outs_BIN_3_E, Outs_BIN_3_F,
               Outs_BIN_4_A,Outs_BIN_4_B, Outs_BIN_4_C, Outs_BIN_4_D, Outs_BIN_4_E, Outs_BIN_4_F]


Types_L2 = ["Baseline",
           "Receiving","Receiving","Receiving","Receiving","Receiving","Receiving",
           "Packed Product", "Packed Product","Packed Product","Packed Product","Packed Product","Packed Product"]
Mass_L2 = ["Baseline",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash",
          "2 Tomatoes", "6 Tomatoes", "20 Tomatoes", "60 Tomatoes", "20 Tomato Mash", "60 Tomato Mash"]



Exps_all_ADD = pd.concat([ger_exps_fromlist(exps_list =Outputs_HB , Clustering = "Harvesting Bucket"),
                        ger_exps_fromlist(exps_list =Outputs_BIN , Clustering = "Harvesting Bin")])

Exps_all_ADD.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\TAC_Additional.csv")

#%%
def get_cont_samp(Outs):
    emptylist =[]
    for i in Outs:
       emptylist.append(i[2])
    return pd.concat(emptylist)
   
Samp_Point_ADD = pd.concat([
     get_cont_samp(Outs = Outputs_HB),
     get_cont_samp(Outs = Outputs_BIN),
    ])

Samp_Point_ADD.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\SampPoint_Additional.csv")

#%%
def get_Prev_samp(Outs):
    emptylist =[]
    for i in Outs:
       emptylist.append(i[5])
    return pd.concat(emptylist)
   
Samp_Point_Prev_ADD = pd.concat([
     get_Prev_samp(Outs = Outputs_HB),
     get_Prev_samp(Outs = Outputs_BIN)
    ])

Samp_Point_Prev_ADD.to_csv(path_or_buf = "C:\\Users\\Gustavo Reyes\\Documents\\GitHubFiles\\CPS-Farm-to-Facility_L_T\\Model\\Data_Tomato_Outputs\\PrevSampPoint_Additional.csv")
