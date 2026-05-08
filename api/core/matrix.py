import math
from .geometry import Column

def mattric_state(t=0.0, n=16):
    columns = []
    center = n / 2
    for i in range(n):
        for j in range(n):
            x = (i - center) * 0.45
            y = (j - center) * 0.45
            d = math.sqrt((i - center)**2 + (j - center)**2)
            h = max(0.12, 2.5 - d * 0.18 + math.sin(t * 6.28 + d) * 0.25)
            columns.append(Column(x, y, h, 0.08))
    return columns
