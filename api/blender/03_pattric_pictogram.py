from api.core.pattern import pattric_state
from api.blender.utils import clear_scene, add_polyline, setup_camera

clear_scene()
for g in pattric_state(0.25):
    add_polyline(g, "pattric", bevel=0.008)
setup_camera()
