"""
Read the particle positions and the density data from 2D model.
The data format is binary.
"""
import os
import tapioca as tp
import matplotlib.pyplot as plt

# Get path to the MANDYOC output directory
script_path = os.path.dirname(os.path.abspath(__file__))

# Path to binary data
files_path = os.path.join(script_path, "data", "vanKeken1997-bin")

# Read the particles position
# slice = (20, 80)
ds_particle = tp.read_mandyoc_particles(
    files_path,
    filetype="binary",
    # steps_slice=slice,
)
print(ds_particle)

# Read density and temperature data
ds_data = tp.read_mandyoc_data(
    files_path,
    datasets=["density", "temperature"],
    filetype="binary",
    # steps_slice=slice,
)
print(ds_data)

# Plot the density and the particle positions
for time in ds_data.time:
    fig, ax = plt.subplots()
    ds_data.density.sel(time=time).plot(
        x="x",
        y="z",
        ax=ax,
        vmin=ds_data.density.min(),
        vmax=ds_data.density.max(),
    )
    ax.scatter(
        ds_particle.x.sel(time=time),
        ds_particle.z.sel(time=time),
        s=0.5,
        color="black",
        alpha=0.2,
    )
    ax.ticklabel_format(axis="both", style="sci", scilimits=(0, 0))
    ax.set_aspect("equal")
    plt.show()