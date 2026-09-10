# ------------------------------------------------------------------------------------- #
# plot_data.py  -> more or less a testing ground for now
#
# Plotting routine, might be expanded and/or altered if necessary... 
# To do: auskommentierte Funktionen sortieren/entfernen
#  
#
# ------------------------------------------------------------------------------------- #

import sys
sys.path.append("/home/jschneider/Projects/dust_ice/global_code/")
from functions import *
from pathlib import Path

file_data_lab = "/home/jschneider/Projects/dust_ice/data/dust_labdata/dustkappa.dat"

#plot_compare_opacity_components(input_dir=Path("/home/jschneider/Projects/dust_ice/data/dust_models"))

plot_opacity_components(file_data_lab, label=fr"MgSiO$_3$", filename_out="MgSiO3")
plt.show()


# txt to lnk conversion
#conv_txt_to_lnk(input_file="/home/jschneider/Projects/dust_ice/data/data_jena-db_MgSiO3.txt", output_file="/home/jschneider/Projects/dust_ice/data/data_jena-db_MgSiO3.lnk", density=2.71)
