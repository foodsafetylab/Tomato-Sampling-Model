# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 13:14:48 2022

@author: gareyes3
"""

#%%
import sys
sys.path
sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility_L_T\Model')

#%%
import Inputz_T
import pandas as pd
import numpy as np
import math
import random
import time

from numpy.random import Generator, PCG64
rng = Generator(PCG64())

#%%
Field_df=pd.DataFrame({"Tomato_ID": Inputz_T.Individual_Tomatoes,
                       "Plant_ID": Inputz_T.Individual_Plants[0:Inputz_T.Individual_Tomatoes.size],
                       "Pick_ID": Inputz_T.Pick_Random[0:Inputz_T.Individual_Tomatoes.size],
                       "Weight": Inputz_T.Tomato_weight,
                       "Harvester" : 0,
                       "Bucket":0,
                       "Bin": 0,
                       "Case_PH": 0,
                       "CFU": 0,
                       "CFU_BRej":"",
                       "Location": 1,
                       'PositiveSamples':0,
                       "Rej_Acc" :"Acc"
                  })

Field_df.PositiveSamples = [list() for x in range(len(Field_df.index))]
#print(time.time() - start_df, "df Creation")
        
#%%

def random_chunk(lst, chunk_size):
    nb_chunks = int(math.ceil(len(lst)/chunk_size))
    choice = random.randrange(nb_chunks) # 0 <= choice < nb_chunks
    return lst[choice*chunk_size:(choice+1)*chunk_size]

def field_cont_percetage2(df, percent_cont, Hazard_lvl,No_Cont_Clusters):
    No_Cont_Clusters = 1
    #This function contaminated the tomato field randomly based on a cluter of X%. 
    Percent_Contaminated =percent_cont #Percentage of tomatoes contaminated
    Percent_D_Contaminatinated= Percent_Contaminated/100 #Percentage in decimal point
    Hazard_lvl = Hazard_lvl #CFUs in contaminated area total Cells
    
    No_Cont_PartitionUnits= int(len(df)*Percent_D_Contaminatinated)
    Field_df_1 =df.loc[(df["Location"]==1) & (df["Rej_Acc"]=="Acc")].copy()
    
    if len(Field_df_1)>0:
        Hazard_lvl_percluster= Hazard_lvl / No_Cont_Clusters #(No_Cont_PartitionUnits*No_Cont_Clusters)
        for i in range(0,No_Cont_Clusters):
            random_Chunky = np.array(random_chunk(lst = df.index, chunk_size = No_Cont_PartitionUnits)) #creating random chunk
            Contamination_Pattern = rng.multinomial(Hazard_lvl_percluster,[1/No_Cont_PartitionUnits]*No_Cont_PartitionUnits,1) #spliting cont into chunks length
            random_Chunky_s= random_Chunky[np.isin(random_Chunky,np.array(Field_df_1.index))]
            Contamination_Pattern_s = Contamination_Pattern[0][range(0,len(random_Chunky_s))]
            Field_df_1.loc[random_Chunky_s, "CFU"] = Field_df_1.loc[random_Chunky_s, "CFU"] + Contamination_Pattern_s
            #Field_df_1.loc[random_Chunky, "CFU"] = Field_df_1.loc[random_Chunky, "CFU"] + Contamination_Pattern[0] #adding contmaination
            
        df.update(Field_df_1)
        return df
    
def F_Sampling_T (df, Pick_No, Location, NSamp_Unit, NoGrab):
    
    df_field_1 =df.loc[(df["Pick_ID"]==Pick_No) & (df["Location"]==Location)].copy()
    if len(df_field_1)>0:
        #print(Location, "Location")
        #print(df["Location"])
        #Unique_TestUnit = list(df[Test_Unit].unique())
        #Grab_Weight = Partition_Weight #In lb
        #for i in (Unique_TestUnit): #From sublot 1 to sublot n (same for pallet,lot,case etc)
        for l in range (1, NSamp_Unit+1): #Number of samples per sublot or lot or pallet.
            for j in range(NoGrab):
                CFU_hh=df_field_1["CFU"]
                #print(len(CFU_hh),"Length")
                List_Random=CFU_hh.sample(n=1)
                CFU = List_Random
                Index = List_Random.index[0]
                CFU_grab = CFU#*(Grab_Weight/(Partition_Weight*454))
                P_Detection=1-math.exp(-CFU_grab)
                RandomUnif = random.uniform(0,1)
                if RandomUnif < P_Detection:
                    #df_field_1.at[Index, 'PositiveSamples'].append(l)
                    df_field_1.at[Index, 'PositiveSamples'] = df_field_1.at[Index, 'PositiveSamples'] + 1
        df.update(df_field_1)
    return (df)


def F_Rejection_Rule_T (df, Pick_No, Av_Picks, Test_Unit, limit):
    #Unique_Test_Unit =list(df[Test_Unit].unique())
    df_field_1 =df.loc[(df["Pick_ID"].isin(Av_Picks))].copy()
    Reject = []
    #for  i in Unique_Test_Unit:
    df_Subset = df_field_1[df_field_1[Test_Unit] == Pick_No].copy()
    #List_of_grabs = df_Subset['PositiveSamples'].tolist()
    #flat_list = [item for sublist in  List_of_grabs for item in sublist]
    #Unique_Positives =list(np.unique(flat_list))
    Postives = sum(df_Subset['PositiveSamples'] >0)
    if Postives>limit:
        Reject.append(Test_Unit)
    df_field_1.PositiveSamples = 0 #this is in case everything gets rejected
    if len(Reject)>0:
     df_field_1.loc[:,"Rej_Acc"] = "REJ"
     df_field_1.loc[:,"CFU_BRej"] = df_field_1["CFU"]
     df_field_1.loc[:,"CFU"] = 0
     
        #df_Blank = df.iloc[[0]]
        #df_Blank.loc[:, ['CFU']] = 0
        #df_Blank.loc[:, ['Weight']] = SCInputz.Partition_Weight
        #df_Blank.loc[:, ['Accept']] = "All Rej"
        #df = df_Blank
    #else:
        #df = df[~df[Test_Unit].isin(Reject)]
    df.update(df_field_1)
    return df


Field_df = field_cont_percetage2(df = Field_df, percent_cont = 10, Hazard_lvl = 13200,No_Cont_Clusters = 1)

start_RR = time.time()

Field_df['PositiveSamples']

def Sampling_Multiple(df, iters): 
    collectdf = []
    for i in range(iters):
        
        df2= df.copy()
        
        df2 =F_Sampling_T (df = df2, Pick_No = 1, Location = 1, NSamp_Unit = 1, NoGrab = 60)
        start_RR = time.time()

        df2 =F_Rejection_Rule_T (df=df2, Pick_No =1, Av_Picks =[1,2,3], Test_Unit ="Pick_ID", limit = 0)
        print(time.time() - start_RR, "Rejection")
        if sum(df2["Rej_Acc"] == "REJ") > 0:
            collectdf.append(1)
        else:
            collectdf.append(0)
    
    pr_rej = sum(collectdf)/iters
    return pr_rej
    
Sampling_Multiple(df=Field_df, iters = 50)    


df5 =F_Sampling_T (df = Field_df, Pick_No = 1, Location =1, NSamp_Unit = 1, NoGrab = 60)
df6 =F_Rejection_Rule_T (df = df5, Pick_No = 1, Av_Picks = [1,2,3], Test_Unit = "Pick_ID", limit = 0)
sum(df6["Rej_Acc"] == "REJ") 

