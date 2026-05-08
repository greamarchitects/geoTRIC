import rhinoscriptsyntax as rs

def clear_scene():
    objs = rs.AllObjects()
    if objs:
        rs.DeleteObjects(objs)

def add_polyline(polyline):
    return rs.AddPolyline(polyline.points)

def add_column(column):
    return rs.AddCylinder((column.x, column.y, 0), column.height, column.radius)

def zoom():
    rs.Command("_Zoom _Extents")
