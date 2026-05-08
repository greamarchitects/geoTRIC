import sys
import bpy

sys.path.append(
    r"C:\Users\ReDI\Documents\GitHub\2026_GREAM\project\local_geoTRIC\geoTRIC"
)

from api.core.grammar import grammatric_state
from api.blender.utils import clear_scene, add_polyline, setup_camera

clear_scene()

for g in grammatric_state(0.35):
    add_polyline(g, "grammatric")

setup_camera()
