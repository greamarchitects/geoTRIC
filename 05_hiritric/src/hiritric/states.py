# states.py
# Sequential states: the variation the assignment asks to be shown as a
# series. A state is one parameter dictionary (tower shape + rule settings +
# attractor positions); a sequence is that dictionary interpolated between a
# START and an END over n steps. Pure - no Rhino.


def lerp_value(a, b, t):
    """Interpolate a number, or a (nested) list/tuple of numbers - e.g. a list
    of attractor points. Anything else (a string setting) is not interpolable
    and is taken from the START state."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return type(a)(lerp_value(x, y, t) for x, y in zip(a, b))
    return a


def interpolate_params(start, end, t):
    """State at position t (0 = start, 1 = end); keys come from `start`."""
    return {key: lerp_value(value, end.get(key, value), t) for key, value in start.items()}


def build_states(start, end, count):
    """`count` states from start to end inclusive."""
    if count < 1:
        raise ValueError("need at least one state")
    if count == 1:
        return [dict(start)]
    return [interpolate_params(start, end, k / (count - 1)) for k in range(count)]
