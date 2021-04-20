import numpy as np
from decimal import *

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

def edge(val, size):
    return (val == 1 or val == size+1)

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
    
    obj = np.zeros((size + 3,size + 3,size + 3), dtype=int)
    for z in range(1,size+2):
        for x in range(1,size+2):
            for y in range(1,size+2):
                if edge(x, size) or edge(y, size) or edge(z, size):
                    obj[z][x][y] = 1
                if (x in rows) or (y in rows):
                    obj[z][x][y] = 1
                    
    return obj
                    
def generateGridInfill(size, density, slope):
    total = int(size * density)
    gap = int(size / total)
        
    rows = []
    
    for i in range(-total, 2*total+1):
        rows.append(int(i * gap) + 1)
    print(rows)
    
    obj = np.zeros((size + 3,size + 3,size + 3), dtype=int)
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
            
def generateInfill(vertpairs):
    #rect
    o1 = generateRectInfill(100, .2)
    
    #grid
    o2 = generateGridInfill(100, .2, 1)
    
    print("")
    
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