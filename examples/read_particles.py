"""
Read the particle positions from 2D data for an specified period of time
"""
import os
import tapioca as tp
import matplotlib.pyplot as plt

# Get path to the MANDYOC output directory
script_path = os.path.dirname(os.path.abspath(__file__))
mandyoc_output_path = os.path.join(script_path, "data", "data_2d")

# Read the particles position
slice = (1500, 4000)
ds_particle = tp.read_mandyoc_particles(
    mandyoc_output_path,
    steps_slice=slice,
)
print(ds_particle)

# Read temperature data
ds_data = tp.read_mandyoc_data(
    mandyoc_output_path,
    datasets=["temperature", "viscosity"],
    steps_slice=slice,
)

for time in ds_data.time:
    fig, ax = plt.subplots()
    ds_data.temperature.sel(time=time).plot(
        x="x",
        y="z",
        ax=ax,
        vmin=ds_data.temperature.min(),
        vmax=ds_data.temperature.max(),
    )
    ax.scatter(
        ds_particle.x.sel(time=time),
        ds_particle.z.sel(time=time),
        s=0.1,
        color="black",
        alpha=0.2,
    )
    ax.ticklabel_format(axis="both", style="sci", scilimits=(0, 0))
    ax.set_aspect("equal")
    plt.show()
