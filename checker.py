import numpy as np
from decimal import *
import copy
import random

granularity = .01

class WavefrontOBJ:
    def __init__( self, default_mtl='default_mtl' ):
        self.path      = None               # path of loaded object
        self.mtllibs   = []                 # .mtl files references via mtllib
        self.mtls      = [ default_mtl ]    # materials referenced
        self.mtlid     = []                 # indices into self.mtls for each polygon
        self.vertices  = []                 # vertices as an Nx3 or Nx6 array (per vtx colors)
        self.normals   = []                 # normals
        self.texcoords = []                 # texture coordinates
        self.polygons  = []                 # M*Nv*3 array, Nv=# of vertices, stored as vid,tid,nid (-1 for N/A)

def load_obj( filename: str, default_mtl='default_mtl', triangulate=False ) -> WavefrontOBJ:
    def parse_vertex( vstr ):
        vals = vstr.split('/')
        vid = int(vals[0])-1
        tid = int(vals[1])-1 if len(vals) > 1 and vals[1] else -1
        nid = int(vals[2])-1 if len(vals) > 2 else -1
        return (vid,tid,nid)

    with open( filename, 'r' ) as objf:
        obj = WavefrontOBJ(default_mtl=default_mtl)
        obj.path = filename
        cur_mat = obj.mtls.index(default_mtl)
        for line in objf:
            toks = line.split()
            if not toks:
                continue
            if toks[0] == 'v':
                obj.vertices.append( [ float(v) for v in toks[1:]] )
            elif toks[0] == 'vn':
                obj.normals.append( [ float(v) for v in toks[1:]] )
            elif toks[0] == 'vt':
                obj.texcoords.append( [ float(v) for v in toks[1:]] )
            elif toks[0] == 'f':
                poly = [ parse_vertex(vstr) for vstr in toks[1:] ]
                if triangulate:
                    for i in range(2,len(poly)):
                        obj.mtlid.append( cur_mat )
                        obj.polygons.append( (poly[0], poly[i-1], poly[i] ) )
                else:
                    obj.mtlid.append(cur_mat)
                    obj.polygons.append( poly )
            elif toks[0] == 'mtllib':
                obj.mtllibs.append( toks[1] )
            elif toks[0] == 'usemtl':
                if toks[1] not in obj.mtls:
                    obj.mtls.append(toks[1])
                cur_mat = obj.mtls.index( toks[1] )
        return obj

def save_obj( obj: WavefrontOBJ, filename: str ):
    with open( filename, 'w' ) as ofile:
        for mlib in obj.mtllibs:
            ofile.write('mtllib {}\n'.format(mlib))
        for vtx in obj.vertices:
            ofile.write('v '+' '.join(['{}'.format(v) for v in vtx])+'\n')
        for tex in obj.texcoords:
            ofile.write('vt '+' '.join(['{}'.format(vt) for vt in tex])+'\n')
        for nrm in obj.normals:
            ofile.write('vn '+' '.join(['{}'.format(vn) for vn in nrm])+'\n')
        if not obj.mtlid:
            obj.mtlid = [-1] * len(obj.polygons)
        poly_idx = np.argsort( np.array( obj.mtlid ) )
        cur_mat = -1
        for pid in poly_idx:
            if obj.mtlid[pid] != cur_mat:
                cur_mat = obj.mtlid[pid]
                ofile.write('usemtl {}\n'.format(obj.mtls[cur_mat]))
            pstr = 'f '
            for v in obj.polygons[pid]:
                vstr = '{}/{}/{} '.format(v[0]+1,v[1]+1 if v[1] >= 0 else 'X', v[2]+1 if v[2] >= 0 else 'X' )
                vstr = vstr.replace('/X/','//').replace('/X ', ' ')
                pstr += vstr
            ofile.write( pstr+'\n')
#courtesy of http://jamesgregson.ca/loadsave-wavefront-obj-files-in-python.html

#check if value is an edge
def edge(val, size):
    return (val == 1 or val == size)

