# ------------------------------------------------------------------------------------- #
# functions.py
#
# contains all functions relevant for the water ice project
#
#
#
# ------------------------------------------------------------------------------------- #

import numpy as np
import optool
import matplotlib.pyplot as plt
import os
from pathlib import Path

# ------------------------------------------------------------------------------------- #
# Function to combine the split nk data into one .lnk file for optool

def merge_lab_data(n_file, k_file, output_name, density):
    data_n = np.loadtxt(n_file)
    data_k = np.loadtxt(k_file)

    wavenumber = data_n[:, 0]
    n_vals = data_n[:, 1]
    k_vals = data_k[:, 1]

    k_vals[k_vals < 0] = 0.0
    wavelength = 10000.0 / wavenumber

    combined = np.column_stack((wavelength, n_vals, k_vals))
    combined = combined[combined[:, 0].argsort()]

    num_rows = len(combined)
    
    with open(output_name, 'w') as f:  
        f.write(f"# Material: {output_name}\n")     
        f.write(f"{num_rows} {density:.3f}\n")      # row number and density
    
        for row in combined:
            f.write(f"{row[0]:.12f}  {row[1]:.12f}  {row[2]:.12f}\n")

    print(f"Created: {output_name} with density {density}")

# ------------------------------------------------------------------------------------- #
# Function to convert .txt input files into nk-data files

def conv_txt_to_lnk(input_file, output_file, density):
    
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".lnk"

    try:
        data = np.loadtxt(input_file)
        
        if data.shape[1] != 3:
            raise ValueError(f"Expected 3 columns (Wavelength, n, k), but found {data.shape[1]}")

        num_rows = data.shape[0]

        with open(output_file, 'w') as f:

            f.write(f"{num_rows}\n")
            f.write(f"{density}\n")
            
            for row in data:
                f.write(f"{row[0]:.6f}\t{row[1]:.6f}\t{row[2]:.6f}\n")
        
        print(f"Successfully converted: {output_file} ({num_rows} points)")

    except Exception as e:
        print(f"Error processing {input_file}: {e}")


# ------------------------------------------------------------------------------------- #
# Plotting function for k_abs and k_scat in two separate windows

def plot_opacity_components(file_path, label, filename_out):
    plt.figure(1)

    try:
        data = np.loadtxt(file_path, skiprows=31)

        wav = data[:, 0]
        k_abs = data[:, 1]
        k_sca = data[:, 2]

        # kappa_abs
        plt.figure(1)
        plt.plot(wav, k_abs,
                 label=r"{} ($\kappa_{{abs}}$)".format(label))
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Wavelength ($\mu m$)')
        plt.ylabel(r'$\kappa_{\mathrm{abs}}$ ($cm^2/g$)')
        #plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend()

        # kappa_scat
        plt.figure(2)
        plt.plot(wav, k_sca,
                 label=r"{} ($\kappa_{{scat}}$)".format(label))
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Wavelength ($\mu m$)')
        plt.ylabel(r'$\kappa_{\mathrm{scat}}$ ($cm^2/g$)')
        #plt.grid(True, which="both", ls="-", alpha=0.3)
        plt.legend()

        plt.figure(1)
        plt.savefig(f"/home/jschneider/Projects/dust_ice/plots/{filename_out}_kappa_abs.pdf", bbox_inches="tight")

        plt.figure(2)
        plt.savefig(f"/home/jschneider/Projects/dust_ice/plots/{filename_out}_kappa_scat.pdf", bbox_inches="tight")

    except Exception as e:
        print(f"An error occurred: {e}")


# ------------------------------------------------------------------------------------- #
# Plotting function for silicate+water mix


def plot_compare_opacity_components(input_dir):

    labels = {
        "rho_2.71_sil_0.729730_waterCore_0.270270_waterMantle_0.000000_ratio_2.7to1": "MgSiO$_3$ + H$_2$O 2.7",
        "rho_2.71_sil_0.882353_waterCore_0.117647_waterMantle_0.000000_ratio_7.5to1": "MgSiO$_3$ + H$_2$O 7.5",
        "rho_3.71_sil_0.729730_waterCore_0.270270_waterMantle_0.000000_ratio_2.7to1": "MgFeSiO$_4$ + H$_2$O 2.7",
        "rho_3.71_sil_0.882353_waterCore_0.117647_waterMantle_0.000000_ratio_7.5to1": "MgFeSiO$_4$ + H$_2$O 7.5",
    }

    plt.figure(1)
    plt.figure(2)

    for file_path in sorted(input_dir.glob("**/dustkappa.dat")):

        data = np.loadtxt(file_path, skiprows=32)

        wav = data[:, 0]
        k_abs = data[:, 1]
        k_sca = data[:, 2]

        label = labels[file_path.parent.name]

        plt.figure(1)
        plt.plot(wav, k_abs, label=label)

        plt.figure(2)
        plt.plot(wav, k_sca, label=label)

    plt.figure(1)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Wavelength ($\\mu$m)")
    plt.ylabel(r"$\kappa_{\mathrm{abs}}$ ($cm^2/g$)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("/home/jschneider/Projects/dust_ice/plots/kappa_abs_mixed.pdf", bbox_inches="tight")

    plt.figure(2)
    plt.yscale("log")
    plt.xscale("log")
    plt.xlabel("Wavelength ($\\mu$m)")
    plt.ylabel(r"$\kappa_{\mathrm{scat}}$ ($cm^2/g$)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("/home/jschneider/Projects/dust_ice/plots/kappa_scat_mixed.pdf", bbox_inches="tight")