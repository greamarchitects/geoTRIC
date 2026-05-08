import math
from .geometry import Column

def hiritric_state(t=0.0, n=28):
    columns = []
    center = n / 2
    for i in range(n):
        for j in range(n):
            x = (i - center) * 0.28
            y = (j - center) * 0.28
            d1 = math.sqrt((x - 1.2)**2 + (y - 1.0)**2)
            d2 = math.sqrt((x + 1.6)**2 + (y + 0.8)**2)
            h = 3.8 * math.exp(-d1 * 0.85) + 1.8 * math.exp(-d2 * 0.55)
            h += math.sin(t * 6.28 + d1 * 2) * 0.25
            columns.append(Column(x, y, max(0.05, h), 0.055))
    return columns