#generates 3d object a square infill with given density
def generateRectInfill(size, density):
    '''verts = verts2.copy()
    for i in range(len(verts)):
        diff = abs(verts[i][0][axis] - verts[i][1][axis])
        gap = (density * diff)
        total = int(diff / density / 2)
        max = verts[i][1][axis]
        for j in range(total - 1):
            val = round(max - ((j + 1) * gap), 2)
            inp = [verts[i][0][0],verts[i][0][1],verts[i][0][2]]
            inp[axis] = val
            verts[i].insert(1,inp)
        print(verts[i])'''
        
    total = int(size * density)
    gap = int(size / total)
        
    rows = []
    
    for i in range(1, total):
        rows.append(int(i * gap) + 1)
    
    obj = np.zeros((size + 2,size + 2,size + 2), dtype=int)
    for z in range(1,size+1):
        for x in range(1,size+1):
            for y in range(1,size+1):
                if edge(x, size) or edge(y, size) or edge(z, size):
                    obj[z][x][y] = 1
                if (x in rows) or (y in rows):
                    obj[z][x][y] = 1
                    
    return obj
           
#generates 3d object an x shaped infill with given density         
def generateGridInfill(size, density, slope):
    total = int(size * density)
    gap = int(size / total)
        
    rows = []
    
    for i in range(-total, 2*total+1):
        rows.append(int(i * gap) + 1)
    
    obj = np.zeros((size + 2,size + 2,size + 2), dtype=int)
    for z in range(1,size+2):
        for x in range(1,size+2):
            for y in range(1,size+2):
                if edge(x, size) or edge(y, size) or edge(z, size):
                    obj[z][x][y] = 1
                for r in rows:
                    if ((int((x-1)*slope) + r == y) or (int((-1/slope)*(x-1)) + r == y)) and y != size + 1:
                        obj[z][x][y] = 1
                        break
    return obj
            
#tests to be run for all values
def generateInfill(vertpairs):
    #rect
    o1 = generateRectInfill(125, .2)
#     o1Mixup = copy.deepcopy(o1)
#     o1Mixup = mixupObj(o1Mixup, 125)
#     print("01 diff ",totalDiff(o1, o1Mixup, 125))

    buildObject(o1, 125)
    
    #grid
    o2 = generateGridInfill(125, .2, 1)
    buildObject(o2,125)
    #o2Mixup = copy.deepcopy(o2)
    #o2Mixup = mixupObj(o2Mixup, 125)
    #print("02 diff ",totalDiff(o2, o2Mixup, 125))
    
    print("")
    
#every time there is a shift over there is a chance that there will be a mechanical error resulting in a skipped spot, 
#this will lead to recalculating the str of the object and then determining if the differences will cause significant str changes
def buildObject(obj, size):
    newObj = np.zeros((size + 2,size + 2,size + 2), dtype=int)
    cost = 0
    amtFlaws = 0
    for z in range(1, size+1):
        for x in range(1, size+1):
            for y in range(1, size+1):
                r = random.randint(0,99)
                yModifier = 0
                if r < 1:
                    yModifier = 1
                newObj[z][x][y] = 0
                newObj[z][x][y + yModifier] = 1
                cost += 1
                if yModifier == 1:
                    putInNew = testRestOfObjForStr(obj, newObj, z, x, y, size)
                    amtFlaws += 1
                    if putInNew:
                        cost += 7
                        newObj[z][x][y] = 1
                y+= yModifier
    print("object cost to build was",cost,"supposed to be",size*size*size,"but had to correct",amtFlaws,"flaws")

#assuming no other printing errors will occur copy the rest of the object to the current object and compare strengths
def testRestOfObjForStr(obj, newObj, z, x, y, size):
    strThresh = 5
    newObj[z][x][y+2:size+2] = obj[z][x][y+2:size+2]
    newObj[z][x:size+2][0:size+2] = obj[z][x:size+2][0:size+2]
    newObj[z:size+2][0:size+2][0:size+2] = obj[z:size+2][0:size+2][0:size+2]
    str = getObjStr(newObj,size)
    strOld = getObjStr(obj,size)
    print("strength with flaw ", str, " str w/o flaw ", strOld)
    if strOld - str < strThresh and strOld > str:
        return True
    return False

