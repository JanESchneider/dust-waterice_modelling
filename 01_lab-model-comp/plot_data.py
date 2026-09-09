# ------------------------------------------------------------------------------------- #
# plot_data.py  -> more or less a testing ground for now
#
# Plotting routine, might be expanded and/or altered if necessary... 
# To do: auskommentierte Funktionen sortieren/entfernen
#  
# ------------------------------------------------------------------------------------- #

import sys
sys.path.append("/home/jschneider/Proj_WaterIce/00_global")
from functions import *

'''file_data_8 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.888889_waterCore_0.111111_waterMantle_0.000000_ratio_8.0to1/dustkappa.dat"
file_data_7 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.882353_waterCore_0.000000_waterMantle_0.117647_ratio_7.5to1/dustkappa.dat"
file_data_5 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.833333_waterCore_0.166667_waterMantle_0.000000_ratio_5.0to1/dustkappa.dat"
file_data_2 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.666667_waterCore_0.333333_waterMantle_0.000000_ratio_2.0to1/dustkappa.dat"
file_data_lab = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_labdata/dustkappa.dat"

file_data_7_2 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.882353_waterCore_0.000000_waterMantle_0.117647_ratio_7.5to1/dustkappa.dat"
file_data_7_3 = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models/rho_3.71_SIL_0.882353_waterCore_0.117647_waterMantle_0.000000_ratio_7.5to1/dustkappa.dat"

filedata_arr = np.array([file_data_2, file_data_5, file_data_7, file_data_8, file_data_lab])
labels = np.array(["model ratio 2:1", "model ratio 5:1", "model ratio 7.5:1", "model ratio 8:1", "lab"])

for path, tag in zip(filedata_arr, labels):
    # Use fr for the f-string + raw string to handle the LaTeX $ subscripts correctly
    plot_opacity_components(path, label=fr"MgFeSiO$_4$ ({tag})")


filedata_arr_new = np.array([file_data_7_2, file_data_7_3, file_data_lab])
labels_new = np.array(["model ratio 7.5:1", "model ratio 7.5:1 pure water core", "lab"])

for path, tag in zip(filedata_arr_new, labels_new):
    # Use fr for the f-string + raw string to handle the LaTeX $ subscripts correctly
    plot_opacity_components(path, label=fr"MgFeSiO$_4$ ({tag})")
plt.show()'''


def plot_model_comparison(model_root, lab_file_path, normalize=True):
    """
    Compares all dust models in a directory against a laboratory reference.
    
    Parameters:
    - model_root: Directory containing folders with 'dustkappa.dat'
    - lab_file_path: Path to the processed lab 'dustkappa.dat'
    - normalize: If True, scales all plots to have the same maximum (better for shape comparison).
    """
    plt.figure(figsize=(12, 7))

    # 1. Load and Plot Lab Data (The "Truth")
    try:
        lab_data = np.loadtxt(lab_file_path, skiprows=26)
        lab_wav = lab_data[:, 0]
        lab_kappa = lab_data[:, 1] # Extinction
        
        norm_factor = np.max(lab_kappa) if normalize else 1.0
        
        plt.plot(lab_wav, lab_kappa / norm_factor, 
                 label="LAB REFERENCE", color='black', linewidth=3, zorder=10)
    except Exception as e:
        print(f"Error loading lab file: {e}")

    # 2. Find and Plot all Model Data
    root = Path(model_root)
    model_files = sorted(list(root.glob("**/dustkappa.dat")))
    
    # Using a colormap to distinguish many lines
    colors = plt.cm.RdYlBu_r(np.linspace(0, 1, len(model_files)))

    for i, file_path in enumerate(model_files):
        # Extract folder name to identify model parameters
        folder_name = file_path.parent.name
        
        # Clean up the label: e.g., Extracting ratio and mantle fraction
        # folder_name looks like: rho_3.0_SIL_0.75..._ratio_3.0to1
        parts = folder_name.split('_')
        label = f"Ratio {parts[-1].replace('to1', ':1')} (Mantle {parts[6]})"

        try:
            data = np.loadtxt(file_path, skiprows=32)
            wav = data[:, 0]
            kappa = data[:, 1]
            
            norm_factor = np.max(kappa) if normalize else 1.0
            
            plt.plot(wav, kappa / norm_factor, 
                     label=label, color=colors[i], alpha=0.6, linewidth=1)
            
        except Exception as e:
            print(f"Skipping {folder_name}: {e}")

    # Plot Formatting
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Wavelength ($\mu m$)', fontsize=12)
    plt.ylabel('Normalized Opacity $\kappa_{abs}$' if normalize else 'Opacity $\kappa_{abs}$ ($cm^2/g$)', fontsize=12)
    plt.title('Dust Model Comparison: Models vs. Lab Data')
    plt.ylim(3e-03, 2e0)
    
    # Move legend outside
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='x-small', ncol=2)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.tight_layout()
    plt.show()

# --- Example Call ---
MODEL_DIR = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_models"
LAB_DATA = "/home/jschneider/Proj_WaterIce/01_lab-model-comp/data_out/dust_labdata/dustkappa.dat"
plot_model_comparison(MODEL_DIR, LAB_DATA, normalize=True)