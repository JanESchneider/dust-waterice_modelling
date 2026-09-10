# ------------------------------------------------------------------------------------- #
# data_conversion.py
#
# This routine stacks separate n- and k-data and writes them into one .lnk file 
# The wavenumber is also converted into wavelength [µm] for further processing
#  
# ------------------------------------------------------------------------------------- #

import sys
sys.path.append("/home/jschneider/Proj_WaterIce/00_global")
from functions import *

# ------------------------------------------------------------------------------------- #
# Set up data for convenience

n_data = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/n_MgFeSiO4+H2O_4.5_150K"
k_data = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/k_MgFeSiO4+H2O_4.5_150K"

n_data_transwater = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/n_trans_water_150.txt"
k_data_transwater = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/k_trans_water_150.txt"

output_pathfile = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/MgFeSiO4.lnk"
output_pathfile_transwater = "/home/jschneider/Proj_WaterIce/data/nk_data_potapov/trans_water_150.lnk"

# ------------------------------------------------------------------------------------- #

#merge_lab_data(n_data, k_data, output_pathfile, 3.71)
#merge_lab_data(n_data_transwater, k_data_transwater, output_pathfile_transwater, 0.93)
#merge_lab_data("Ice_n.txt", "Ice_k.txt", "Ice.lnk")

input = "/home/jschneider/Downloads/olmg50.txt"
output = "/home/jschneider/Proj_WaterIce/data/model_data/MgFeSiO4_model.lnk"

conv_txt_to_lnk(input, output, 3.71)