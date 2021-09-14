# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np

def temporal_projection(subspace_signal, data_signal, Ndelays):
    n_samples = len(subspace_signal)
#    if n_samples != data_signal[0].size:
#        print('inputs signals need to be the same number of time samples')
    S = np.zeros((Ndelays+1, n_samples))+1j*np.zeros((Ndelays+1, n_samples))
    if Ndelays == 0:
        S = subspace_signal
        inverse = 1/np.matmul(S, np.conj(np.transpose(S)))
    else:
        S[0, n_samples-1] = 0
        S[0, 0:(n_samples-1)] = subspace_signal[1:n_samples]
        S[1] = subspace_signal
        for ii in range(1, Ndelays):
            S[ii+1, 0:ii] = np.zeros((1, ii))
            S[ii+1, ii:n_samples] = subspace_signal[0:(n_samples-ii)]
    P = np.linalg.lstsq(np.matmul(S, np.conj(np.transpose(S))), S, rcond = None)[0]
    P = np.matmul(np.conj(np.transpose(S)), P)
    Zp = np.matmul(data_signal, P)
    Zrx_proj_block = data_signal - Zp
    return Zrx_proj_block

#test
#sub_re = np.loadtxt('sub_re.csv', delimiter = ",")
#sub_im = np.loadtxt('sub_im.csv', delimiter = ",")
#ds_re = np.loadtxt('ds_re.csv', delimiter = ",")
#ds_im = np.loadtxt('ds_im.csv', delimiter = ",")
#subspace_signal = sub_re + 1j*sub_im
#data_signal = ds_re +1j*ds_im
#Ndelays = 3
#Zrx_proj_block = temporal_projection(subspace_signal, data_signal, Ndelays)