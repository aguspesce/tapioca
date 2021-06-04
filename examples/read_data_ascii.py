"""
Read the model data and plot the particle positions and the density.
The data format is ASCII.
"""
import os
import tapioca as tp
import matplotlib.pyplot as plt

# Get path to the model data directory
script_path = os.path.dirname(os.path.abspath(__file__))
# Path to ASCII data
files_path = os.path.join(script_path, "data", "vanKeken1997")

# Read the particles position
# slice = (100, 300)
ds_particle = tp.read_mandyoc_particles(
    files_path,
    # steps_slice=slice,
)
print("DATASET WITH THE PARTICLE DATA:", ds_particle)

# Read data model
ds_data = tp.read_mandyoc_data(
    files_path,
    # steps_slice=slice,
)
print("DATASET WITH ALL MODEL DATA:", ds_data)

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
