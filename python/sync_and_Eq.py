#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Jacob Holtom.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
import scipy.signal as sig
import scipy.linalg as la
from scipy.io import savemat
import numpy
from gnuradio import gr
import pmt

class sync_and_Eq(gr.basic_block):
    """
    docstring for block sync_and_Eq
    """
    def __init__(self, psf_taps, access_code, eq_len, frame_size, sps):
        gr.basic_block.__init__(self,
            name="Sync and Equalize",
            in_sig=None,
            out_sig=None)
        self.psf_taps = psf_taps
        self.access_code = access_code
        self.eq_len = eq_len
        self.frame_size = frame_size
        self.sps = sps

        self.message_port_register_out(pmt.intern('pdu_out'))
        self.message_port_register_in(pmt.intern('pdu_in'))
        self.set_msg_handler(pmt.intern('pdu_in'), self.handle_msg)

    def handle_msg(self, msg):
        # Process Synchronization and Eq here
        info_dict = pmt.car(msg)
        rfData = pmt.to_python(pmt.cdr(msg))
        (rxTC, tEst, pEst) = time_align(rfData, self.psf_taps, self.access_code, self.sps, self.frame_size)
        (rxEq, _) = mmse_equalizer(rxTC, self.access_code, rxTC[0:len(self.access_code)], self.eq_len, 0)
        outInfo = pmt.to_pmt({'frame_len': len(rxEq)})
        outData = pmt.to_pmt(rxEq.astype(np.csingle))
        rxOut = pmt.cons(outInfo, outData)
        self.message_port_pub(pmt.intern('pdu_out'), rxOut)

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
