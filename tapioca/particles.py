"""
Read particles data as dataset
"""
import os
import numpy as np
import xarray as xr

from .utils import PARAMETERS_FILE, _read_parameters, _read_times


def read_mandyoc_particles(
    path,
    parameters_file=PARAMETERS_FILE,
    steps_slice=None,
    filetype="ascii",
):
    """
    Read the particle files generated by Mandyoc code and return the dataset with the
    position, id, layer and cumulative strain in time.

    Parameters
    ----------
    path : str
        Path to the folder where the Mandyoc output files are located.
    parameters_file : str (optional)
        Name of the parameter file. It is mus be located inside the ``path`` directory.
        Default to ``"param_1.5.3_2D.txt"``.
    steps_slice : tuple
    filetype : str
        Files format to be read. Default to ``"ascii"``.

    Returns
    -------
    dataset : :class: `xarray.Dataset`
        Dataset containing the position, id, layer and cumulative strain in time.
    """
    # Check valid filetype
    _check_filetype(filetype)
    # Get particle files
    particle_files = [f for f in os.listdir(path) if "step_" in f]
    # Determine the number of time steps using the parameter file
    parameters = _read_parameters(os.path.join(path, parameters_file))
    print_step, max_steps = parameters["print_step"], parameters["stepMAX"]
    steps, times = _read_times(path, print_step, max_steps, steps_slice)
    dimension = parameters["dimension"]
    # Get the particle id from the first step file
    particle_ids = _get_all_particles_ids(path, particle_files, filetype=filetype)
    # Initialize the dataset. The data variable have nans values
    dims = ("time", "particle_id")
    coords = {"time": times, "step": ("time", steps), "particle_id": particle_ids}
    shape = (len(times), particle_ids.size)
    if dimension == 2:
        data_vars = {
            "x": (dims, np.nan * np.ones(shape)),
            "z": (dims, np.nan * np.ones(shape)),
            "layer": (dims, np.nan * np.ones(shape)),
            "cumulative_strain": (dims, np.nan * np.ones(shape)),
        }
    elif dimension == 3:
        data_vars = {
            "x": (dims, np.nan * np.ones(shape)),
            "y": (dims, np.nan * np.ones(shape)),
            "z": (dims, np.nan * np.ones(shape)),
            "layer": (dims, np.nan * np.ones(shape)),
            "cumulative_strain": (dims, np.nan * np.ones(shape)),
        }
    ds = xr.Dataset(data_vars, coords=coords)
    # Fill the dataset
    for counter, (step, time) in enumerate(zip(steps, times)):
        # Determine the rank value on the first step and check it for following steps
        step_files = [f for f in particle_files if "step_{}-".format(step) in f]
        if counter == 0:
            n_rank = len(step_files)
        if len(step_files) != n_rank:
            raise ValueError(
                "Invalid number of ranks '{}' for step '{}'".format(
                    len(step_files), step
                )
            )
        # Read the files for the step and fill the dataset depending of the dimension
        for i in range(n_rank):
            basename = "step_{}-rank_new{}".format(step, i)
            if dimension == 2:
                # To open binary files
                if filetype == "binary":
                    file_name = basename + ".bin"
                    x, z, particle_id, layer, cumulative_strain = _load_binary_file(
                        path, file_name
                    )
                else:
                    x, z, particle_id, layer, cumulative_strain = np.loadtxt(
                        os.path.join(path, basename + ".txt"),
                        unpack=True,
                    )
                ds.x.sel(time=time).loc[dict(particle_id=particle_id)] = x
                ds.z.sel(time=time).loc[dict(particle_id=particle_id)] = z
                ds.layer.sel(time=time).loc[dict(particle_id=particle_id)] = layer
                ds.cumulative_strain.sel(time=time).loc[
                    dict(particle_id=particle_id)
                ] = cumulative_strain
            if dimension == 3:
                x, y, z, particle_id, layer, cumulative_strain = np.loadtxt(
                    os.path.join(path, basename + ".txt"),
                    unpack=True,
                )
                ds.x.sel(time=time).loc[dict(particle_id=particle_id)] = x
                ds.y.sel(time=time).loc[dict(particle_id=particle_id)] = y
                ds.z.sel(time=time).loc[dict(particle_id=particle_id)] = z
                ds.layer.sel(time=time).loc[dict(particle_id=particle_id)] = layer
                ds.cumulative_strain.sel(time=time).loc[
                    dict(particle_id=particle_id)
                ] = cumulative_strain
    return ds


def _check_filetype(filetype):
    """
    Checks if passed filetype is either ascii or binary
    """
    if filetype not in ("ascii", "binary"):
        raise ValueError(f"Invalid filetype '{filetype}'")


def _get_all_particles_ids(
    path,
    particle_files,
    filetype,
    first_step=0,
):
    """
    Function to get the particle id from the first step file
    """
    first_step_files = [f for f in particle_files if "step_{}".format(first_step) in f]
    particle_ids = []
    for i in range(len(first_step_files)):
        if filetype == "binary":
            _, _, id_f, _, _ = _load_binary_file(path, first_step_files[i])
        else:
            _, _, id_f, _, _ = np.loadtxt(
                os.path.join(path, first_step_files[i]), unpack=True
            )
        particle_ids.append(id_f)
    particle_ids = np.hstack(particle_ids)
    return particle_ids


def _load_binary_file(
    path,
    file_name,
):
    """"""
    sint = 4
    sfloat = 8
    # Determine the number of lines in the file
    n = np.fromfile(
        os.path.join(path, file_name),
        dtype=np.intc,
        count=1,
        sep="",
        offset=0,
    )[0]
    # Coordinates for each particle
    coordinates = np.fromfile(
        os.path.join(path, file_name),
        dtype=np.double,
        count=n * 2,
        sep="",
        offset=sint,
    )
    x, z = coordinates[::2], coordinates[1::2]
    # Particles ids
    offset = sint + sfloat * n * 2
    particle_id = np.fromfile(
        os.path.join(path, file_name),
        dtype=np.intc,
        count=n,
        sep="",
        offset=offset,
    )
    # Layer
    offset = sint + sfloat * n * 2 + sint * n
    layer = np.fromfile(
        os.path.join(path, file_name),
        dtype=np.intc,
        count=n,
        sep="",
        offset=offset,
    )
    # Cumulative strain
    offset = sint + sfloat * n * 2 + sint * n * 2
    cumulative_strain = np.fromfile(
        os.path.join(path, file_name),
        dtype=np.double,
        count=n,
        sep="",
        offset=offset,
    )
    return x, z, particle_id, layer, cumulative_strain
