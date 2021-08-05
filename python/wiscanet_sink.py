#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Jacob Holtom.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class wiscanet_sink(gr.sync_block):
    """
    docstring for block wiscanet_sink
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="wiscanet_sink",
            in_sig=[numpy.complex64, ],
            out_sig=None)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        return len(input_items[0])

