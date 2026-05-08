from api.core.skeleton import skeletric_state
from api.blender.utils import clear_scene, add_polyline, setup_camera

clear_scene()
for g in skeletric_state(1.0):
    add_polyline(g, "skeletric", bevel=0.02)
setup_camera()
