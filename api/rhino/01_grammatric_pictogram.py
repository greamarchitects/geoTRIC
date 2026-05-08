from api.core.grammar import grammatric_state
from api.rhino.utils import clear_scene, add_polyline, zoom

clear_scene()
for g in grammatric_state(0.35):
    add_polyline(g)
zoom()
