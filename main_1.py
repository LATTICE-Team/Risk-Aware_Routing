import createGitter
from labelprop import labelprop
from maxcdf import maxcdf
import numpy as np
import networkx as nx
from distributions import pdf2cdf, cdf2pdf
from example_graphs import create_zwickau
import sys
from propagate_distributions import propagate_distributions

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
    print("Zeitpunkte:")
    print(target_cdf[0])

    print("Kumulierte Ankunftswahrscheinlichkeiten:")
    print(target_cdf[1])

# allpaths = nx.all_simple_paths(G, source='s', target='t')
# for path in allpaths:
    # while node < len(path):
    #     prelabel = G.nodes[path[node]]['ArrCDF']
    #     transit_pdf = G.edges[path[node],path[node+1]]['TransittimesPDF']
    #     nextlabel = labelprop(cdf2pdf(prelabel),np.array(transit_pdf))
# print(len(list(allpaths)))
