#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 ASU.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
import scipy.linalg as la
import scipy.signal as sig
from scipy.io import savemat
from gnuradio import gr
import pmt
import queue


class temporal_mitigation(gr.sync_block):
    """
    docstring for block temporal_mitigation
    """
    def __init__(self, ndelays):
        gr.sync_block.__init__(self,
                               name="temporal_mitigation",
                               in_sig=None,
                               out_sig=None)

        self.burst_q = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]
        self.est_symbols = queue.Queue()
        self.ndelays = ndelays
        self.message_port_register_in(pmt.intern('bursts'))
        self.message_port_register_in(pmt.intern('mitigation_syms'))
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.set_msg_handler(pmt.intern('bursts'), self.handle_msg)
        self.set_msg_handler(pmt.intern('mitigation_syms'), self.handle_est_syms)

    def handle_msg(self, msg):
        info_dict = pmt.to_python(pmt.car(msg))
        rfData = pmt.to_python(pmt.cdr(msg))
        # Place rfData into the correct queue
        chan = int(info_dict['channel'])-1
        self.burst_q[chan].put(rfData)
        # Check if all queues have a data thing to use
        if all([not q.empty() for q in self.burst_q]) and not self.est_symbols.empty():
            remodSyms = self.est_symbols.get()
            trn_l = len(remodSyms)
            z_rf = np.ndarray((4,trn_l), np.complex64)
            for i in range(0,len(self.burst_q)):
                d = self.burst_q[i].get()
                z_trn[i] = d
            rxProj = temporal_projection(remodSyms, z_rf, self.ndelays) 
            outInfo = pmt.to_pmt({'frame_len': len(rxProj)})
            outData = pmt.to_pmt(rxProj.astype(np.csingle))
            rxOut = pmt.cons(outInfo, outData)
            self.message_port_pub(pmt.intern('pdu_out'), rxOut)

    def handle_est_syms(self, msg):
        info_dict = pmt.to_python(pmt.car(msg))
        rfData = pmt.to_python(pmt.cdr(msg))
        self.est_symbols.put(rfData)

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
