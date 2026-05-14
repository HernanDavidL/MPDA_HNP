import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def wave_z(u, v, ah, av, fh, fv, h):
    """Return the Z height at normalised position (u, v) in [0,1]."""
    z  = ah * math.sin(fh * math.pi * u)
    z += av * math.sin(fv * math.pi * v)
    z += h  * math.sin(math.pi * v)   # main arch curve
    return z


# --- guard against zero divisions ---
nu = max(int(div_u), 2)
nv = max(int(div_v), 2)

# --- build point grid ---
rows = []
all_pts = []

for j in range(nv + 1):
    v = j / float(nv)
    y = v * length
    row = []
    for i in range(nu + 1):
        u = i / float(nu)
        x = u * width
        z = wave_z(u, v, amp_h, amp_v, freq_h, freq_v, height)
        pt = rg.Point3d(x, y, z)
        row.append(pt)
        all_pts.append(pt)
    rows.append(row)

# --- SURFACE (NurbsSurface interpolated through the grid) ---
surface = rg.NurbsSurface.CreateFromPoints(
    all_pts,
    nu + 1,   # point count in U direction
    nv + 1,   # point count in V direction
    3,         # degree U
    3          # degree V
)

# --- MESH (quad faces) ---
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

# --- POINTS ---
points = all_pts

# --- STRIPS U  (horizontal ribbons — run across the width) ---
strips_u = []
for j in range(nv + 1):
    crv = rg.Curve.CreateInterpolatedCurve(rows[j], 3)
    if crv:
        strips_u.append(crv)

# --- STRIPS V  (longitudinal ribbons — run along the length) ---
strips_v = []
for i in range(nu + 1):
    col = [rows[j][i] for j in range(nv + 1)]
    crv = rg.Curve.CreateInterpolatedCurve(col, 3)
    if crv:
        strips_v.append(crv)
