"""
This test uses another module I wrote for dynamics that is not yet open source.
Sorry!
"""
import numpy as np

from spectra.bath import DebyeBath
from spectra.convolve import pulse_amp_fit
from spectra.constants import CM_K, CM_FS
from spectra.hamiltonian import Hamiltonian, ElectronicHamiltonian
from spectra.nonlinear_response import greens_function, nonlinear_response
from spectra.pulse import GaussianPulse

from convolve import *
from spectroscopy import *

# params (other than bath) from
# Yuen-Zhou et al., PNAs 108, (2011).
H2 = np.array([[12881, 120], [120, 12719]])
d2 = np.array([[1, 0, 0], [2 * np.cos(.3), 2 * np.sin(.3), 0]])
hamiltonian = Hamiltonian(ElectronicHamiltonian(H2, disorder_fwhm=100.0),
                          DebyeBath(CM_K * 300, 35, 106), d2)

rw_freq = hamiltonian.system.central_freq

# evaluate
G = greens_function(hamiltonian, 1000, piecewise=False)
R_PE = nonlinear_response(G, hamiltonian, direction=(-1, 1, 1))
R_NR = nonlinear_response(G, hamiltonian, direction=(1, -1, 1))
R_c = combine_NR_PE(R_NR, R_PE)

pulse = GaussianPulse(fwhm=40, carrier_freq=rw_freq)
pulse_vec = ControlField(pulse_amp_fit(pulse, G.ticks, normalize=True))
E_all = [pulse_vec, pulse_vec, pulse_vec]

P3 = R3_to_P3(R_c, E_all)
R3 = R3_resize(R_c, E_all)

R_PE = select_PE(R3)
R_NR = select_NR(R3)

P_PE = select_PE(P3)
P_NR = select_NR(P3)

P_2D = fft_2D(P3, freq_bounds=(12300, 13300))
R_2D = fft_2D(R3, freq_bounds=(12300, 13300))

P_PE_2D = fft_2D(P_PE, freq_bounds=(12300, 13300))
R_PE_2D = fft_2D(R_PE, freq_bounds=(12300, 13300))

P_NR_2D = fft_2D(P_NR, freq_bounds=(12300, 13300))
R_NR_2D = fft_2D(R_NR, freq_bounds=(12300, 13300))

freq_weights = np.array([np.sum(pulse_vec[:]
								* np.exp(1j * CM_FS * (f - rw_freq)
                                         * pulse_vec.vec.ticks))
                     	 for f in P_2D.ticks[0]])

P_2D_w = reweight_R3(R_2D, freq_weights)
P_PE_2D_w = reweight_R3(R_PE_2D, freq_weights)
P_NR_2D_w = reweight_R3(R_NR_2D, freq_weights)

alpha, beta = np.argmin(np.abs(R_2D.ticks[0].reshape(1, -1)
							   - hamiltonian.system.E('e').reshape(-1, 1)), 1)


S3_forward_ones = R3_to_P3(np.ones_like(R_c), E_all, shortcut=True)
S3_backward_ones = unshift_time_indices(
    P3_unsize(np.ones_like(P3), R_c.shape, E_all), E_all)

