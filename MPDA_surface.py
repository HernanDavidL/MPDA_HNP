import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def get_z_height(u, v, ah, av, fh, fv, h, dh, ratio, loc_u, loc_v):
    z_wave = ah * math.sin(fh * math.pi * u)
    z_wave += av * math.sin(fv * math.pi * v)
    z_arch = h * math.sin(math.pi * v)
    
    # Calculate distance in UV space
    dist = math.sqrt((u - loc_u)**2 + (v - loc_v)**2)
    max_influence_dist = 0.707 * ratio
    
    if dist < max_influence_dist:
        influence = 0.5 * (math.cos(math.pi * (dist / max_influence_dist)) + 1.0)
        z_drop = -(influence * dh)
    else:
        z_drop = 0
    return z_wave + z_arch + z_drop

# --- Inputs ---
nu = max(int(div_u), 2)
nv = max(int(div_v), 2)
r_val = max(drop_part_ratio, 0.001)

# --- THE FIX: Convert actual coordinates to 0-1 range ---
if drop_location:
    # We divide by width and length so the drop stays inside the mesh
    loc_u = drop_location.X / width
    loc_v = drop_location.Y / length
else:
    loc_u, loc_v = 0.5, 0.5

# --- Build Grid ---
rows = []
all_pts = []
for j in range(nv + 1):
    v = j / float(nv)
    y = v * length
    row = []
    for i in range(nu + 1):
        u = i / float(nu)
        x = u * width
        z = get_z_height(u, v, amp_h, amp_v, freq_h, freq_v, height, drop_height, r_val, loc_u, loc_v)
        pt = rg.Point3d(x, y, z)
        row.append(pt)
        all_pts.append(pt)
    rows.append(row)

# --- Mesh ---
mesh = rg.Mesh()
for pt in all_pts: mesh.Vertices.Add(pt)
for j in range(nv):
    for i in range(nu):
        a, b = j * (nu + 1) + i, j * (nu + 1) + i + 1
        c, d = a + (nu + 1) + 1, a + (nu + 1)
        mesh.Faces.AddFace(a, b, c, d)
mesh.Normals.ComputeNormals()
mesh.Compact()

# --- Outputs ---
strips_u = [rg.Curve.CreateInterpolatedCurve(r, 3) for r in rows]
strips_v = []
for i in range(nu + 1):
    column = [rows[j][i] for j in range(nv + 1)]
    strips_v.append(rg.Curve.CreateInterpolatedCurve(column, 3))

mesh = mesh # or mesh_out = mesh depending on your nub name
points = all_pts