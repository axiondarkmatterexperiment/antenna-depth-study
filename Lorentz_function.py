import numpy as np

# define function to be used in curve fitting
def dip_func(f, dy, Q, f0, C):
    delta = Q*(f - f0)/f0
    return C - dy/(1 + 4*np.square(delta))

def peak_func(f, dy, Q, f0, C):
    delta = Q*(f - f0)/f0
    return C + dy/(1 + 4*np.square(delta))
