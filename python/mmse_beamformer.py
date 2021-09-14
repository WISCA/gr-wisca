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
from gnuradio import gr
import pmt
import queue

class mmse_beamformer(gr.basic_block):
    """
    docstring for block mmse_beamformer
    """

    def __init__(self, training_symbols, psf_taps, sps):
        gr.basic_block.__init__(self,
            name="mmse_beamformer",
            in_sig=None,
            out_sig=None)
        self.training_symbols = training_symbols
        self.psf_taps = psf_taps
        self.sps = sps
        self.burst_q = [queue.Queue(), queue.Queue(), queue.Queue(), queue.Queue()]
        self.message_port_register_in(pmt.intern('bursts'))
        self.message_port_register_out(pmt.intern('est_symbols'))
        self.set_msg_handler(pmt.intern('bursts'), self.handle_msg)

    def handle_msg(self, msg):
        info_dict = pmt.to_python(pmt.car(msg))
        rfData = pmt.to_python(pmt.cdr(msg))
        # Basically place the rfData into the correct queue
        chan = int(info_dict['channel'])-1
        self.burst_q[chan].put(rfData)
        # Check if all queues have a data thing to use
        if all([not q.empty() for q in self.burst_q]):
            # We got all channels here! whooo!
            # Use the data thing to do MMSE beamformer
            s_trn = np.asarray(self.training_symbols, np.complex64)
            trn_l = len(s_trn)
            z_trn = np.ndarray((4,trn_l), np.complex64)
            for i in range(0,len(self.burst_q)):
                d = self.burst_q[i].get()
                (rxF, _, _) = time_align(d, self.psf_taps, self.training_symbols, self.sps, trn_l)
                (rxM, _) = mmse_equalizer(rxF, s_trn, rxF, 15, 0)
                z_trn[i] = rxM
            # Output estimated symbols
            w = np.matmul(la.inv(np.matmul(z_trn,z_trn.T.conj())),np.matmul(z_trn,s_trn.T.conj()))
            rxEq = np.matmul(w.T.conj(),z_trn)
            # Demodulate BPSK (initial phase rotation of pi in MATLAB)
            rxBits = rxEq > 0
            # Remodulate - same logic as above
            modSyms = (rxBits-0.5)*2;
            remodSyms = sig.upfirdn(self.psf_taps, modSyms, self.sps, 1)
            #savemat('/home/jholtom/test_mmse_bf.mat',{'rxMMSE': rxEq, 'z_trn': z_trn, 's_trn': s_trn})
            outInfo = pmt.to_pmt({'frame_len': len(remodSyms)})
            outData = pmt.to_pmt(remodSyms.astype(np.csingle))
            rxOut = pmt.cons(outInfo, outData)
            self.message_port_pub(pmt.intern('est_symbols'), rxOut)

def time_align(rxSig, rrcosFilter, trSyms, sps, nTotalSyms):
    rxSigFiltered = sig.upfirdn(rrcosFilter, rxSig, 1, sps)
    xc = np.correlate(rxSigFiltered,np.pad(trSyms,(0,len(rxSigFiltered)-len(trSyms))),'full')
    lag = np.arange(-np.floor(len(xc)/2),np.floor(len(xc)/2))
    maxIdx = np.argmax(np.abs(xc))
    timingOffsetEstimate = int(lag[maxIdx])
    rxTimeCorrected = rxSigFiltered[timingOffsetEstimate:nTotalSyms+timingOffsetEstimate]
    phaseOffsetEstimate = np.angle(xc[maxIdx])
    #rxPhaseCorrected = np.exp(-1j*phaseOffsetEstimate) * rxTimeCorrected
    return (rxTimeCorrected,timingOffsetEstimate,phaseOffsetEstimate)

def mmse_equalizer(msgSyms, trnSyms, rxTrn, eqLen, eqDelay):
    R = la.toeplitz(np.concatenate(([rxTrn[0]], np.zeros(eqLen-1))),rxTrn)
    Sd = np.concatenate((np.zeros(eqDelay), trnSyms[0:len(trnSyms)-eqDelay]))
    Sd = np.reshape(Sd,(1,len(Sd)))
    epsilon_load = 10e-6
    w = np.matmul(np.matmul(Sd,R.T.conj()),la.inv(np.matmul(R,R.T.conj()) + epsilon_load*np.eye(eqLen)))
    s_hat = sig.lfilter(w.flatten(),1,msgSyms)
    return (s_hat, w.flatten())
