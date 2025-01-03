import numpy as np

def split(a, value, source=None):
    # like str.split, but for arrays
    if source is None:
        source = a
    if np.isnan(value):
        idx = np.where(~np.isnan(source))[0]
    else:
        idx = np.where(source != value)[0]

    return np.split(a[idx],np.where(np.diff(idx)!=1)[0]+1)


def join(sep, items):
    return [i for item in items for i in (item, sep)]


def stack(items, sep):
    return [i for item in items for i in (*item, sep)]


if __name__ == "__main__":
    print(join([1,2], [ [[0,0],[0,0]], [[1,1],[1,1]] ]))

    print(stack([ [[0,0],[0,0]], [[1,1],[1,1]] ],  [5,5]))
