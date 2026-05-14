#Hi guys im Ning
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

# ---------------------------------------------------------------
# WAVE PAVILION  —  Grasshopper Python Script
# ---------------------------------------------------------------
# WORKFLOW
#   1. Edit this file in VS Code
#   2. Copy the full file path  (right-click tab → Copy Path)
#   3. Paste the path into a Grasshopper Panel
#   4. Panel  →  Read File component  →  Python 3 Script component
#
# INPUT PINS  (add with right-click → Inputs on the Python component)
#   amp_h   Number Slider  0.0 – 5.0   Horizontal wave amplitude
#   amp_v   Number Slider  0.0 – 5.0   Vertical wave amplitude
#   freq_h  Number Slider  1.0 – 8.0   Horizontal frequency
#   freq_v  Number Slider  1.0 – 8.0   Vertical frequency
#   div_u   Number Slider  4   – 40    U divisions  (ribbon strips)
#   div_v   Number Slider  4   – 40    V divisions  (ribbon strips)
#   width   Number Slider  5.0 – 30.0  Pavilion width  (meters)
#   length  Number Slider  5.0 – 50.0  Pavilion length (meters)
#   height  Number Slider  1.0 – 10.0  Peak arch height
#
# OUTPUT PINS  (add with right-click → Outputs on the Python component)
#   surface   →  connect to a Surface parameter or Bake
#   mesh      →  connect to a Mesh parameter or Mesh Display
#   points    →  connect to a Point parameter or Point Cloud
#   strips_u  →  connect to a Curve parameter  (horizontal ribbons)
#   strips_v  →  connect to a Curve parameter  (vertical ribbons)
# ---------------------------------------------------------------


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

# The variables surface, mesh, points, strips_u, strips_v
# are automatically mapped to the output pins of the same name.
