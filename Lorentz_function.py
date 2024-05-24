def dip_func(f, dy, Q, f0, C):
    delta = Q*(f - f0)/f0
    return C - dy/(1 + 4*np.square(delta))