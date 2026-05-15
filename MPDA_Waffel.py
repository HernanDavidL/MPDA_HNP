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


def get_mesh_outline(mesh):
    if not mesh or mesh.Vertices.Count == 0:
        return None

    try:
        naked_edges = mesh.GetNakedEdges()
    except:
        naked_edges = None

    edge_curves = [e for e in (naked_edges or []) if e and e.IsValid and e.GetLength() > 1e-6]

    # Try joining with increasing tolerances
    candidates = []
    if edge_curves:
        for tol in (1e-6, 1e-4, 1e-3, 1e-2):
            try:
                joined = rg.Curve.JoinCurves(edge_curves, tol)
                if joined:
                    candidates = joined
                    break
            except:
                pass
        if not candidates:
            candidates = edge_curves

    # If we have candidate curves, prefer largest closed curve
    best_curve = None
    if candidates:
        closed = [c for c in candidates if c and c.IsClosed]
        if closed:
            best_area = -1.0
            for c in closed:
                try:
                    ap = rg.AreaMassProperties.Compute(c)
                    area = abs(ap.Area) if ap else c.GetLength()
                except:
                    area = c.GetLength()
                if area > best_area:
                    best_area = area
                    best_curve = c
        else:
            # chain open segments into longest polyline
            def chain_longest(segments, tol=1e-3):
                segs = list(segments)
                used_global = set()
                best_pts = None
                best_len = 0.0
                for start_idx in range(len(segs)):
                    if start_idx in used_global:
                        continue
                    used = set()
                    seq = []
                    cur = segs[start_idx]
                    used.add(start_idx)
                    seq.append(cur)
                    changed = True
                    while changed:
                        changed = False
                        end_pt = seq[-1].PointAtEnd()
                        for i, s in enumerate(segs):
                            if i in used:
                                continue
                            a = s.PointAtStart()
                            b = s.PointAtEnd()
                            if end_pt.DistanceTo(a) <= tol:
                                seq.append(s)
                                used.add(i)
                                changed = True
                                break
                            if end_pt.DistanceTo(b) <= tol:
                                try:
                                    rev = s.DuplicateCurve()
                                    rev.Reverse()
                                    seq.append(rev)
                                    used.add(i)
                                    changed = True
                                    break
                                except:
                                    pass
                    pts = [seq[0].PointAtStart()]
                    for sc in seq:
                        pts.append(sc.PointAtEnd())
                    length = sum([pts[i].DistanceTo(pts[i+1]) for i in range(len(pts)-1)])
                    if length > best_len:
                        best_len = length
                        best_pts = pts
                    used_global.update(used)
                if best_pts and len(best_pts) > 1:
                    if best_pts[0].DistanceTo(best_pts[-1]) <= 1e-3:
                        best_pts[-1] = best_pts[0]
                    pl = rg.Polyline(best_pts)
                    if pl.IsValid and pl.Count > 1:
                        return rg.PolylineCurve(pl)
                return None

            chained = chain_longest(candidates, tol=1e-3)
            if chained:
                best_curve = chained
            else:
                try:
                    best_curve = max(candidates, key=lambda c: c.GetLength())
                except:
                    best_curve = candidates[0] if candidates else None

    # If no candidate outline, fallback to convex hull of vertices
    if not best_curve:
        try:
            pts3 = [mesh.Vertices[i] for i in range(mesh.Vertices.Count)]
            if pts3:
                seen = set()
                pts2 = []
                for p in pts3:
                    key = (round(p.X, 6), round(p.Y, 6))
                    if key in seen:
                        continue
                    seen.add(key)
                    pts2.append((p.X, p.Y))

                def cross(o, a, b):
                    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])

                pts2_sorted = sorted(pts2)
                if len(pts2_sorted) >= 3:
                    lower = []
                    for p in pts2_sorted:
                        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                            lower.pop()
                        lower.append(p)
                    upper = []
                    for p in reversed(pts2_sorted):
                        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                            upper.pop()
                        upper.append(p)
                    hull2 = lower[:-1] + upper[:-1]
                    avgZ = sum([v.Z for v in pts3]) / len(pts3)
                    poly_pts = [rg.Point3d(x, y, avgZ) for (x, y) in hull2]
                    if len(poly_pts) > 1:
                        if poly_pts[0].DistanceTo(poly_pts[-1]) > 1e-6:
                            poly_pts.append(poly_pts[0])
                        pl = rg.Polyline(poly_pts)
                        if pl.IsValid and pl.Count > 1:
                            return rg.PolylineCurve(pl)
        except:
            pass

    return best_curve


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

frames_mesh = None
if rib_meshes:
    frames_mesh = rib_meshes[0]
    for m in rib_meshes[1:]:
        try:
            frames_mesh.Append(m)
        except:
            pass
    if frames_mesh and frames_mesh.Vertices.Count > 0:
        try:
            frames_mesh.Normals.ComputeNormals()
            frames_mesh.Compact()
        except:
            pass

frames_curve = []
if rib_meshes:
    for m in rib_meshes:
        try:
            outline = get_mesh_outline(m)
        except:
            outline = None
        frames_curve.append(outline)

# Debugging counters for Grasshopper inspection
frames_naked_count = 0
frames_candidates_count = 0
frames_closed_count = 0
try:
    frames_naked_count = len(edge_curves) if 'edge_curves' in locals() and edge_curves else 0
    frames_candidates_count = len(candidates) if 'candidates' in locals() and candidates else 0
    frames_closed_count = len(closed) if 'closed' in locals() and closed else 0
except:
    pass

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