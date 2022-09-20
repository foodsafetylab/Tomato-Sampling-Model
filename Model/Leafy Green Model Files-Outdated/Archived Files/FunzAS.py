import pandas as pd
import numpy as np
import scipy.stats as stats
import math
import random


#Function Source File
#%% Utility Functions
#Normal Truncated function
def Func_NormalTrunc(Min,Max, Mean, SD):
     X= stats.truncnorm((Min - Mean) / SD, (Max - Mean) / SD, loc=Mean, scale=SD)
     Y=(np.float(X.rvs(1)))
     return Y

#%% Die off functions    

#Die-off model

def F_DieOff1():
    Die_off_rate1=Func_NormalTrunc(-16.52,-0.47, -7.07,3.41)
    return Die_off_rate1

def F_DieOff2():
    Die_off_rate2=Func_NormalTrunc(-1.94,3.04, -0.24,0.70)
    return Die_off_rate2

#Die -off from Irrigation to Pre-Harvest
def F_DieOff_IR_PH(Time, Break_Point,Dieoff1, Dieoff2):
    TimeD = Time
    if TimeD < Break_Point: 
        T_Die_off= Dieoff1*TimeD
    elif TimeD >= Break_Point:
        Seg1T = TimeD-Break_Point
        T_Die_off1=Dieoff1*Seg1T
        Seg2T = TimeD - Seg1T
        T_Die_off2= Dieoff2*Seg2T
        T_Die_off = T_Die_off1+T_Die_off2
    return T_Die_off

#Die-off from Pre-Harvest Sampling to Harvest sampling
def F_DieOff_PHS_HS(Time,Time_Agg,Break_Point ,Dieoff1, Dieoff2 ):
    if Time_Agg < Break_Point: 
        TimeLeft = Break_Point-Time_Agg
        if Time < TimeLeft:
            T_Die_off = Dieoff1*Time
        elif Time >=TimeLeft:
            Seg1T = Time-TimeLeft
            T_Die_off1=Dieoff1*Seg1T
            Seg2T = Time-Seg1T
            T_Die_off2=Dieoff2*Seg2T
            T_Die_off = T_Die_off1+T_Die_off2
    elif Time_Agg>=Break_Point:
        T_Die_off=Dieoff2*Time
    return T_Die_off


def F_Simple_DieOff (Time): 
    Reduction = -((Time/2.45/24)**0.3)
    return Reduction

#%% Growth  or Reduction Models
#Cold Storage growth Model
def F_Growth(DF,Temperature, TimeD ):
    b=0.0616
    T0= 2.628
    if (Temperature-T0) <0:
        TDif = 0
    else:
        TDif = Temperature-T0
    Growth1D = (b*TDif)**2
    TotalGrowth = Growth1D*TimeD #Change Log CFU
    DF['CFU']=DF['CFU']*10**TotalGrowth #Final Growth change CFU/g
    return DF


#Washing
def F_Washing (DF, LogRedWash):
    DF.CFU=DF.CFU*10**-LogRedWash 
    return DF

#%% Contamination Functions

#Calculation of E.coli in Water
def F_Ecoli_Water():   
    Cw = random.uniform(1,235)
    X = stats.truncnorm((-5 - -1.9) / 0.6, (0 - -1.9) / 0.6, loc=-1.9, scale=0.6)
    Rw_1=(np.float(X.rvs(1)))
    Rw = 10**Rw_1
    Y = stats.truncnorm((0 - 0.108) / 0.019, (5 - 0.108) / 0.019, loc=0.108, scale=0.019)
    W=np.float(Y.rvs(1))
    Ci = (Cw/100)*Rw*W
    return Ci

def F_HarvestingCont ():
    Cs = 10**Func_NormalTrunc(Min=0, Max=3.67, Mean = 0.928, SD=1.11) #Soil, E.coli conc
    Rs = 10**Func_NormalTrunc(Min=-5, Max=0, Mean = -1.9, SD=0.6) #prob
    M = 10.22 #g soil in blades
    Nb = Cs *Rs*M #E coli cells in Blade CFU
    Rt1 = 0.0013 #Trasnfer Rate from soil to Lettuce
    Nh1 = Nb*Rt1 #Total E coli from harvesting blades to lettuce
    return Nh1

#%% Sampling Functions

