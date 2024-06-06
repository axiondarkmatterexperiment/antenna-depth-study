import numpy as np
from scipy.optimize import curve_fit
from Lorentz_function import dip_func, peak_func
from numpy import genfromtxt

def reflection_fit(freq, real_amp, im_amp, phase):

    # turn arrays into numpy arrays
    freq = np.asarray(freq)
    real_amp = np.asarray(real_amp)
    im_amp = np.asarray(im_amp)
    phase = np.asarray(phase)

    # use the real and imaginary components of power to find gamma squared
    gamma_sq = np.add(np.square(real_amp), np.square(im_amp))

    # define a guess for the resonant frequency
    f0_arg = np.argmin(gamma_sq)
    f0 = freq[f0_arg]

    # define a guess for C
    gamma_arg = int(np.round((gamma_sq.size)/3))
    gamma_C = gamma_sq[-gamma_arg:]
    C = np.median(gamma_C)

    # define a guess for delta y
    delta_y = C - np.min(gamma_sq)

    # find bandwidth
    gamma_sq_Q1 = np.abs(gamma_sq[f0_arg:] - (C - delta_y/2))
    gamma_sq[-f0_arg:]
    df1 = freq[np.argmin(gamma_sq_Q1)]
    gamma_sq_Q2 = np.abs(gamma_sq[-f0_arg:] - (C - delta_y/2))
    df2 = freq[np.argmin(gamma_sq_Q2)]
    delta_f = df2 - df1

    # define a guess for Q
    Q = f0/delta_f
    
    # find a fit for delta
    params = [delta_y, Q, f0, C]
    popt, pcov = curve_fit(dip_func, freq, gamma_sq, params)
    
    #determine under- or over-coupling
    slope_sign  = phase[(f0_arg + 3)] - phase[(f0_arg - 3)]

    #calculate beta
    if slope_sign >= 0:
        beta = (1 - np.abs(np.sqrt(gamma_sq[f0_arg])))/(1 + np.abs(np.sqrt(gamma_sq[f0_arg])))
    elif slope_sign < 0:
        beta = (1 + np.abs(np.sqrt(gamma_sq[f0_arg])))/(1 - np.abs(np.sqrt(gamma_sq[f0_arg])))

    return popt, pcov, beta

def transmission_fit(freq, real_amp, im_amp):

    # turn arrays into numpy arrays
    freq = np.asarray(freq)
    real_amp = np.asarray(real_amp)
    im_amp = np.asarray(im_amp)

    # use the real and imaginary components of power to find gamma squared
    gamma_sq = np.add(np.square(real_amp), np.square(im_amp))

    # define a guess for the resonant frequency
    f0_arg = np.argmax(gamma_sq)
    f0 = freq[f0_arg]

    # define a guess for C
    gamma_arg = int(np.round((gamma_sq.size)/3))
    gamma_C = gamma_sq[-gamma_arg:]
    C = np.median(gamma_C)

    # define a guess for delta y
    delta_y = np.max(gamma_sq) - C

    # find bandwidth
    gamma_sq_Q1 = np.abs(gamma_sq[f0_arg:] - (C + delta_y/2))
    gamma_sq[-f0_arg:]
    df1 = freq[np.argmin(gamma_sq_Q1)]
    gamma_sq_Q2 = np.abs(gamma_sq[-f0_arg:] - (C + delta_y/2))
    df2 = freq[np.argmin(gamma_sq_Q2)]
    delta_f = df2 - df1

    # define a guess for Q
    Q = f0/delta_f
    
    # find a fit for delta
    params = [delta_y, Q, f0, C]
    popt, pcov = curve_fit(peak_func, freq, gamma_sq, params)

    return popt, pcov
