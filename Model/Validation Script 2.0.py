# -*- coding: utf-8 -*-
"""
Created on Tue Mar  8 14:17:16 2022

@author: gareyes3
"""

#%%
import sys, os
sys.path
#sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility\Model')
sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility\Model')

# %%
from importlib import reload
import numpy as np
import Listz
import pandas as pd
import MainModel3z
import SCInputz
import Inputz
import ContCondz
import ScenCondz
import InFunz
import OutFunz
import ContScen
import Funz
from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter
import seaborn as sns
import sys
import random
import Dictionariez
import SCInputsValidation
sys.path
#sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility\Model')
sys.path.append(
    'C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility\Model')

#%%
Total_grams= 100_000*454


CFU_10000g = Total_grams/10000 #-4 log
CFU_1000g = Total_grams/1000  #-3 log
CFU_100g = Total_grams/100 #-2 log
CFU_10g = Total_grams/10  #-1 log
CFU_g =  Total_grams #0 log
CFU_0_1g = Total_grams*10 #1 log


CFU_0_01g = Total_grams*100 #2log
CFU_0_001g = Total_grams*1000 #3log

#%%

def Sampling_Validation(Hazard_Level, Sample_Size, Number_Grabs, iterations):
    Rejection_List = []
    for i in range(iterations):
        #Creation of the Data Frame to Track: 
        df= InFunz.F_InDF(Partition_Units = 2_000,
                          Field_Weight = 100_000, 
                          slot_number = 10)
               
        #Adding Contamination depending on challenge Systematic Sampling
        
        df = ContScen.F_systematic_C(df=df, Hazard_lvl= Hazard_Level,
                                     No_Cont_Clusters =1,
                                     Cluster_Size= 100_000,
                                     Partition_Weight = 50)
            
        
        
        #Sampling at Pre-Harvest
        
        df = Funz.F_Sampling_2(df =df,Test_Unit ="Lot", 
                                      NSamp_Unit = 1, 
                                      Samp_Size =Sample_Size, 
                                      Partition_Weight =50, 
                                      NoGrab =Number_Grabs )
        
        df=Funz.F_Rejection_Rule3(df =df, Test_Unit = SCInputz.RR_PH_Trad, limit = SCInputz.Limit_PH) 
        
        if df["Weight"].sum() == 50:
            print("Rejected")
            Rejection_List.append(0)
        else:
            print("Accepted")
            Rejection_List.append(1)
    
    return Rejection_List

def Sampling_Validation_PS(Hazard_Level, Sample_Size, Number_Grabs, iterations):
    Rejection_List = []
    for i in range(iterations):
        #Creation of the Data Frame to Track: 
        df= InFunz.F_InDF(Partition_Units = 2_000,
                          Field_Weight = 100_000, 
                          slot_number = 10)
               
        #Adding Contamination depending on challenge Systematic Sampling
        
        df = ContScen.F_systematic_C(df=df, Hazard_lvl= Hazard_Level,
                                     No_Cont_Clusters =1,
                                     Cluster_Size= 300,
                                     Partition_Weight = 50)
            
        
        
        #Sampling at Pre-Harvest
        
        df = Funz.F_Sampling_2(df =df,Test_Unit ="Lot", 
                                      NSamp_Unit = 1, 
                                      Samp_Size =Sample_Size, 
                                      Partition_Weight =50, 
                                      NoGrab =Number_Grabs )
        
        df=Funz.F_Rejection_Rule3(df =df, Test_Unit = SCInputz.RR_PH_Trad, limit = SCInputz.Limit_PH) 
        
        if df["Weight"].sum() == 50:
            print("Rejected")
            Rejection_List.append(0)
        else:
            print("Accepted")
            Rejection_List.append(1)
    
    return Rejection_List
#%%
###################### UNIFORM #######################
Tuning_Contamination_levels = [CFU_10000g,CFU_1000g,CFU_100g,CFU_10g]
Tuning_SampleSize =[180,360,900,1800,3600]#[60,120,300,600,1200]
Tuning_NoGrabs = [60,120,300,600,1200]

Frames = []
for k in Tuning_Contamination_levels:
    for i in Tuning_NoGrabs:
        
        Hazard_Level = k
        Number_Grabs = i
        Sample_Size = i*3
        iterations = 1000
        
        Results = Sampling_Validation(Hazard_Level, Sample_Size, Number_Grabs, iterations)
        
        Contlvl_List = [k]*iterations
        Grabs_List = [i]*iterations
        Size_List = [i*3]*iterations
        
        dic={'Cont_Level': Contlvl_List, 
             'Grabs': Grabs_List,
             "Mass":Size_List,
             "Acceptance": Results}
        df = pd.DataFrame(dic)
        Frames.append(df)

FinalDF = pd.concat(Frames)   

FinalDF["Cont_Level"].replace({CFU_10000g: "1 CFU/10kg",
                                    CFU_1000g: "1 CFU/kg",
                                    CFU_100g: "1 CFU/100g", 
                                    CFU_10g: "1 CFU/10g"}, inplace=True)  

sns.lineplot(x="Grabs", y="Acceptance", hue = "Cont_Level" ,data=FinalDF)
plt.xlabel("Number of 3g samples")
plt.ylabel("% of contamination Accepted")
plt.title("Area Contamination, Uniform")
# Put the legend out of the figure
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        
#%%
########################POINT SOURce##############################
Tuning_Contamination_levels = [CFU_0_001g]
Tuning_NoGrabs = [60,120,300,600,1200]

Frames = []
for k in Tuning_Contamination_levels:
    for i in Tuning_NoGrabs:
        
        Hazard_Level = k
        Number_Grabs = i
        Sample_Size = i*3
        iterations = 100
        
        Results = Sampling_Validation_PS(Hazard_Level, Sample_Size, Number_Grabs, iterations)
        
        Contlvl_List = [k]*iterations
        Grabs_List = [i]*iterations
        Size_List = [i*3]*iterations
        
        dic={'Cont_Level': Contlvl_List, 
             'Grabs': Grabs_List,
             "Mass":Size_List,
             "Acceptance": Results}
        df = pd.DataFrame(dic)
        Frames.append(df)

FinalDF_PS = pd.concat(Frames)   

FinalDF_PS["Cont_Level"].replace({CFU_10000g: "1 CFU/10kg",
                                    CFU_1000g: "1 CFU/kg",
                                    CFU_100g: "1 CFU/100g", 
                                    CFU_10g: "1 CFU/10g"}, inplace=True)  

sns.lineplot(x="Grabs", y="Acceptance" ,data=FinalDF_PS)
plt.xlabel("Number of 3g samples")
plt.ylabel("% of contamination Accepted")
plt.title("Area Contamination, Uniform")
# Put the legend out of the figure
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)