import Rhino.Geometry as rg
import math

def create_tear_drop(base_pt, total_height):
   
    width = abs(total_height) * 0.35
    
    p1 = rg.Point3d(base_pt.X, base_pt.Y, base_pt.Z + total_height) 
    p2 = rg.Point3d(base_pt.X + width, base_pt.Y, base_pt.Z + (total_height * 0.7)) 
    p3 = rg.Point3d(base_pt.X, base_pt.Y, base_pt.Z) 
    
    profile_curve = rg.Curve.CreateInterpolatedCurve([p1, p2, p3], 3)
    
    axis_line = rg.Line(base_pt, rg.Point3d(base_pt.X, base_pt.Y, base_pt.Z + 1.0))
    
    rev_surface = rg.RevSurface.Create(profile_curve, axis_line)
    
    return rev_surface.ToBrep()

if Point and Height:
    try:
        drop_length = -float(Height)
        
        drop_brep = create_tear_drop(Point, drop_length) 

        if drop_brep:
            mesh_params = rg.MeshingParameters.Smooth
            mesh_parts = rg.Mesh.CreateFromBrep(drop_brep, mesh_params)
            
            if mesh_parts and len(mesh_parts) > 0:
                Mesh = mesh_parts[0]
                Mesh.Normals.ComputeNormals()
                Mesh.Compact()
            else:
                Mesh = None
    except Exception as e:
        Mesh = str(e)