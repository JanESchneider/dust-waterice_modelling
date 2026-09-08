# ------------------------------------------------------------------------------------- #
# plot_data.py
#
# Plotting routine, might be expanded and/or altered if necessary... 
# To do: auskommentierte Funktionen sortieren/entfernen
#  
# ------------------------------------------------------------------------------------- #

import sys
sys.path.append("/home/jschneider/Proj_WaterIce/00_global")
from functions import *

file_data = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/rho_3.71_SIL_0.833333_waterCore_0.166667_waterMantle_0.000000_ratio_5.0to1/dustkappa.dat"


#plt.figure(figsize=(10, 6))
plot_opacity_components(file_data, label="MgFeSiO$_4$ lab")
plt.show()