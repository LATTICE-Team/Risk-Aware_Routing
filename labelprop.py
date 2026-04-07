import numpy as np

def labelprop(pdf1, pdf2, maxTime):
    """
    Propagate a vertex label (pdf) via an edge.
    Output is label at end of edge (pdfout, no update of target vertex label).
    
    Parameters
    ----------
    pdf1 : np.ndarray
        2 x N array, first pdf
    pdf2 : np.ndarray
        2 x M array, second pdf
    maxTime : float
        maximum allowed time
    
    Returns
    -------
    pdfout : np.ndarray
        propagated pdf
    """
    pdfout_list = []
    pdfout=[]
    n1 = pdf1.shape[1]
    n2 = pdf2.shape[1]
    for i in range(n1):
        Rp=0
        for j in range(n2):
            value=pdf1[0,i]+pdf2[0,j]
            if value>=maxTime:
                prob=1-Rp
                pdfout.append([value,prob])
                break
            else:
                prob=pdf1[1,i]*pdf2[1,j] 
                Rp=Rp+prob
                pdfout.append([value,prob])

    """  
    for i in range(pdf1.shape[1]):
        for j in range(pdf2.shape[1]):
        
            value = pdf1[0, i] + pdf2[0, j]
            prob = pdf1[1, i] * pdf2[1, j]

            pdfout.append([value, prob])
    """

    pdfout = np.array(pdfout).T


    # Sortieren nach erster Zeile (Zeit)
    sort_idx = np.argsort(pdfout[0, :])
    pdfout = pdfout[:, sort_idx]

    # Doppelte Zeiten zusammenführen (Wahrscheinlichkeiten addieren)
    """
    i = 0
    while i < pdfout.shape[1] - 1:
        if pdfout[0, i] == pdfout[0, i+1]:
            pdfout[1, i] = min(pdfout[1,i]+pdfout[1, i+1],1)
            pdfout = np.delete(pdfout, i+1, axis=1)
        else:
            i += 1

    return pdfout
    """
    i=0
    sp=0
    while i<pdfout.shape[1]-1:
        if pdfout[0,i]>=maxTime:
            sp=np.sum(pdfout[1,:i])
            pdfout[1,i]=1-sp
            pdfout = np.delete(pdfout, [i+1,-1], axis=1) #löschen alle folgenden noch machen 
        elif pdfout[0,i]==pdfout[0,i+1]:
            pdfout[1, i] = pdfout[1,i]+pdfout[1, i+1]
            pdfout = np.delete(pdfout, i+1, axis=1)
        else:
            i+=1

        
        

    return pdfout 
"""
pdf1 = np.array([[4., 5., 6., 7., 8.,9.],
       [0.16666667, 0.27777778, 0.27777778, 0.16666667, 0.05555556,
        0.05555556]])
pdf2 = np.array([[1.  , 2.  , 3.  ],
       [0.25, 0.25, 0.5 ]])
maxTime = 9
pdfout = labelprop(pdf1, pdf2, maxTime)
print("pdfout =\n", pdfout)
"""