#Sampling Sublots
#df =dateframe,
#NoSampleLot = Number of samples per lot
#Sample_size = Composite sample weight
#Cluster_Unit_weight 
#Limit= Limit CFU
#Grabs = Total grabs per sublot
def F_Sampling(df,Test_Unit, NSamp_Unit, Samp_Size, Clust_Weight, Limit, NoGrab ):
    Results=[]
    Unique_TestUnit=list(df[Test_Unit].unique())
    for i in (Unique_TestUnit):
        Reject_Lis=[]
        for l in range (NSamp_Unit):
            Sampled_Grabs =df[df[Test_Unit] == i].sample(NoGrab, replace= True)
            Sampled_Grabs =list(Sampled_Grabs.CFU)
            Grab_Weight = Samp_Size/NoGrab
            Detected = []
            for j in Sampled_Grabs: 
                CFU_grab = j*(Grab_Weight/(Clust_Weight*454))
                P_Detection=1-math.exp(-CFU_grab)
                if random.uniform(0,1)<P_Detection:
                    Reject_YN=1
                else:
                    Reject_YN=0
                Detected.append(Reject_YN)
                if sum(Detected)>0:
                    Detected_YN = 1
                elif sum(Detected) ==0:
                    Detected_YN =0
            Reject_Lis.append(Detected_YN)
            print("Hey",Reject_Lis)
        a=sum(Reject_Lis)
        if a > Limit:
            AR= False
        else:
            AR= True
        print("Yo",AR)
        Results.append(AR)
        print("Results",Results)
    data1 =  {Test_Unit: Unique_TestUnit,
           'Accept_Reject': Results}
    dT = pd.DataFrame(data1)
    dT= dT.loc[dT['Accept_Reject'] == False]
    ListR= list(dT[Test_Unit])
    return(ListR)

def F_SamplingFProd (df, Test_Unit, N_SampPacks, Grab_Weight):
    Results=[]
    Clust_Weight = int(df.loc[1,"Weight"]*454)
    Sampled_Packs = list(df[Test_Unit].sample(N_SampPacks))
    for i in Sampled_Packs:
        CFU = df.loc[df['PackNo'] == i, 'CFU'].values[0]
        CFU_grab = CFU*(Grab_Weight/(Clust_Weight*454))
        P_Detection=1-math.exp(-CFU_grab)
        if random.uniform(0,1)<P_Detection:
            Reject_YN=1
        else:
            Reject_YN=0
        Results.append(Reject_YN)
        if sum(Results) == 1:
            Detected_YN = 1
        elif sum(Results) ==0:
            Detected_YN =0
    return Detected_YN

#%% Partitioning and Mixing Functions




#Paritioning Function
def F_Partitioning(DF,NPartitions):
    AllParts_Cont = []
    for i, row in DF.iterrows():
        Cont = DF.at[i,'CFU']
        PartCont=np.random.multinomial(Cont,[1/NPartitions]*NPartitions,size=1)
        PartCont = PartCont[0]
        AllParts_Cont.append(PartCont)
    b_flat = [j for i in AllParts_Cont for j in i]
    newdf = pd.concat([DF]*NPartitions,axis=0)
    newdf=newdf.sort_values(by=['PalletNo'])
    #Pallet_List=(list(range(1,NPartitions+1)))
    newdf["PackNo"] =list(range(1,len(newdf.index)+1))#np.tile(Pallet_List, len(newdf)//NPartitions)
    newdf = newdf.reset_index(drop=True)  
    newdf.Weight=newdf.Weight/NPartitions
    newdf.CFU = b_flat
    newdf["Sublot"] = 1
    newdf = newdf[['PalletNo','PackNo','CFU','Weight', 'Sublot','ProLine','Lot']]
    return newdf

def F_Lots_FP(df, Nolots):
    l = len(df.index) // Nolots 
    df.loc[:l - 1, "Sublot"] = Nolots-1
    df.loc[l:, "Sublot"] = Nolots
    return df

def F_Mixing(DF):
    CFU_Summation = sum(DF.CFU)
    gram_Summation = sum(DF.Weight)*454
    Cont = CFU_Summation/gram_Summation
    ArrayUnique= pd.unique(DF['Sublot'])
    data1 = {'Sublot': [ArrayUnique],
       'Lot': 1,
       'Cont':Cont,
       'CFU':CFU_Summation,
       'Accept': True,
       'Weight': sum(DF.Weight)}
    df1 = pd.DataFrame(data1)  
    return df1



def parts(a, b):
    q, r = divmod(a, b)
    return [q + 1] * r + [q] * (b - r)


def F_Partitioning2(DF, Partition_Weight):
    LWeights = []
    LXX_2 = []
    for i,row in DF.iterrows():
        Weight= int(DF.at[i,'Weight'])
        xx_2=int(Weight//Partition_Weight)
        LXX_2.append(xx_2)
        Weight2 = parts(Weight,xx_2)
        LWeights.append(Weight2)  
    LWeightsFlat = [item for sublist in  LWeights for item in sublist]
    newDF= DF.loc[DF.index.repeat(LXX_2)]
    newDF["Weight"] = LWeightsFlat
    AllParts_Cont = []
    b_flat=[]
    DF['Parts'] =LXX_2
    for i, row in DF.iterrows():
            Cont = DF.at[i,'CFU']
            Parts = int(DF.at[i,'Parts'])
            PartCont=np.random.multinomial(Cont,[1/Parts]*Parts, size =1)
            PartCont = PartCont[0]
            AllParts_Cont.append(PartCont)
    b_flat = [j for i in AllParts_Cont for j in i]
    newDF.CFU = b_flat
    return newDF


