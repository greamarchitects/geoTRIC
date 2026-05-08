import bpy

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def add_polyline(polyline, name="polyline", bevel=0.015):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    spl = curve.splines.new("POLY")
    spl.points.add(len(polyline.points) - 1)

    for p, co in zip(spl.points, polyline.points):
        p.co = (co[0], co[1], co[2], 1)

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return obj

def add_column(column, name="column"):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=column.radius,
        depth=column.height,
        location=(column.x, column.y, column.height / 2)
    )
    bpy.context.object.name = name
    return bpy.context.object

def setup_camera():
    bpy.ops.object.light_add(type="AREA", location=(0, -4, 6))
    bpy.context.object.data.energy = 350
    bpy.context.object.data.size = 5

    bpy.ops.object.camera_add(location=(0, -8, 6), rotation=(1.05, 0, 0))
    bpy.context.scene.camera = bpy.context.object

    bpy.context.scene.render.resolution_x = 900
    bpy.context.scene.render.resolution_y = 900
