from api.core.matrix import mattric_state
from api.blender.utils import clear_scene, add_column, setup_camera

clear_scene()
for c in mattric_state(0.25):
    add_column(c, "mattric")
setup_camera()
