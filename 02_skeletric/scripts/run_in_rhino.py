import Rhinoscriptsyntax as rs
from skeletric import bones
from skeletric import derive

def main():
    crvs = bones.get_bones()
    if not crvs:
        rect = bones.make_rectangle_bone(12, 6)
        crvs = [rect]

    spine = crvs[0]
    pts = bones.sample_curve(spine, n=25)

    # Derived geometry
    derive.polyline(pts)
    derive.ribs_along_spine(pts, rib_len=2.5, every=2)
    derive.circles_on_points(pts, radius=0.25, every=4)

main()