#get the strength of a full object
def getObjStr(o1,size):
    oTemp = o1[1:size+1,1:size+1,1:size+1]
    for i in range(2):
        ret = np.zeros((int(len(oTemp)/5),int(len(oTemp)/5),int(len(oTemp)/5)),dtype=int)
        for z in range(int(len(oTemp)/5)):
            for x in range(int(len(oTemp)/5)):
                for y in range(int(len(oTemp)/5)):
                    temp5by5 = get5by5(oTemp, len(oTemp), z*5, x*5, y*5)
                    if i == 0:
                        strVal = getStr5by5(temp5by5)
                    else:
                        strVal = np.sum(temp5by5)
                    ret[z][x][y] = strVal
        oTemp = ret
    return np.sum(oTemp)
    
#shuffle object
def mixupObj(obj, size):
    for z in range(1, size+1):
        for x in range(1, size+1):
            for y in range(1, size+1):
                r = random.randint(0,99)
                if r < 10 and obj[z][x][y] == 1:
                    obj[z][x][y] = 0
                    x1 = random.randint(-1,1)
                    y1 = random.randint(-1,1)
                    z1 = random.randint(-1,1)
                    obj[z + z1][x + x1][y + y1] = 1
    return obj

#range check
def outofrange(size, z1, x1, y1, z, x, y):
    if z1 + z < 0 or z1 + z > size+2:
        return True
    elif x1 + x < 0 or x1 + x > size+2:
        return True
    elif y1 + y < 0 or y1 + y > size+2:
        return True
    return False

#get a 5x5x5 partial object at given indices
def get5by5(obj, size, z1, x1, y1):
    ret = np.zeros((5,5,5),dtype=int)
    for z in range(-2,3):
        for x in range(-2,3):
            for y in range(-2,3):
                if not outofrange(size, z1, x1, y1, z, x, y):
                    ret[z+2][x+2][y+2] = obj[z1+z][x1+x][y1+y]
    return ret

#calculate the str of a 5x5x5 object
def getStr5by5(inp):
    smallTotal = 0
    neighborStr = 0
    for z in range(5):
        for x in range(5):
            for y in range(5):
                if inp[z][x][y] == 1:
                    tempNeighborStr = 0.0
                    for z1 in range(-1,2):
                        for x1 in range(-1,2):
                            for y1 in range(-1,2):
                                try:
                                    if inp[z+z1][x+x1][y+y1] == 1:
                                        planesInCommon = 0
                                        if(z1 == 0):
                                            planesInCommon += 1
                                        if(x1 == 0):
                                            planesInCommon += 1
                                        if(y1 == 0):
                                            planesInCommon += 1
                                        
                                        if planesInCommon == 0:
                                            tempNeighborStr += 1
                                        elif planesInCommon == 1:
                                            tempNeighborStr += 4
                                        else:
                                            tempNeighborStr += 16
                                except IndexError:
                                    continue
                    neighborStr += tempNeighborStr
                    smallTotal += 1
                    
    str = smallTotal/125
    return neighborStr

# testStr = np.zeros((5,5,5),dtype=int)
# for z in range(5):
#     for x in range(5):
#         for y in range(5):
#             testStr[z][x][y] = 1
# 
# print(getStr5by5(testStr))
# exit()

#measure differences between 2 objects
def totalDiff(og, o2, size):
    diff = 0
    for z in range(1, size+2):
        for x in range(1, size+2):
            for y in range(1, size+2):
                if(og[z][x][y] != o2[z][x][y]):
                    diff += 1
    return diff
    
#get diffreent faces of an obj file
def getFace(axis, verts):
    allRet = []
    for i in range(len(verts)):
        tempRet = []
        if not verts[i] in allRet:
            tempRet.append(verts[i])
        for j in range(len(verts)):
            if i != j:
                if verts[i][axis] == verts[j][axis] and not verts[j] in allRet:
                    tempRet.append(verts[j])
        tempRet.sort()
        if not tempRet in allRet:
            allRet.append(tempRet)
    return allRet
    
            
cube = load_obj("cube.obj")

f = getFace(2,cube.vertices)
infillInput = []
for face in f:
    f2 = getFace(1, face)
    for i in f2:
        infillInput.append(i)

generateInfill(infillInput)