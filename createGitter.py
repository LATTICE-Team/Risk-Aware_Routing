import numpy as np
import networkx as nx

def createGitterGraph(x,y): 
    G=nx.Graph()

    # Startknoten
    G.add_node('s',ArrCDF=[[0],[1]],T0=0,Pfad=['s'])
    # Giterknoten
    for i in range(1,x+1):
        for j in range(1,y+1):
            label=f'v_{i}_{j}'
            G.add_node(label,ArrCDF=[[100000.],[1.]],T0=100000,Pfad=[label])
    # Zielknoten
    G.add_node('t',ArrCDF=[[100000],[1]],T0=100000,Pfad=['t'])

    # Waagerechete Kanten 
    for i in range(1, x):
        for j in range(1, y+1):
         label1 = f'v_{i}_{j}'
         label2 = f'v_{i+1}_{j}'
         transits = [[1., 2., 3.], [1/3, 1/3, 1/3]]
         G.add_edge(label1, label2, TransittimesPDF=transits)

    # Vertikale Kanten
    for i in range(1, x+1):
        for j in range(1, y):
            label1 = f'v_{i}_{j}'
            label2 = f'v_{i}_{j+1}'
            transits = [[1., 2., 3.], [1/4, 1/4, 1/2]]
            G.add_edge(label1, label2, TransittimesPDF=transits)

    # s und t anschließen
    G.add_edge('s', 'v_1_1', TransittimesPDF=[[3.,4.,6.], [1/2, 1/3, 1/6]])
    G.add_edge(f'v_{x}_{y}', 't', TransittimesPDF=[[3.,4.,6.], [1/2, 1/3, 1/6]])
    return G


def createGraph2(x,y):
    G=nx.Graph()

    # Startknoten
    G.add_node('s',ArrCDF=[[0],[1]],T0=0,Pfad=['s'])
    # Giterknoten
    for i in range(1,x+1):
        for j in range(1,y+1):
            label=f'v_{i}_{j}'
            G.add_node(label,ArrCDF=[[100000.],[1.]],T0=100000,Pfad=[label])
    # Zielknoten
    G.add_node('t',ArrCDF=[[100000],[1]],T0=100000,Pfad=['t'])

    # Waagerechete Kanten 
    #vec_waa=[]
    b=[1.3,2.6,3.68,3.73,2.97,2.31]
    for i in range(1, x):
        for j in range(1, y+1):
         label1 = f'v_{i}_{j}'
         label2 = f'v_{i+1}_{j}'
         #a=np.random.uniform(0,4,1)
         a=b[i+j]
         transits = [[a, a+1., a+2.], [1/3, 1/3, 1/3]]
         G.add_edge(label1, label2, TransittimesPDF=transits)
         #vec_waa.append(a)


    # Vertikale Kanten
    #vec_vert=[]
    b=[3.76,2.94,1.66,0.68,3.20,0.77]
    for i in range(1, x+1):
        for j in range(1, y):
            label1 = f'v_{i}_{j}'
            label2 = f'v_{i}_{j+1}'
            #a=np.random.uniform(0,4,1)
            a=b[i+j]
            transits = [[a, a+1., a+3.], [1/4, 1/4, 1/2]]
            G.add_edge(label1, label2, TransittimesPDF=transits)
           # vec_vert.append(a)  

    #vec_diag=[]
    b=[3*1.76,3*2.6]
    for i in range(1,x):
        label1=f'v_{i}_{i}'
        label2=f'v_{i+1}_{i+1}'
        #a=np.random.uniform(0, 4, 1)
        a=b[i-1]
        transits = [[a, a+2., a+3.], [1/3, 1/3, 1/3]]
        G.add_edge(label1, label2, TransittimesPDF=transits)
        #vec_diag.append(a)    
    # s und t anschließen
    G.add_edge('s', 'v_1_1', TransittimesPDF=[[3.,4.,6.], [1/2, 1/3, 1/6]])
    G.add_edge(f'v_{x}_{y}', 't', TransittimesPDF=[[3.,4.,6.], [1/2, 1/3, 1/6]])
    return G

"""
x=10
y=10
G=createGitterGraph(x,y)
m1 = [attrs['T0'] for n, attrs in G.nodes(data=True) if 'T0' in attrs]
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
"""