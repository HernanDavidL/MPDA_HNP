import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import math

def get_z_height(u, v, ah, av, fh, fv, h, dh, ratio):
    # 1. Sine Wave Texture (Keep small for the 'flat' look)
    z_wave = ah * math.sin(fh * math.pi * u)
    z_wave += av * math.sin(fv * math.pi * v)
    
    # 2. Base Arch (The overall subtle curve)
    z_arch = h * math.sin(math.pi * v)
    
    # 3. Controlled Drop Logic
    center_u, center_v = 0.5, 0.5
    dist = math.sqrt((u - center_u)**2 + (v - center_v)**2)
    
    # Normalize distance (max distance from center to corner is ~0.707)
    # We use the ratio to define where the 'flat' zone starts.
    max_dist = 0.707 * ratio
    
    if dist < max_dist:
        # Create a smooth curve from center (1.0) to the flat edge (0.0)
        # Using a Cosine interpolation for a natural architectural look
        influence = 0.5 * (math.cos(math.pi * (dist / max_dist)) + 1.0)
        z_drop = -(influence * dh)
    else:
        # Outside the ratio area, it is perfectly flat
        z_drop = 0
    
    return z_wave + z_arch + z_drop

# --- Guard against zero divisions ---
nu = max(int(div_u), 2)
nv = max(int(div_v), 2)
# Ensure ratio isn't zero to avoid division error
r_val = max(drop_part_ratio, 0.001)

rows = []
all_pts = []

for j in range(nv + 1):
    v = j / float(nv)
    y = v * length
    row = []
    for i in range(nu + 1):
        u = i / float(nu)
        x = u * width
        
        # Calculate Z with the new ratio control
        z = get_z_height(u, v, amp_h, amp_v, freq_h, freq_v, height, drop_height, r_val)
        
        pt = rg.Point3d(x, y, z)
        row.append(pt)
        all_pts.append(pt)
    rows.append(row)

# --- Mesh Generation ---
mesh = rg.Mesh()
for pt in all_pts: mesh.Vertices.Add(pt)
for j in range(nv):
    for i in range(nu):
        a, b = j * (nu + 1) + i, j * (nu + 1) + i + 1
        c, d = a + (nu + 1) + 1, a + (nu + 1)
        mesh.Faces.AddFace(a, b, c, d)

# --- Curve Generation ---
curves_u = [rg.Curve.CreateInterpolatedCurve(r, 3) for r in rows]
curves_v = []
for i in range(nu + 1):
    col = [rows[j][i] for j in range(nv + 1)]
    curves_v.append(rg.Curve.CreateInterpolatedCurve(col, 3))

# --- Outputs ---
mesh_out = mesh
points = all_pts