from api.core.surface import hiritric_state
from api.rhino.utils import clear_scene, add_column, zoom

clear_scene()
for c in hiritric_state(0.25):
    add_column(c)
zoom()
