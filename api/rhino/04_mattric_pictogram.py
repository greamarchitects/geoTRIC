from api.core.matrix import mattric_state
from api.rhino.utils import clear_scene, add_column, zoom

clear_scene()
for c in mattric_state(0.25):
    add_column(c)
zoom()
