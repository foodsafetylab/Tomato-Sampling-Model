# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 13:28:22 2022

@author: gareyes3
"""
#%%
import sys
sys.path
sys.path.append('C:\\Users\Gustavo Reyes\Documents\GitHubFiles\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility_L_T\Model')
sys.path.append('C:\\Users\\reyes\\Documents\\GitHub\\CPS-Farm-to-Facility_L_T\\Model')
#%%


import Funz_T
import Inputz_T
import numpy as np
import random
import pandas as pd
import numpy as np
import math
import time

from numpy.random import Generator, PCG64
rng = Generator(PCG64())



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
                       'PositiveSamples':"",
                       "Rej_Acc" :"Acc"
                  })

Field_df["CFU"] = 0
Field_df.loc[1:1000,"CFU"] = 1000

sum(Field_df["CFU"]>0)/len(Field_df)

from numba import jit, cuda
@jit(nopython = True)
def Cross_cont(vectorCFU,Tr_P_S, Tr_S_P):
    newvector = []
    ContS = 0
    for i in vectorCFU:
        TotTr_P_S= np.random.binomial(i,Tr_P_S) #Transfer from Product to Surfaces
        TotTr_S_P = np.random.binomial(ContS,Tr_S_P) #Trasnfer from Surfaces to product
        ContPNew = i-TotTr_P_S+TotTr_S_P #New Contmination on Product
        ContS=ContS+TotTr_P_S-TotTr_S_P #Remiining Contamination in Surface for upcoming batches
        newvector.append(ContPNew)
    return newvector


#from numba import jit, cuda
#@cuda.jit(target_backend='cuda') 
def F_CrossContProLine_tom (df, Tr_P_S, Tr_S_P, Location):
        #df_field_1 =df[df["Location"]==Location].copy()
        #index_vec = range(len(df_field_1["CFU"].copy()))
        #df.loc[df["Location"]==Location, "CFU"]
        vectorCFU = np.array(df.loc[df["Location"]==Location, "CFU"].copy())
        df.loc[df["Location"]==Location, "CFU"] = Cross_cont(vectorCFU,Tr_P_S, Tr_S_P)
        #df.update(df_field_1)
        return df
    
aa= np.array([])
aa=np.append(aa, 3)

aaa =  pd.Series([30, 0, 0 ,0])
aa_s = [0,0,0,0]

aaa = pd.DataFrame({
    "CFU": np.zeros(236200),
    "S": np.zeros(236200)
    })

def CCont(aaa,s):
    TotTr_P_S =np.random.binomial(aaa, 0.2)
    TotTr_S_P = np.random.binomial(s,0.1)
    aaa = aaa-TotTr_P_S+TotTr_S_P
    s = s+TotTr_P_S-TotTr_S_P
    return aaa

def CCont2(aaa):
    TotTr_P_S =np.random.binomial(aaa.CFU, 0.2)
    TotTr_S_P = np.random.binomial(aaa.S,0.1)
    aaa.CFU = aaa.CFU-TotTr_P_S+TotTr_S_P
    aaa.S = aaa.S+TotTr_P_S-TotTr_S_P
    return aaa

aaa.apply(func = CCont2,axis=1)


start_df = time.time()
Field_df=F_CrossContProLine_tom (df = Field_df, 
                                 Tr_P_S = Inputz_T.Tr_P_CB, 
                                 Tr_S_P = Inputz_T.Tr_CB_P,
                                 Location = 1 )

print(time.time() - start_df, "CC")



def F_CrossContProLine_tom2 (df, Tr_P_S, Tr_S_P,  Location, Sanitation_Freq_lb = 0, StepEff = 0 , compliance = 0):
        df_field_1 =df.loc[df["Location"]==Location].copy()
        rateweight = 0.57
        every_x_many = int(Sanitation_Freq_lb/rateweight)
        ContS=0
        vectorCFU = df_field_1["CFU"].copy()
        index_vec = range(len(vectorCFU))
        vectorCFU = np.array(vectorCFU)
        newvector=[]
        if every_x_many > 0:
            Cleaning_steps = np.arange(0, len(vectorCFU) , every_x_many )
        for i in index_vec:
            if compliance>0: #to not run if there is no sanitation.
                if random.uniform(0,1)<compliance:
                    if every_x_many > 0:
                        if i in Cleaning_steps:
                            ContS = ContS*10**StepEff
                            print ("cleaned")
            ContP = vectorCFU[i] #Contamination product
            ContS=int((1-Tr_S_P)*ContS+(Tr_P_S*ContP)) #Remiining Contamination in Surface for upcoming batches
            newvector.append(int((1-Tr_P_S)*ContP+(Tr_S_P*ContS)))
        df_field_1.loc[:,"CFU"] = newvector
        df.update(df_field_1)
        return df
    
#(1-Tr_P_S)*ContP+(Tr_S_P*ContS)
#(1-Tr_S_P)*ContS+(Tr_P_S*ContP)


start_df = time.time()
Field_df=F_CrossContProLine_tom2 (df = Field_df, 
                                 Tr_P_S = Inputz_T.Tr_P_CB, 
                                 Tr_S_P = Inputz_T.Tr_CB_P,
                                 Location = 1,
                                 Sanitation_Freq_lb = 0, 
                                 StepEff = 0 , 
                                 compliance = 0 )
print(time.time() - start_df, "CC")

##WashiNG
@jit(nopython =True)
def Wash_CC(Field_df_1_conts,logred_cont, Tras_old,transfer_cont):
    for i in range(len(Field_df_1_conts)):
        #logred_cont = -rng.normal(log_red_Wash_mean, logred_sd)
        Cont = Field_df_1_conts[i]
        if logred_cont>=0:
            GrowthCeil = math.ceil(logred_cont)
            Difference = logred_cont-GrowthCeil
            MaxCont = Cont*10**GrowthCeil
            Updated_CFUs = np.random.binomial(MaxCont,10**Difference)
        else:
            Updated_CFUs= np.random.binomial(Cont,10**logred_cont)
    
        if i == 0:
            upconts = Updated_CFUs
        if i >0:
            upconts = Updated_CFUs + Tras_old
        Transfer = np.random.binomial(Cont,10**transfer_cont)
        Tras_old = Transfer
        Field_df_1_conts[i] =upconts
    return (Field_df_1_conts)
    

def Tomato_Wash(df, Location, FC_lvl,i):
    #Parameters from https://www.sciencedirect.com/science/article/pii/S0963996916306081#f0010
    #Maffei. 
    #Backup https://www.sciencedirect.com/science/article/pii/S0740002019309694?casa_token=dt-V4Cbh89YAAAAA:FoQTt7f3Hly2-k9lJjUXPqkZ-W5tJChevsm2XIz3UTimqrYdUT9zAoqZUQlZWx1OhENvX3zqpqw
    #FC_lvl = np.random.triangular(0,5,10)
    if FC_lvl<10:
        log_red_Wash_mean = (FC_lvl*0.04)+0.3
    elif FC_lvl>=10:
        log_red_Wash_mean = (FC_lvl*0.0056)+0.5952    
    logred_sd = 0.175
    np.random.seed(i)
    logred_cont = -np.random.normal(log_red_Wash_mean, logred_sd)
    
    #Transfer to uncontaminated pieces. 
    Log_Trans_Upper = (-0.6798*FC_lvl)-0.6003
    Log_Trans_Lower = (-1.3596*FC_lvl)-0.6
    
    transfer_cont = np.random.uniform(Log_Trans_Lower,Log_Trans_Upper)
    
    #Field_df_1 =df[df["Location"]==Location].copy() #location 4 is wash water
    Field_df_1_conts = np.array(df.loc[df["Location"]==Location, "CFU"].copy())
    Tras_old= 0
    df.loc[df["Location"]==Location, "CFU"] = Wash_CC(Field_df_1_conts,logred_cont, Tras_old,transfer_cont)
    #df.update(Field_df_1)
    return df


start_df = time.time()
Field_df2=Tomato_Wash(df= Field_df, Location = 1, FC_lvl = 10, i = 20)
print(time.time() - start_df, "Wash")



    
####

def Survival_Salmonella_cucum2(Series,Time, RH, Temp):
    #time  in H
    #model obtained fromhttps://www.sciencedirect.com/science/article/pii/S0740002021001052#fig4
    Log_Change_7= 4.48385-0.00199*(Temp)*RH
    Day_Log_h = Log_Change_7/24/7 #Change in log CFU per hour
    total_change = -(Day_Log_h*Time)
    
    if total_change>=0:
        GrowthCeil = math.ceil(total_change)
        Difference = total_change-GrowthCeil
        MaxCont = Series*10**GrowthCeil
        Updated_CFUs = rng.binomial(MaxCont,10**Difference)
    else:
        Updated_CFUs= rng.binomial(Series,10**total_change)
    
    return Updated_CFUs


#rng.binomial(Field_df["CFU"].array, 10**-1)

def applying_survival_salmonella_cucum2(df, Time, RH, Temp, Location):
    start_df = time.time()
    df_field_1 =df.loc[(df["Location"]==Location)].copy()
    print(time.time() - start_df, "loc")
    
    start_df = time.time()
    df_field_1.loc[:,"CFU"] = Survival_Salmonella_cucum2(df_field_1["CFU"].array,
                                   Time= Time, 
                                   RH = RH, 
                                   Temp = Temp)
    print(time.time() - start_df, "app")
    
    start_df = time.time()
    df.update(df_field_1)
    print(time.time() - start_df, "update")
    return df


def Survival_Salmonella_cucum2(Series,Time, RH, Temp):
    #time  in H
    #model obtained fromhttps://www.sciencedirect.com/science/article/pii/S0740002021001052#fig4
    Log_Change_7= 4.48385-0.00199*(Temp)*RH
    Day_Log_h = Log_Change_7/24/7 #Change in log CFU per hour
    total_change = -(Day_Log_h*Time)
    
    if total_change>=0:
        GrowthCeil = math.ceil(total_change)
        Difference = total_change-GrowthCeil
        MaxCont = Series*10**GrowthCeil
        Updated_CFUs = rng.binomial(MaxCont,10**Difference)
    else:
        Updated_CFUs= rng.binomial(Series,10**total_change)
    
    return Updated_CFUs

def applying_survival_salmonella_cucum3(df, Time, RH, Temp, Location):
    
    df1=df.copy()
    
    Log_Change_7= 4.48385-0.00199*(Temp)*RH
    Day_Log_h = Log_Change_7/24/7 #Change in log CFU per hour
    total_change = -(Day_Log_h*Time)
    
    if total_change>=0:
        GrowthCeil = math.ceil(total_change)
        Difference = total_change-GrowthCeil
        #MaxCont = Series*10**GrowthCeil
        df1['CFU'] = np.where(df['Location']==Location, rng.binomial((df1['CFU']*10**GrowthCeil),10**Difference), df1['CFU'])
        #Updated_CFUs = rng.binomial(MaxCont,10**Difference)
    else:
        df1['CFU'] = np.where(df1['Location']==Location, rng.binomial((df1['CFU']),10**total_change), df1['CFU'])
        #Updated_CFUs= rng.binomial(Series,10**total_change)
    
    return df1
    

#Survival_Salmonella_cucum2(Series = np.array(Field_df["CFU"]),Time = 12, RH = 74, Temp =22)

Field_df["CFU"] = 10000

Field_df
start_df = time.time()
df1 =applying_survival_salmonella_cucum3(df = Field_df, Time = 12, RH = 74, Temp = 22, Location =1)
print(time.time() - start_df, "Wash")

Field_df["CFU"] = 10000

start_df = time.time()
df2 = applying_survival_salmonella_cucum2(df = Field_df, Time = 12, RH = 74, Temp = 22, Location =1)
print(time.time() - start_df, "Wash")


start_df = time.time()
Field_df.loc[(Field_df["Location"]==1)].copy()
print(time.time() - start_df, "Wash")

Field_df[(Field_df["Location"]==1)].copy()


Field_df['CFU'] = np.where(Field_df['Location']==1, rng.binomial(Field_df['CFU'],10**-1), Field_df['CFU'])

######
def Update_Location(df, Previous, NewLoc):
    df_field_1 =df.loc[df["Location"]==Previous].copy()
    df_field_1.loc[:,"Location"] =NewLoc
    df.update(df_field_1)
    return df

def Update_Location2(df, Previous, NewLoc):
    df1 =df.copy()
    df1["Location"] = np.where(df1['Location']==Previous, NewLoc, df1['Location'])
    return df1


start_df = time.time()
df3 =Update_Location2(df = Field_df, Previous =2, NewLoc =3)
print(time.time() - start_df, "Wash")

start_df = time.time()
df3 =Update_Location(df = Field_df, Previous =2, NewLoc =3)
print(time.time() - start_df, "Wash")

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

Field_df["CFU"] = 0
Field_df.loc[1:1000,"CFU"] = 1000





def F_Sampling_T (df, Pick_No, Location, NSamp_Unit, NoGrab):
    df2= df.copy()
    if len(df2.loc[(df2["Pick_ID"]==Pick_No) & (df2["Location"]==Location)])>0:
        #print(Location, "Location")
        #print(df["Location"])
        #Unique_TestUnit = list(df[Test_Unit].unique())
        #Grab_Weight = Partition_Weight #In lb
        #for i in (Unique_TestUnit): #From sublot 1 to sublot n (same for pallet,lot,case etc)
        CFU_hh=df.loc[(df2["Pick_ID"]==Pick_No) & (df2["Location"]==Location), "CFU"]
        for l in range (1, NSamp_Unit+1): #Number of samples per sublot or lot or pallet.
            for j in range(NoGrab):
                #print(len(CFU_hh),"Length")
                List_Random=CFU_hh.sample(n=1)
                CFU = List_Random
                Index = List_Random.index[0]
                CFU_grab = CFU#*(Grab_Weight/(Partition_Weight*454))
                P_Detection=1-math.exp(-CFU_grab)
                RandomUnif = random.uniform(0,1)
                if RandomUnif < P_Detection:
                    #df_field_1.at[Index, 'PositiveSamples'].append(l)
                    df2.at[Index, 'PositiveSamples'] = df2.at[Index, 'PositiveSamples'] + 1
                    print("positive")
        #df.update(df_field_1)
    return (df2)



start_df = time.time()
df22=F_Sampling_T (df= Field_df, Pick_No = 1, Location = 1, NSamp_Unit = 1, NoGrab= 60)
print(time.time() - start_df, "Wash")



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



start_df = time.time()
F_Rejection_Rule_T (df = Field_df, Pick_No = 1, Av_Picks = [1,2,3], Test_Unit ="Pick_ID", limit = 0)
print(time.time() - start_df, "Wash")