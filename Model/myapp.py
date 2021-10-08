# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 09:16:17 2021

@author: gareyes3
"""
#import sys
#sys.path
#sys.path.append('C:\\Users\gareyes3\Documents\GitHub\CPS-Farm-to-Facility\Model')

import streamlit as st
import pandas as pd

import pandas as pd 
import seaborn as sns
from matplotlib import pyplot as plt
import base64


#Own Libraries ----------------------------------------------------------------
import Funz
import ContScen
import Listz 
import OutFunz
import InFunz
import ScenCondz
import ContCondz
import Inputz
from importlib import reload 

reload(Listz)
reload(Inputz)
#Main Model Loops
import MainModel3z


#Input SideBar=======================================================================================================================================

st.sidebar.header('Scenario Input Parameters')
#FieldPackLettuce
ScenCondz.Field_Pack = st.sidebar.checkbox("Field Pack Lettuce?")


#Field Size
Inputz.Field_Weight = st.sidebar.select_slider('Field Size [Lb]',options=[1000,10000,50000,100000,200000],value = 100000)
Inputz.slot_weight = st.sidebar.select_slider('Sublot Size [Lb]',options=[1000,10000,50000,100000,200000],value = 10000)

#Contamination Scenarios ----------------------------------------------------
st.sidebar.write("""
Select Contamination Scenarios:
""")

layout = st.sidebar.columns([4, 4])
with layout[0]: 
    ContCondz.Background_C = st.checkbox("Background")
    ContCondz.Point_Source_C = st.checkbox("Point Source")
    ContCondz.Systematic_C = st.checkbox("Systematic")
    ContCondz.Crew_C = st.checkbox(" Harvesting Crew")
 
with layout[-1]: 
    ContCondz.Harvester_C = st.checkbox("Harvester")
    ContCondz.PE_C = st.checkbox("Processing Equipment")
    ContCondz.Pack_C = st.checkbox("Packing")
    
#Contamination Tunning Parameters---------------------------------------------
st.sidebar.write("""
Contamination Tunning Parameters:
""")

if ContCondz.Background_C == True:
    Inputz.BGHazard_lvl = st.sidebar.number_input("Background Hazard Level [CFU]", value = 50000)
    
  
if ContCondz.Point_Source_C == True:
    Inputz.PSHazard_lvl = st.sidebar.number_input("Point Source Hazard Level [CFU]", value = 50000)
    Inputz.PSNo_Cont_Clusters = st.sidebar.number_input("Point Source: Number contamination clusters", value = 4, max_value = 100 )
    SL_maxVALPS =  int(Inputz.Field_Weight/Inputz.PSNo_Cont_Clusters)
    Inputz.PSCluster_Size = st.sidebar.slider('Cluster Size [Lb]',min_value=1000, max_value=SL_maxVALPS, step=1000)#st.sidebar.number_input("Cluster Size [lb]. (1K lb. increments)", value = 1000, step = 1000 )

if ContCondz.Systematic_C == True:
    Inputz.SysHazard_lvl = st.sidebar.number_input("Systematic Hazard Level [CFU]", value = 50000)
    Inputz.SysNo_Cont_Clusters = st.sidebar.number_input("Systematic: Number contamination clusters", value = 1, max_value = 10 )
    SL_maxVALSys =  int(Inputz.Field_Weight/Inputz.SysNo_Cont_Clusters)
    Inputz.SysCluster_Size = st.sidebar.slider('Cluster Size [Lb]',min_value=10000, max_value=SL_maxVALSys, step=10000)


#Sampling Strategies --------------------------------------------------------
st.sidebar.write("""
Select Sampling Strategy:
""")

layoutSamp = st.sidebar.columns([3, 3])
with layoutSamp[0]: 
    ScenCondz.Baseline_Sampling = st.checkbox("No Sampling")
    ScenCondz.PH_Sampling = st.checkbox("PreHarvest")
    ScenCondz.H_Sampling = st.checkbox("Harvest")

 
with layoutSamp[-1]: 
    ScenCondz.R_Sampling = st.checkbox("Receiving")
    ScenCondz.FP_Sampling = st.checkbox("Finished Product")

#Sampling Strategies
st.sidebar.write("""
Sampling Tunning Parameters:
""")

#Sampling Tuning Parameters ----------------------------------------------------------

#Baseline
if ScenCondz.Baseline_Sampling ==True:
    st.sidebar.write("""
None
""")

#Pre-Harvest
if ScenCondz.PH_Sampling ==True:
    st.sidebar.write("""
Pre-Harvest sampling tuning parameters
""")
    PH_S_Stratgy = st.sidebar.selectbox(label = "Select Type of Pre-Harvest Sampling", options = ["4 day", "4 Hour", "Intense"])
    if  PH_S_Stratgy == "4 day":
        ScenCondz.PHS_4d = True
    elif PH_S_Stratgy == "4 Hour":
        ScenCondz.PHS_4h = True
    elif PH_S_Stratgy == "Intense":
        ScenCondz.PHS_Int = True
        
    Inputz.sample_size_PH = st.sidebar.number_input("Enter Sample Size [g]", value = 300)
    if PH_S_Stratgy == "4 day" or PH_S_Stratgy == "4 Hour":
        Inputz.n_samples_slot_PH =st.sidebar.number_input("Samples per Sublot", value = 1)
    elif PH_S_Stratgy == "Intense":
         Inputz.n_samples_slot_PH =st.sidebar.number_input("Samples per Lot", value = 10)
#In-Harvest



def get_table_download_link_csv(df):
    #csv = df.to_csv(index=False)
    csv = df.to_csv().encode()
    #b64 = base64.b64encode(csv.encode()).decode() 
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="Results.csv" target="_blank">Download csv file</a>'
    return href



#Header============================================================================================================-

#Main Header and Title for the model
st.write("""
# CPS Farm to Facility Web App
This App Predicts the Following:
- Percent of CFU Rejected
- Percent of Lb. Rejected
""")

st.subheader('Tune Run:')
Inputz.N_Iterations = st.number_input("Enter Number of Iterations",value = 10, min_value = 0, max_value =1000)

#Looks
if st.button('Click Here to Iterate'):
    #Side Bar Inputs
    Main_Mod_Outs=MainModel3z.F_MainLoop()
    D_PH4d = Main_Mod_Outs[1]
    DProg_PH4d=Main_Mod_Outs[0]
    
    
    #Results
    st.subheader('Results')
    st.subheader('Outputs DataFrame')
    st.write(D_PH4d)
    st.markdown(get_table_download_link_csv(D_PH4d), unsafe_allow_html=True)
    
    st.subheader('Boxplot')
    fig = plt.figure(figsize=(8,4)) # try different values
    sns.boxplot(y=D_PH4d["PerRejected at PH"])
    plt.ylabel("Percent CFU Rejected by Sampling Plan")

    st.pyplot(fig)
    
    

    

    


