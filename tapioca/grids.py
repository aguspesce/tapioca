"""
Read and write data structured in regular grids
"""
import os
import numpy as np
import xarray as xr
import pandas as pd
import petsc4py
from petsc4py import PETSc

from .utils import _read_parameters, _read_times, PARAMETERS_FILE

BASENAMES = {
    "temperature": "temperature",
    "density": "density",
    "radiogenic_heat": "heat",
    "viscosity": "viscosity",
    "strain": "strain",
    "strain_rate": "strain_rate",
    "pressure": "pressure",
    "velocity": "velocity",
}
DATASETS = (
    "temperature",
    "density",
    "radiogenic_heat",
    "viscosity",
    "strain",
    "strain_rate",
    "pressure",
    "velocity",
)
# Define which datasets are scalars measured on the nodes of the grid, e.g.
# velocity is not a scalar.
SCALARS_ON_NODES = DATASETS[:6]


def read_mandyoc_data(
    path,
    parameters_file=PARAMETERS_FILE,
    datasets=DATASETS,
    steps_slice=None,
    filetype="ascii",
):
    """
    Read the files  generate by Mandyoc code

    Parameters
    ----------
    path : str
        Path to the folder where the Mandyoc files are located.
    parameters_file : str (optional)
        Name of the parameters file. It must be located inside the ``path``
        directory.
        Default to ``"param.txt"``.
    datasets : tuple (optional)
        Tuple containing the datasets that wants to be loaded.
        The available datasets are:
            - ``temperature``
            - ``density"``
            - ``radiogenic_heat``
            - ``strain``
            - ``strain_rate``
            - ``pressure``
            - ``viscosity``
            - ``velocity``
        By default, every dataset will be read.
    steps_slice : tuple
        Slice of steps to generate the step array. If it is None, it is taken
        from the folder where the Mandyoc files are located.
    filetype : str
        Files format to be read. Default to ``"ascii"``.

    Returns
    -------
    dataset :  :class:`xarray.Dataset`
        Dataset containing data generated by Mandyoc code.
    """
    # Check valid filetype
    _check_filetype(filetype)
    # Read parameters
    parameters = _read_parameters(os.path.join(path, parameters_file))
    # Build coordinates
    shape = parameters["shape"]
    coordinates = _build_coordinates(region=parameters["region"], shape=shape)
    # Get array of times and steps
    steps, times = _read_times(
        path,
        parameters["print_step"],
        parameters["step_max"],
        steps_slice,
    )
    # Create the coordinates dictionary containing the coordinates of the nodes
    # and the time and step arrays. Then create data_vars dictionary containing
    # the desired scalars datasets.
    coords = {"time": times, "step": ("time", steps)}
    dims = ("time", "x", "z")
    coords["x"], coords["z"] = coordinates[:]

    # Create a dictionary containing the scalar data (no velocity)
    data_vars = {
        scalar: (
            dims,
            _read_scalars(path, shape, steps, quantity=scalar, filetype=filetype),
        )
        for scalar in datasets
        if scalar in SCALARS_ON_NODES
    }

    # Read velocity if needed
    if "velocity" in datasets:
        velocities = _read_velocity(path, shape, steps, filetype)
        data_vars["velocity_x"] = (dims, velocities[0])
        data_vars["velocity_z"] = (dims, velocities[1])

    return xr.Dataset(data_vars, coords=coords, attrs=parameters)


def _check_filetype(filetype):
    """
    Checks if passed filetype is either ascii or binary
    """
    if filetype not in ("ascii", "binary"):
        raise ValueError(f"Invalid filetype '{filetype}'")


def _build_coordinates(region, shape):
    """
    Create grid coordinates

    Parameters
    ----------
    region : tuple
        Boundary coordinates for each direction.
        If reading 2D data, they must be passed in the following order:
        ``x_min``, ``x_max``, ``z_min``, ``z_max``.
        All coordinates should be in meters.
    shape : tuple
        Number of points for each direction.
        If reading 2D data, they must be passed in the following
        order: ``nx``, ``nz``.

    Returns
    -------
    coordinates : tuple
        Tuple containing grid coordinates in the following order:
        ``x``, ``z`` if 2D.
        All coordinates are in meters.
    """
    # Get number of dimensions
    x_min, x_max, z_min, z_max = region[:]
    nx, nz = shape[:]
    x = np.linspace(x_min, x_max, nx)
    z = np.linspace(z_min, z_max, nz)
    return x, z


def _read_scalars(path, shape, steps, quantity, filetype):
    """
    Read Mandyoc scalar data

    Read ``temperature``, ``density``, ``radiogenic_heat``, ``viscosity``,
    ``strain``, ``strain_rate`` and ``pressure``.

    Parameters
    ----------
    path : str
        Path to the folder where the Mandyoc files are located.
    shape: tuple
        Shape of the expected grid.
    steps : array
        Array containing the saved steps.
    quantity : str
        Type of scalar data to be read.

    Returns
    -------
    data: np.array
        Array containing the Mandyoc scalar data.
    """
    data = []
    for step in steps:
        filename = "{}_{}".format(BASENAMES[quantity], step)
        # To open outpus binary files
        if filetype == "binary":
            load = PETSc.Viewer().createBinary(
                os.path.join(path, filename + ".bin"), "r"
            )
            data_step = PETSc.Vec().load(load).getArray()
            del load
        else:
            data_step = np.loadtxt(
                os.path.join(path, filename + ".txt"),
                unpack=True,
                comments="P",
                skiprows=2,
            )
        # Convert very small numbers to zero
        data_step[np.abs(data_step) < 1.0e-200] = 0
        # Reshape data_step
        data_step = data_step.reshape(shape, order="F")
        # Append data_step to data
        data.append(data_step)
    data = np.array(data)
    return data


def _read_velocity(path, shape, steps, filetype):
    """
    Read velocity data generated by Mandyoc code

    Parameters
    ----------
    path : str
        Path to the folder where the Mandyoc output files are located.
    shape: tuple
        Shape of the expected grid.
    steps : array
        Array containing the saved steps.

    Returns
    -------
    data: tuple of arrays
        Tuple containing the components of the velocity vector.
    """
    # Determine the dimension of the velocity data
    dimension = len(shape)
    velocity_x, velocity_z = [], []
    for step in steps:
        filename = "{}_{}".format(BASENAMES["velocity"], step)
        # To open outpus binary files
        if filetype == "binary":
            load = PETSc.Viewer().createBinary(
                os.path.join(path, filename + ".bin"), "r"
            )
            velocity = PETSc.Vec().load(load).getArray()
            del load
        else:
            velocity = np.loadtxt(
                os.path.join(path, filename + ".txt"), comments="P", skiprows=2
            )
        # Convert very small numbers to zero
        velocity[np.abs(velocity) < 1.0e-200] = 0
        # Separate velocity into their three components
        velocity_x.append(velocity[0::dimension].reshape(shape, order="F"))
        velocity_z.append(velocity[1::dimension].reshape(shape, order="F"))
    # Transform the velocity_* lists to arrays
    velocity_x = np.array(velocity_x)
    velocity_z = np.array(velocity_z)
    return (velocity_x, velocity_z)
