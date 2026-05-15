import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def get_z_height(u, v, ah, av, fh, fv, h, dh):
    
    z_wave = ah * math.sin(fh * math.pi * u)
    z_wave += av * math.sin(fv * math.pi * v)
    z_arch = h * math.sin(math.pi * v)
    center_u, center_v = 0.5, 0.5
    dist = math.sqrt((u - center_u)**2 + (v - center_v)**2)
    
    falloff = math.exp(-pow(dist * 3.0, 2)) 
    z_drop = -(falloff * dh) # Negative because it hangs down
    
    return z_wave + z_arch + z_drop

nu = max(int(div_u), 2)
nv = max(int(div_v), 2)

rows = []
all_pts = []


for j in range(nv + 1):
    v = j / float(nv)
    y = v * length
    row = []
    for i in range(nu + 1):
        u = i / float(nu)
        x = u * width
        
    
        z = get_z_height(u, v, amp_h, amp_v, freq_h, freq_v, height, Drop_Height)
        
        pt = rg.Point3d(x, y, z)
        row.append(pt)
        all_pts.append(pt)
    rows.append(row)

mesh = rg.Mesh()
for pt in all_pts:
    mesh.Vertices.Add(pt)

for j in range(nv):
    for i in range(nu):
        a = j * (nu + 1) + i
        b = a + 1
        c = a + (nu + 1) + 1
        d = a + (nu + 1)
        mesh.Faces.AddFace(a, b, c, d)

mesh.Normals.ComputeNormals()
mesh.Compact()

strips_u = [rg.Curve.CreateInterpolatedCurve(r, 3) for r in rows]
strips_v = []
for i in range(nu + 1):
    col = [rows[j][i] for j in range(nv + 1)]
    strips_v.append(rg.Curve.CreateInterpolatedCurve(col, 3))


mesh_out = mesh
curves_u = strips_u
curves_v = strips_v
points = all_pts