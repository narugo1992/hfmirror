from collections.abc import Mapping, Sequence


def _object_hashable(obj):
    try:
        _ = hash(obj)
        return obj
    except TypeError:
        if isinstance(obj, Mapping):
            items = []
            for key in sorted(obj.keys(), key=repr):
                items.append((_object_hashable(key), _object_hashable(obj[key])))
            return type(obj), tuple(items)
        elif isinstance(obj, Sequence):
            items = [_object_hashable(item) for item in obj]
            return type(obj), tuple(items)
        else:
            return type(obj), id(obj)


def hash_anything(obj):
    return hash(_object_hashable(obj))
