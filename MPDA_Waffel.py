import Rhino.Geometry as rg


waffel_frames = None

points = []

rib_height = float(rib_height)

rib_width = float(rib_width)

if not isinstance(strips_u, list):

    strips_u = [strips_u] if strips_u else []

if not isinstance(strips_v, list):

    strips_v = [strips_v] if strips_v else []



breps = []



# -----------------------------------

# Helper: Create a rectangular rib brep along a curve

# -----------------------------------

def make_rib_mesh(crv, width, height, samples=12):
    if not crv or width <= 0 or height <= 0:
        return None

    params = crv.DivideByCount(samples, True)
    if not params or len(params) < 2:
        return None

    half_w = width / 2.0
    up = -rg.Vector3d.ZAxis
    verts = []
    for t in params:
        pt = crv.PointAt(t)
        tangent = crv.TangentAt(t)
        if not tangent or not tangent.IsValid or tangent.IsZero:
            continue
        tangent.Unitize()

        side = rg.Vector3d.CrossProduct(up, tangent)
        if not side.Unitize():
            side = rg.Vector3d.XAxis

        left = -side
        verts.append(pt + left * half_w)
        verts.append(pt + side * half_w)
        verts.append(pt + side * half_w + up * height)
        verts.append(pt + left * half_w + up * height)

    if len(verts) < 8:
        return None

    mesh = rg.Mesh()
    for v in verts:
        mesh.Vertices.Add(v)

    section_count = len(verts) // 4
    for i in range(section_count - 1):
        i0 = i * 4
        i1 = i0 + 1
        i2 = i0 + 2
        i3 = i0 + 3
        j0 = i0 + 4
        j1 = i1 + 4
        j2 = i2 + 4
        j3 = i3 + 4
        mesh.Faces.AddFace(i0, i1, j1, j0)
        mesh.Faces.AddFace(i1, i2, j2, j1)
        mesh.Faces.AddFace(i2, i3, j3, j2)
        mesh.Faces.AddFace(i3, i0, j0, j3)

    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh


# Simplified: no outline helpers; output will be the combined mesh of ribs.


# Simplified: per-mesh naked-outline helpers removed for clarity.


# -----------------------------------
# Build frame ribs as mesh
# -----------------------------------

rib_meshes = []
for crv in strips_u:
    rib = make_rib_mesh(crv, rib_width, rib_height)
    if rib and rib.IsValid and rib.Vertices.Count > 0:
        rib_meshes.append(rib)

for crv in strips_v:
    rib = make_rib_mesh(crv, rib_width, rib_height)
    if rib and rib.IsValid and rib.Vertices.Count > 0:
        rib_meshes.append(rib)

# Combine all rib meshes into a single mesh output
mesh = None
if rib_meshes:
    mesh = rg.Mesh()
    for m in rib_meshes:
        try:
            mesh.Append(m)
        except:
            pass
    try:
        mesh.Normals.ComputeNormals()
        mesh.Compact()
    except:
        pass

# Keep `frames_mesh` name for compatibility with previous outputs
frames_mesh = mesh

# No debug counters; script simplified to produce combined `mesh` only.

# Collect points for visualization
# -----------------------------------
for crvs in [strips_u, strips_v]:
    for c in crvs:
        try:
            ts = c.DivideByCount(10, True)
            if ts:
                for t in ts:
                    points.append(c.PointAt(t))
        except:
            pass