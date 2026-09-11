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

file_data_lab = "/home/jschneider/Projects/dust_ice/data/dust_potapov/MgFeSiO4_H2O_150K_4_5/dustkappa.dat"

#plot_compare_opacity_components(input_dir=Path("/home/jschneider/Projects/dust_ice/data/dust_models"), silicate_density=2.71)
plot_opacity_components(file_data_lab, label=fr"MgFeSiO$_4$ + H$_2$O 4.5", filename_out="MgFeSiO4_potapov")

'''
def plot_comparison():
    input1 = "/home/jschneider/Projects/dust_ice/data/dust_potapov/MgSiO3_H2O_150K_2_7/dustkappa.dat"
    input2 = "/home/jschneider/Projects/dust_ice/data/dust_potapov/MgSiO3_H2O_150K_7_5/dustkappa.dat"

    labels = [
        "MgSiO$_3$ + H$_2$O 2.7 Potapov",
        "MgSiO$_3$ + H$_2$O 7.5 Potapov"
    ]

    input_arr = [input1, input2]

    # -------------------------------------------------------------------------
    # Read data
    # -------------------------------------------------------------------------

    plt.figure(1)

    for i, file_path in enumerate(input_arr):

        data = np.loadtxt(file_path, skiprows=32)

        wav = data[:, 0]
        k_abs = data[:, 1]

        plt.plot(
            wav,
            k_abs,
            label=labels[i]
        )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Wavelength ($\\mu$m)")
    plt.ylabel(r"$\kappa_{\mathrm{abs}}$ ($cm^2/g$)")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "/home/jschneider/Projects/dust_ice/plots/MgSiO3_potapov_kappa_abs_mixed_log.pdf",
        bbox_inches="tight"
    )


    # -------------------------------------------------------------------------
    # Scattering
    # -------------------------------------------------------------------------

    plt.figure(2)

    for i, file_path in enumerate(input_arr):

        data = np.loadtxt(file_path, skiprows=32)

        wav = data[:, 0]
        k_sca = data[:, 2]

        plt.plot(
            wav,
            k_sca,
            label=labels[i]
        )

    plt.xscale("log")
    plt.yscale('log')
    plt.xlabel("Wavelength ($\\mu$m)")
    plt.ylabel(r"$\kappa_{\mathrm{scat}}$ ($cm^2/g$)")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "/home/jschneider/Projects/dust_ice/plots/MgSiO3_potapov_kappa_scat_mixed_log.pdf",
        bbox_inches="tight"
    )

plot_comparison()
'''
plt.show()
