import numpy as np

def isvalid_pdf(pdf):
    pdf = np.asarray(pdf, dtype=float)

    if pdf.ndim != 2 or pdf.shape[0] != 2:
        raise ValueError("pdf must be a 2 x N array.")

    supports = pdf[0]
    probabilities = pdf[1]

    if not np.all(np.isfinite(pdf)):
        raise ValueError("CDF values and support points must be finite.")

    if np.any(np.diff(supports) <= 0):
        raise ValueError(
            "Support points must be strictly increasing."
        )

    if np.any(probabilities < 0):
        raise ValueError("Probabilities must be non-negative.")

    if not np.isclose(np.sum(probabilities), 1.0):
        raise ValueError(
            f"Probabilities sum to {np.sum(probabilities)}, not 1."
        )
    return 1

def isvalid_cdf(cdf):
    tolerance = 1e-8    # tolerance for floatingpoint error
    cdf = np.asarray(cdf, dtype=float)

    if cdf.ndim != 2 or cdf.shape[0] != 2:
        raise ValueError("cdf must be a 2 x N array.")

    if cdf.shape[1] == 0:
        raise ValueError("cdf must contain at least one support point.")

    supports = cdf[0]
    probabilities = cdf[1]

    if not np.all(np.isfinite(cdf)):
        raise ValueError("CDF values and support points must be finite.")

    if np.any(np.diff(supports) <= 0):
        raise ValueError(
            "Support points must be strictly increasing."
        )

    if np.any(probabilities < 0 + tolerance) or np.any(probabilities > 1 + tolerance):
        raise ValueError(
            f"CDF values must lie in (0,1]. "
            f"values are {probabilities}"
        )

    if np.any(np.diff(probabilities) < 0):
        raise ValueError(
            "CDF values must be monotonically non-decreasing."
        )

    if not np.isclose(probabilities[-1], 1.0):
        raise ValueError(
            f"Invalid CDF: final cumulative probability is "
            f"{probabilities[-1]}, not 1."
        )
    return 1

def pdf2cdf(pdf):
    """
    Convert a discrete probability density function (pdf) to a cumulative distribution function (cdf).

    Parameters
    ----------
    pdf : 2 x N numpy.ndarray

    Returns
    -------
    cdf : 2 x N numpy.ndarray
    """
    pdf = np.asarray(pdf, dtype=float)
    isvalid_pdf(pdf)

    cdf = pdf.copy()
    cdf[1] = np.cumsum(cdf[1])

    return cdf


def cdf2pdf(cdf):
    """
    Convert a discrete cumulative distribution function (cdf) to a probability density function (pdf).

    Parameters
    ----------
    cdf : 2 x N numpy.ndarray

    Returns
    -------
    pdf : 2 x N numpy.ndarray
    """
    pdf = cdf.copy()

    pdf[1, 0] = cdf[1, 0]
    pdf[1, 1:] = np.diff(cdf[1])

    return pdf


def isdominant(cdf1, cdf2):
    """
    Returns 1 if cdf1 is strictly dominating cdf2.

    Parameters
    ----------
    cdf1: 2 x N numpy.ndarray
    cdf2: 2 x N numpy.ndarray
    """
    isvalid_cdf(cdf1)
    isvalid_cdf(cdf2)
    tolerance = 1e-8    #tolerance for floatingpoint error

    t1 = cdf1[0, :]
    p1 = cdf1[1, :]
    t2 = cdf2[0, :]
    p2 = cdf2[1, :]

    return 0
    # WIP
