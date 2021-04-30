
import random

import network

import numpy as np
import math

def generateDataset(sz, testData=False):
    dset = []
    for i in range(1,25):
        for n in range(sz):
            coordsTemp = []
            for j in range(i):
                #generate i random numbers
                r = random.randint(0,24)
                coordsTemp.append(r)
            stable = 1
            for c1 in range(len(coordsTemp)):
                hasNeighbor = False
                for c2 in range(len(coordsTemp)-1):
                    if c1 != c2:
                        diff = abs(c1 - c2)
                        if diff == 1 or (diff >= 4 and diff <= 6):
                            hasNeighbor = True
                if hasNeighbor == False:
                    stable = 0
                    break
            dataTemp = []
            imageTemp = np.ndarray(shape=(25,1), dtype=np.float64)
            stableThresh = i - 1
            for j in range(0,24):
                if coordsTemp.__contains__(j):
                    imageTemp[j] = 1.
                else:
                    imageTemp[j] = 0.
            label = []
            if stable >= stableThresh:
                if testData:
                    label = 1
                else:
                    label = np.zeros((2,1), dtype=np.float64)
                    label[1] = 1.
            else:
                if testData:
                    label = 0
                else:
                    label = np.zeros((2,1), dtype=np.float64)
                    label[0] = 1.
            dset.append((imageTemp,label))
    
    return dset

train = generateDataset(10000)

test = generateDataset(2000, True)

net = network.Network([25, 15, 2])

net.SGD(train, 10, 40, 3.0, test)
    