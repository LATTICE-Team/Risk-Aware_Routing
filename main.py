import createGitter
from labelprop import labelprop
from maxcdf import maxcdf
import numpy as np
import networkx as nx
from distributions import pdf2cdf, cdf2pdf
from example_graphs import create_zwickau
import sys
from propagate_distributions import propagate_distributions
from tabulate import tabulate

G = createGitter.createGitterGraph(5, 5)

nodes = list(G.nodes(data=True))

# Ankunftsverteilungen vom Start aus propagieren
cdfs = propagate_distributions(
    graph=G,
    start="s",
    target="t",
)

# Ergebnis am Ziel auslesen
target_cdf = cdfs["t"]

if target_cdf is None:
    print("Das Ziel ist vom Start aus nicht erreichbar.")
else:
    target_cdf[1] = target_cdf[1]*100
    print(tabulate(
        target_cdf.T,
        headers=['Time','Probability'],
        tablefmt="grid",
        floatfmt=(".0f",".2f"),
        numalign="right",
    ))
