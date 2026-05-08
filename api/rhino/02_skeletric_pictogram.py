from api.core.skeleton import skeletric_state
from api.rhino.utils import clear_scene, add_polyline, zoom

clear_scene()
for g in skeletric_state(1.0):
    add_polyline(g)
zoom()
