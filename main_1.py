import createGitter
import labelprop
import maxcdf
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import zeichene_Graph
from distributions import pdf2cdf, cdf2pdf

x=3
y=3
G=createGitter.createGraph2(x,y)
print(G.nodes(data=True))
print(G.edges(data=True))

nodes = list(G.nodes(data=True))

m=[attr['T0'] for n, attr in G.nodes(data=True)]    #Liste von "T0" aller Knoten
m=min(m)
v=[n for n, attr in G.nodes(data=True)if attr['T0']==m] #Knoten mit kleinstem "T0"
target='t'  #Name vom Zielknoten

# Dijkstra für Worst-Case und Best-Case
for u, w, attr in G.edges(data=True):
    attr['maxTranTime'] = [max(attr['TransittimesPDF'][0])]
    attr['minTranTime'] = [min(attr['TransittimesPDF'][0])]

dmax,pmax=nx.single_source_dijkstra(G,'s',weight='maxTranTime')
dmin,pmin=nx.single_source_dijkstra(G,'s',weight='minTranTime')

for w, attr in G.nodes(data=True):
    attr['maxTime']=dmax[w]
    attr['minTime']=dmin[w]



itercnt=0
while m<G.nodes[target]['ArrCDF'][0][-1]: 
    itercnt +=1
    ed=[]
    ed=list(G.edges(v))
    ed.sort()
    for v,w in ed:
        start_node={}
        target_node={}
        start_node['CDF']=G.nodes[v]['ArrCDF'] # Cdf vom StartKnoten
        target_node['CDF']=G.nodes[w]['ArrCDF'] #Cdf am Zielknotnen
        t0=G.nodes[w]['T0']

        PDFtransit=G.edges[v,w]['TransittimesPDF'] # Transit pdf
        Maxtransit=G.nodes[w]['maxTime'] # Maxtime um zum Zielknonten zu kommen
        v_Pfad=G.nodes[v]['Pfad']
        w_Pfad=G.nodes[w]['Pfad']

        templabel=labelprop.labelprop(cdf2pdf(np.array(start_node['CDF'])),np.array(PDFtransit),Maxtransit) # Faltung vom Startknoten mit transit pdf
        CDFtarget,t0,target_pfad=maxcdf.maxcdf(np.array(target_node['CDF']),pdf2cdf(templabel),t0,[v],w_Pfad,w) # Werte nehmen mit maximlaer Wahrscheinlichkeit

        G.nodes[w]['ArrCDF']=CDFtarget # ändern des zielknoten
        G.nodes[w]['T0']=t0 # neuer start wert
        G.nodes[w]['Pfad']=target_pfad

    G.nodes[v]['T0']=100000 # inf setzen von alten startknotnen damit dieser nicht wieder genommen wird
    m=[attr['T0'] for n, attr in G.nodes(data=True)]
    m=min(m)
    v=[n for n, attr in G.nodes(data=True)if attr['T0']==m]
    v=v[0]
    #print('nzk:',v)

#print(itercnt)

final = G.nodes[target]['ArrCDF']
#print(final)
#plt.plot(final[0],final[1])
#plt.show()
