"""
Read Mandyoc output files and seve them as a xarray.dataset
"""
import os
import matplotlib.pyplot as plt
import tapioca as tp

# Get path to the Mandyoc output directory
script_path = os.path.dirname(os.path.abspath(__file__))
mandyoc_files_path = os.path.join(script_path, "data", "data_2d")

# Read the MANDYOC output files
dataset = tp.read_mandyoc_data(
    mandyoc_files_path, datasets=["temperature", "viscosity"]
)
print(dataset)

# Plot the temperature
for time in dataset.time:
    fig, ax = plt.subplots()
    dataset.temperature.sel(time=time).plot(
        x="x",
        y="z",
        ax=ax,
        vmin=dataset.temperature.min(),
        vmax=dataset.temperature.max(),
    )
    ax.ticklabel_format(axis="both", style="sci", scilimits=(0, 0))
    ax.set_aspect("equal")
    plt.show()
