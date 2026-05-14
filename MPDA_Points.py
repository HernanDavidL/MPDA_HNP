import Rhino.Geometry as rg
import math

def create_drop_geometry(base_pt, height):
   
    radius = height / 3.0
   
    center_pt = rg.Point3d(base_pt.X, base_pt.Y, base_pt.Z + radius)
    sphere = rg.Sphere(center_pt, radius)
    drop_brep = sphere.ToBrep()
    
    
    plane = rg.Plane.WorldXY
    plane.Origin = base_pt
    
    z_scale_factor = height / (radius * 2.0)
    
    scale_transform = rg.Transform.Scale(plane, 1.0, 1.0, z_scale_factor)
    drop_brep.Transform(scale_transform)
    
    return drop_brep

if Point and Height:
    
    valid_height = max(0.01, Height)
    a = create_drop_geometry(Point, valid_height)