import fun_pdf_cdf
import createGitter
import labelprop
import maxcdf
import numpy as np
import networkx as nx 
import matplotlib.pyplot as plt 
import zeichene_Graph

def cdf2pdf(cdf): 
     """
    Convert a discrete cumulative distribution function (CDF)
    to a probability density function (PDF).

    Parameters
    ----------
    cdf : numpy.ndarray
        2 x N array containing the cumulative distribution.

    Returns
    -------
    pdf : numpy.ndarray
        2 x N array containing the probability density.
    """
     #cdf[1, 1:] -= cdf[1, :-1]
     pdf=cdf.copy()
     if cdf.shape[1]==1:
         cdf=np.append([[0],[1]],cdf,axis=1)

     for i in  range(1,pdf.shape[1]):
        pdf[1,i]=cdf[1,i]-cdf[1,i-1]

     return pdf 
def pdf2cdf(pdf):
    """
    Convert Pdf to CDF
    Input: PDf: 2xN Array double (Probebillity function )
    Output: CDF: 2xN Array double (sum of them )
    """
    pdf[1]=np.minimum(np.cumsum(pdf[1]),1.0)
    return pdf

x=3
y=3

G=createGitter.createGraph2(x,y)
nodes = list(G.nodes(data=True))
m1 = [attrs['T0'] for n, attrs in G.nodes(data=True) if 'T0' in attrs]

m=[attr['T0'] for n, attr in G.nodes(data=True)]
m=min(m)
v=[n for n, attr in G.nodes(data=True)if attr['T0']==m]
target='t'

Gmax=G
Gmin=G

e_nr=nx.number_of_edges(G)
#maxTime=[max(attr['TransittimesPDF'][0]) for u,w , attr in G.edges(data=True)]
#minTime=[min(attr['TransittimesPDF'][0]) for u,w, attr in G.edges(data=True)]

for u, w, attr in G.edges(data=True):
    attr['maxTranTime'] = [max(attr['TransittimesPDF'][0])]
    attr['minTranTime'] = [min(attr['TransittimesPDF'][0])]

dmax,pmax=nx.single_source_dijkstra(G,'s',weight=lambda u, v, d: d['maxTranTime'][0])
dmin,pmin=nx.single_source_dijkstra(G,'s',weight=lambda u, v, d: d['minTranTime'][0])

for w,attr in G.nodes(data=True):
    attr['maxTime']=dmax[w]
    attr['minTime']=dmin[w]


#print(dmax,pmax)
#print(dmin,pmin)
zeichene_Graph.zeichne_graph(G.nodes,G.edges)


#ähnlcihe Dijkstra Berechnung mit Verteiungsfunktionen

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
    m=[attr['T0'] for n, attr in G.nodes(data=True)] # 
    m=min(m)
    v=[n for n, attr in G.nodes(data=True)if attr['T0']==m]
    v=v[0]
    #print('nzk:',v)

print(itercnt)

final = G.nodes[target]['ArrCDF']
print(final)
#plt.plot(final[0],final[1])
#plt.show()