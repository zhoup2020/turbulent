import numpy as np
import pycwt as wavelet
from scipy import signal


def wavelet_calculate(x,dt,dj,J):
    t = np.arange(0, len(x), 1) * dt
    dt = dt
    mother = wavelet.Morlet(6)
    s0 = 2 * dt  # Starting scale, in this case 2 * timestep (default = 0.1 s)
    dj = dj  # The scale resolution
    J = J  # The number of scales

    dat = signal.detrend(x.values, type='linear')
    N = dat.size
    # standardization
    std = dat.std()
    dat_norm = (dat - dat.mean()) / std

    alpha, _, _ = wavelet.ar1(dat_norm)  # Lag-1 autocorrelation for red noise
    wave, scales, freqs, coi, fft, fftfreqs = wavelet.cwt(dat_norm, dt, dj, s0, J, mother)
    power = (np.abs(wave)) ** 2
    fft_power = np.abs(fft) ** 2
    period = 1 / freqs

    power /= scales[:, None]

    signif, fft_theor = wavelet.significance(1.0, dt, scales, 0, alpha,
                                             significance_level=0.95,
                                             wavelet=mother)
    sig95 = np.ones([1, N]) * signif[:, None]
    sig95 = power / sig95

    return period,power,sig95,coi,fft_power
