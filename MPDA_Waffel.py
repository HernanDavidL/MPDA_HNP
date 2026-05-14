import Rhino.Geometry as rg

surface = None
mesh = rg.Mesh()
points = []

rib_height = float(rib_height)
rib_width = float(rib_width)
thickness = float(thickness)

breps = []

# -----------------------------------
# helper
# -----------------------------------
def make_rib(crv):

    if not crv:
        return None

    vec = rg.Vector3d(0,0,rib_height)

    ext = rg.Extrusion.Create(crv, rib_height, True)

    if ext:
        return ext.ToBrep()

    return None


# -----------------------------------
# U ribs
# -----------------------------------
for crv in strips_u:

    rib = make_rib(crv)

    if rib:
        breps.append(rib)

# -----------------------------------
# V ribs
# -----------------------------------
for crv in strips_v:

    rib = make_rib(crv)

    if rib:
        breps.append(rib)

# -----------------------------------
# Join
# -----------------------------------
if breps:
    joined = rg.Brep.JoinBreps(breps, 0.01)

    if joined and len(joined) > 0:
        surface = joined[0]
    else:
        surface = breps[0]

# -----------------------------------
# Mesh
# -----------------------------------
if surface:

    m = rg.Mesh.CreateFromBrep(
        surface,
        rg.MeshingParameters.Smooth
    )

    if m:
        for part in m:
            mesh.Append(part)

mesh.Normals.ComputeNormals()
mesh.Compact()

# -----------------------------------
# points
# -----------------------------------
for crvs in [strips_u, strips_v]:
    for c in crvs:
        ts = c.DivideByCount(10, True)
        if ts:
            for t in ts:
                points.append(c.PointAt(t))