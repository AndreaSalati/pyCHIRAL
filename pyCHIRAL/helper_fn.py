import numpy as np

ccg = np.array(
    [
        "Arntl",
        "Npas2",
        "Cry1",
        "Cry2",
        "Per1",
        "Per2",
        "Nr1d1",
        "Nr1d2",
        "Tef",
        "Dbp",
        "Ciart",
        "Per3",
        "Bmal1",
    ]
)


def ind2(large_list, small_list, verbose=False):
    if isinstance(small_list, str):
        small_list = [small_list]
    large_array = np.array(large_list)
    small_array = np.array(small_list)
    indices = []

    element_to_index = {element: idx for idx, element in enumerate(large_array)}

    for element in small_array:
        if element in element_to_index:
            indices.append(element_to_index[element])
        else:
            # Optionally handle or notify when an element is not found
            if verbose:
                print(f"Warning: '{element}' not found in the large list.")

    return indices


def process_expression_data(
    E, clockgenes=None, ccg=None, layer=None, standardize=False, mean_centre_E=False
):
    """
    Processes the expression data based on the provided parameters.

    Parameters:
    - E: The expression data object (assumed to have X and layers attributes).
    - clockgenes: List of clock genes to select. If None, uses ccg.
    - ccg: Default list of clock genes if clockgenes is None.
    - layer: Specific layer of expression data to use.
    - standardize: Whether to standardize the expression data.
    - mean_centre_E: Whether to mean center the expression data.

    Returns:
    - E: Processed expression data.
    - clock_coord: Indices of the selected clock genes.
    - N: Number of samples.
    - Ng: Number of genes.
    """

    if clockgenes is None:
        clockgenes = ccg

    E_full = E.copy()
    genes = E_full.var_names

    if layer is None:
        E = E.X
    else:
        E = E.layers[layer]

    # Clock gene selection
    clock_coord = ind2(genes, clockgenes)
    E = E[:, clock_coord]

    # Standardize the matrix if needed
    if standardize:
        E = E / np.std(E, axis=0, keepdims=True)

    # Mean center the expression data if needed
    if mean_centre_E:
        E = E - E.mean(axis=0, keepdims=True)

    N, Ng = E.shape

    return E, E_full, clock_coord, N, Ng


def circular_deviation(x, y, period=2 * np.pi):
    """
    It computes the circular absolute deviation between two vectors x and y
    Inputs:
    x: phase array
    y: phase array
    period: period of the circular variable
    """

    x, y = x % period, y % period
    v1 = np.abs(x - y)
    v2 = (period - v1) % period

    return np.minimum(v1, v2)


def optimal_shift(p, p0, n_s=200, return_mad=True):
    """
    Aligns two sequences defined on the unit circle, taking care of the periodicity
    and the flipping symmetry of the circle.
    It uses the median absolute deviation (MAD) as a measure of the distance between the two sequences.
    """
    Nc = p.shape[0]
    shifts = np.linspace(0, 2 * np.pi, n_s)
    # creating a matrix of all possible shifts
    theta_cs = (p.reshape(Nc, 1) - shifts.reshape(1, n_s)) % (2 * np.pi)
    theta_cs_neg = (-p.reshape(Nc, 1) - shifts.reshape(1, n_s)) % (2 * np.pi)

    # for each shift, computing the circular deviation, using apply_along_axis
    delta_cs = circular_deviation(p0[:, None], theta_cs)
    delta_cs_neg = circular_deviation(p0[:, None], theta_cs_neg)

    # computing the median absolute deviation for all shifts
    v = np.median(delta_cs, axis=0)
    v_neg = np.median(delta_cs_neg, axis=0)
    # selecting the best shift
    best_shift_ind = np.argmin(v)
    best_shift_ind_neg = np.argmin(v_neg)
    mad, mad_neg = v[best_shift_ind], v_neg[best_shift_ind_neg]

    # selecting which direction is the best
    if mad < mad_neg:
        phi_aligned = theta_cs[:, best_shift_ind]
    else:
        phi_aligned = theta_cs_neg[:, best_shift_ind_neg]

    if return_mad:
        return phi_aligned, mad
    else:
        return phi_aligned
