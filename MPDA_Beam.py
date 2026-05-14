import Rhino.Geometry as rg
import math

breps = []
frames = []
profiles = []

if crv1 and crv2:

    sections = max(2, int(sections))

    for rail in [crv1, crv2]:

        t_params = rail.DivideByCount(sections, True)

        rects = []

        for i, t in enumerate(t_params):

            pt = rail.PointAt(t)

            success, frame = rail.PerpendicularFrameAt(t)

            if success:

                # torsión progresiva
                angle = math.radians(twist_deg) * (float(i)/(sections-1))

                frame.Rotate(angle, frame.ZAxis, pt)

                rect = rg.Rectangle3d(
                    frame,
                    rg.Interval(-width/2, width/2),
                    rg.Interval(-height/2, height/2)
                )

                rects.append(rect.ToNurbsCurve())
                frames.append(frame)
                profiles.append(rect)

        # Loft entre rectángulos
        loft = rg.Brep.CreateFromLoft(
            rects,
            rg.Point3d.Unset,
            rg.Point3d.Unset,
            rg.LoftType.Normal,
            False
        )

        if loft:
            breps.extend(loft)