import numpy as np
from distributions import isvalid_cdf

def maxcdf(cdf1, cdf2):
    """
    Merges two discrete CDFs by preserving the maximal value of both CDFs for each probability.

    Parameters
    ----------
    cdf1 : 2 x N np.ndarray

    cdf2 : 2 x M np.ndarray

    Returns
    -------
    mcdf : np.ndarray merged CDF
    """
    isvalid_cdf(cdf1)
    isvalid_cdf(cdf2)

    # beide CDFs aneinandderhängen und nach Zeit sortieren
    mcdf = np.append(cdf1,cdf2,axis=1)
    sort_idx = np.argsort(mcdf[0, :])
    mcdf = mcdf[:, sort_idx]

    for i in range(mcdf.shape[1]-1):
        mcdf[1, i+1] = max(mcdf[1, i], mcdf[1, i+1])

    for i in range(mcdf.shape[1]-1, 0, -1):
        if np.isclose(mcdf[1, i], mcdf[1, i-1]):
            mcdf = np.delete(mcdf, i, axis=1)

    for i in range(mcdf.shape[1]-1):
        if np.isclose(mcdf[0, i], mcdf[0, i+1]):
            mcdf = np.delete(mcdf, i, axis=1)

    return mcdf

if __name__ == '__main__':
    cdf1 = np.array([[3, 4, 6, 7, 8], [1/2, 0.7, 0.75, 0.9, 1]])
    cdf2 = np.array([[2, 5, 6, 7], [0.2, 0.6, 0.8, 1]])
    mcdf = maxcdf(cdf1, cdf2)
    print("mcdf =\n", mcdf)
