"""
Utility functions for reading and writing data from/to files
"""
import os
import numpy as np

TIMES_BASENAME = "Tempo_"
PARAMETERS_FILE = "param_1.5.3_2D.txt"


def _read_parameters(parameters_file):
    """
    Read parameters file

    .. warning :

        The parameters file contains the length of the region along each axe. While
        creating the region, we are assuming that the z axe points upwards and therefore
        all values beneath the surface are negative, and the x and y axes are all
        positive within the region.

    Parameters
    ----------
    parameters_file : str
        Path to the location of the parameters file.

    Returns
    -------
    parameters : dict
        Dictionary containing the parameters of Mandyoc output files.
    """
    parameters = {}
    read_shape, read_max_coords = False, False
    with open(parameters_file, "r") as params_file:
        for line in params_file:
            # Skip blank lines
            if not line.strip():
                continue
            # Read number of coordinates per direction
            if not read_shape:
                parameters["shape"] = tuple(int(i) for i in line.split())
                read_shape = True
                # Determine the dimension of the data
                dimension = len(parameters["shape"])
                continue
            # Read maximum coordinates per direction
            if not read_max_coords:
                max_coords = tuple(float(i) for i in line.split())
                read_max_coords = True
                # Assert that the dimension matches the one read in shape
                assert len(max_coords) == dimension
                continue
            # Read more parameters
            key, value = line.split()
            if key in "print_step stepMAX".split():
                parameters[key] = int(value)
            elif key == "timeMAX":
                parameters[key] = float(value)
            else:
                parameters[key] = value
    # Add extrime values for the axis according to the dimension
    parameters["dimension"] = dimension
    if dimension == 2:
        x_max, z_max = max_coords[:]
        parameters["region"] = (0, x_max, -z_max, 0)
    elif dimension == 3:
        x_max, y_max, z_max = max_coords[:]
        parameters["region"] = (0, x_max, 0, y_max, -z_max, 0)
    else:
        raise ValueError("Invalid dimension: {}".format(dimension))
    # Add units
    parameters["coords_units"] = "m"
    parameters["times_units"] = "Ma"
    parameters["temperature_units"] = "C"
    parameters["density_units"] = "kg/m^3"
    parameters["heat_units"] = "W/m^3"
    parameters["viscosity_factor_units"] = "dimensionless"
    parameters["viscosity_units"] = "Pa s"
    parameters["strain_rate_units"] = "s^(-1)"
    parameters["pressure_units"] = "Pa"
    return parameters


def _read_times(path, print_step, max_steps, steps_slice):
    """
    Read the time files from the Mandyoc output

    Parameters
    ----------
    path : str
        Path to the folder where the Mandyoc output files are located.
    print_step : int
        Only steps multiple of ``print_step`` are saved by Mandyoc.
    max_steps : int
        Maximum number of steps. Mandyoc could break computation before the
        ``max_steps`` are run if the maximum time is reached. This quantity only
        bounds the number of time files.
    steps_slice : tuple
        Slice of steps (min_steps_slice, max_steps_slice). If it is None,
        min_step_slice = 0 and max_steps_slice = max_steps.

    Returns
    -------
    steps : numpy array
        Array containing the saved steps.
    times : numpy array
        Array containing the time of each step in Ma.
    """
    steps, times = [], []
    # Define the mininun and maximun step
    if steps_slice is not None:
        min_steps_slice, max_steps_slice = steps_slice[:]
    else:
        min_steps_slice, max_steps_slice = 0, max_steps
    for step in range(min_steps_slice, max_steps_slice + print_step, print_step):
        filename = os.path.join(path, "{}{}.txt".format(TIMES_BASENAME, step))
        if not os.path.isfile(filename):
            break
        time = np.loadtxt(filename, unpack=True, delimiter=":", usecols=(1))
        if time.shape == ():
            times.append(time)
        else:
            time = time[0]
            times.append(time)
        steps.append(step)

    # Transforms lists to arrays
    times = 1e-6 * np.array(times)  # convert time units into Ma
    steps = np.array(steps, dtype=int)
    return steps, times
