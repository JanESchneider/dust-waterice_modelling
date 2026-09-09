# ------------------------------------------------------------------------------------- #
# plot_data.py  -> more or less a testing ground for now
#
# Plotting routine, might be expanded and/or altered if necessary... 
# To do: auskommentierte Funktionen sortieren/entfernen
#  
#
# ------------------------------------------------------------------------------------- #

import sys
sys.path.append("/home/jschneider/Proj_WaterIce/00_global")
from functions import *

file_data_8 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.888889_waterCore_0.111111_waterMantle_0.000000_ratio_8.0to1/dustkappa.dat"
file_data_7 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.882353_waterCore_0.000000_waterMantle_0.117647_ratio_7.5to1/dustkappa.dat"
file_data_5 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.833333_waterCore_0.166667_waterMantle_0.000000_ratio_5.0to1/dustkappa.dat"
file_data_2 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.666667_waterCore_0.333333_waterMantle_0.000000_ratio_2.0to1/dustkappa.dat"
file_data_lab = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_labdata/dustkappa.dat"

filedata_arr = np.array([file_data_2, file_data_5, file_data_7, file_data_8, file_data_lab])
labels = np.array(["model ratio 2:1", "model ratio 5:1", "model ratio 7.5:1", "model ratio 8:1", "lab"])

for path, tag in zip(filedata_arr, labels):
    # Use fr for the f-string + raw string to handle the LaTeX $ subscripts correctly
    plot_opacity_components(path, label=fr"MgFeSiO$_4$ ({tag})")
plt.show()
