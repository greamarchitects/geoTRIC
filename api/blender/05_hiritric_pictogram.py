from api.core.surface import hiritric_state
from api.blender.utils import clear_scene, add_column, setup_camera

clear_scene()
for c in hiritric_state(0.25):
    add_column(c, "hiritric")
setup_camera()
