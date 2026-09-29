import createGitter
from labelprop import labelprop
from maxcdf import maxcdf
import numpy as np
import networkx as nx
from distributions import pdf2cdf, cdf2pdf
from example_graphs import create_zwickau
import sys

x = 5
y = 5
G = createGitter.createGitterGraph(x,y)

nodes = list(G.nodes(data=True))

T0_list = [attr['T0'] for n, attr in G.nodes(data=True)]    #Liste von "T0" aller Knoten
minT0 = min(T0_list)                                            #kleinstes "T0"
v = [n for n, attr in G.nodes(data=True)if attr['T0']==minT0] #Knoten mit kleinstem "T0"
target = 't'  #Name vom Zielknoten

allpaths = nx.all_simple_paths(G, source='s', target='t')
# for path in allpaths:
    # while node < len(path):
    #     prelabel = G.nodes[path[node]]['ArrCDF']
    #     transit_pdf = G.edges[path[node],path[node+1]]['TransittimesPDF']
    #     nextlabel = labelprop(cdf2pdf(prelabel),np.array(transit_pdf))
print(len(list(allpaths)))


itercnt = 0
while minT0 < G.nodes[target]['ArrCDF'][0][-1]:
    itercnt +=1
    edges = list(G.edges(v))
    edges.sort()
    for v,w in edges:
        start_cdf = G.nodes[v]['ArrCDF']  #Cdf vom aktuellen Knoten
        target_cdf = G.nodes[w]['ArrCDF'] #Cdf am Nachfolgeknoten
        T0 = G.nodes[w]['T0']

        transit_pdf = G.edges[v,w]['TransittimesPDF'] # Pdf für Fahrtzeit zwischen v und w
        v_Pfad = G.nodes[v]['Pfad']
        w_Pfad = G.nodes[w]['Pfad']

        templabel = labelprop(cdf2pdf(np.array(start_cdf)),np.array(transit_pdf)) # Faltung von start_pdf mit transit_pdf
        CDFtarget = maxcdf(np.array(target_cdf),pdf2cdf(templabel)) # Werte nehmen mit maximler Wahrscheinlichkeit

        G.nodes[w]['ArrCDF'] = CDFtarget # ändern des zielknoten
        G.nodes[w]['T0'] = T0 # neuer start wert

    G.nodes[v]['T0'] = 100000 # inf setzen von alten startknotnen damit dieser nicht wieder genommen wird
    T0_list = [attr['T0'] for n, attr in G.nodes(data=True)]
    minT0 = min(T0_list)
    v = [n for n, attr in G.nodes(data=True)if attr['T0']==minT0]
    v = v[0]

print('Iterations:',itercnt)

final = G.nodes[target]['ArrCDF']
