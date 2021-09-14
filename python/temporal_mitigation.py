#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 ASU.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class temporal_mitigation(gr.sync_block):
    """
    docstring for block temporal_mitigation
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="temporal_mitigation",
            in_sig=[np.complex64, np.complex64, np.complex64, np.complex64, ],
            out_sig=[np.complex64, ])


    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        # <+signal processing here+>
        out[:] = in0
        return len(output_items[0])
