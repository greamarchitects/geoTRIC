from api.core.pattern import pattric_state
from api.rhino.utils import clear_scene, add_polyline, zoom

clear_scene()
for g in pattric_state(0.25):
    add_polyline(g)
zoom()
