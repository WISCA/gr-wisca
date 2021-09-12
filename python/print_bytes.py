#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Jacob Holtom.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class print_bytes(gr.sync_block):
    """
    docstring for block print_bytes
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="print_bytes",
            in_sig=[np.uint8],
            out_sig=None)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        print(bytes(in0))
        return len(input_items[0])
