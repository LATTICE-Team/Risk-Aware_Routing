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

    # Node reached for the first time
    if cdf1[0,0] == 100000:
        mcdf = cdf2.copy()
        mcdflabel=v_cdflabel
    else:
        mcdf = np.hstack((cdf1, cdf2))
        mcdflabel=w_cdflabel+v_cdflabel

    # Sort according to first row
    sort_idx = np.argsort(mcdf[0, :])
    mcdf = mcdf[:, sort_idx]
    mcdflabel=[mcdflabel[i] for i in sort_idx]

    # Merge double entries in first row (max in second row)
    i = 0
    while i < mcdf.shape[1] - 1:
        if mcdf[0, i] == mcdf[0, i+1]:

            k,mcdf[1, i] = max(enumerate([mcdf[1, i],mcdf[1, i+1]]),key=lambda x: x[1])
            mcdf = np.delete(mcdf, i+1, axis=1)
            mcdflabel[i]=mcdflabel[k]
            mcdflabel.pop(i+1)
        else:
            i += 1

    # Delete columns where second row decreases (monotonically increasing)
    j = 0
    tol = 1e-10
    while j < mcdf.shape[1] - 1:
        if mcdf[1, j] >= mcdf[1, j+1] - tol:
            mcdf = np.delete(mcdf, j+1, axis=1)
            mcdflabel.pop(j+1)
        else:
            j += 1

    # Find first column where cdf1 and mcdf differ
    imax = min(cdf1.shape[1], mcdf.shape[1])
    i = 0
    while i < imax and np.allclose(mcdf[:, i], cdf1[:, i], atol=1e-12):
        i += 1


    return mcdf

if __name__ == '__main__':
    cdf1 = np.array([[3, 4, 6], [1/2, 5/6, 1]])
    cdf2 = np.array([[1000000], [1]])
    t0old = 4
    v='s'
    w='v_1_1'
    mcdf, t0 = maxcdf(cdf1, cdf2, t0old,v,w)
    print("mcdf =\n", mcdf)
    print("t0 =", t0)
