import Rhino.Geometry as rg



waffel_frames = None

points = []



rib_height = float(rib_height)

rib_width = float(rib_width)



# Convert single curves to lists if needed

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
if frames_mesh and frames_mesh.Vertices.Count > 0:
    try:
        naked_edges = frames_mesh.GetNakedEdges()
        if naked_edges:
            edge_curves = [e for e in naked_edges if e and e.IsValid and e.GetLength() > 1e-6]
            if edge_curves:
                # Try joining with increasing tolerances to get closed outlines
                candidates = []
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

                # Prefer largest closed curve by area
                best_curve = None
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
                    # If no closed curves, attempt to build the longest chained polyline
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
                            # start with this segment
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
                                        # reverse s by creating a reversed curve
                                        try:
                                            rev = s.DuplicateCurve()
                                            rev.Reverse()
                                            seq.append(rev)
                                            used.add(i)
                                            changed = True
                                            break
                                        except:
                                            pass
                            # build point list for seq
                            pts = [seq[0].PointAtStart()]
                            for sc in seq:
                                pts.append(sc.PointAtEnd())
                            # compute total length
                            length = sum([pts[i].DistanceTo(pts[i+1]) for i in range(len(pts)-1)])
                            if length > best_len:
                                best_len = length
                                best_pts = pts
                            used_global.update(used)
                        if best_pts and len(best_pts) > 1:
                            # close if endpoints match
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
                        # fallback: pick the longest candidate curve
                        try:
                            best_curve = max(candidates, key=lambda c: c.GetLength())
                        except:
                            best_curve = candidates[0] if candidates else None

                if best_curve:
                    frames_curve = [best_curve]
                else:
                    frames_curve = list(candidates)
    except:
        frames_curve = []

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