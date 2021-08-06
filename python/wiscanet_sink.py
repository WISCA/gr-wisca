#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Jacob Holtom.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
import socket
import struct
import time

class wiscanet_sink(gr.sync_block):
    """
    docstring for block wiscanet_sink
    """

    tx_udp = None
    UCONTROL_IP = "127.0.0.1"
    TX_PORT = 9940
    data_buffer = []

    def __init__(self, req_num_samps, num_chans, start_time, delay_time, ref_power):
        gr.sync_block.__init__(self,
            name="wiscanet_sink",
            in_sig=[numpy.complex64, ],
            out_sig=None)
        self.req_num_samps = req_num_samps
        self.num_chans = num_chans
        self.start_time = start_time
        self.delay_time = delay_time
        self.ref_power = ref_power
        self.tx_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        if len(self.data_buffer) > 0:
            if len(self.data_buffer) < self.req_num_samps:
                # Continuing filling buffer
                self.data_buffer = numpy.append(self.data_buffer, in0)
            else:
                # We are finally full! Get ready to transmit
                if len(self.data_buffer) > self.req_num_samps:
                    self.data_buffer = self.data_buffer[:self.req_num_samps]
                self.data_buffer = self.data_buffer.reshape(self.req_num_samps, self.num_chans)
                [in_rows, in_cols] = self.data_buffer.shape # Get shape of input
                assert in_rows == self.req_num_samps
                assert in_cols == self.num_chans
                tx_buff = self.data_buffer.reshape(in_rows*in_cols, 1)
                interleaved_tx_buff = numpy.zeros((2*in_rows*in_cols, 1))
                interleaved_tx_buff[::2] = tx_buff.real
                interleaved_tx_buff[1::2] = tx_buff.imag
                # in original right here we do a single(transpose(interleaved_tx_buff))
                print("[Local USRP] Transmitting at %f, %d bytes (%d samples)\n" % (self.start_time, len(interleaved_tx_buff), self.req_num_samps), flush=True)
                byte_buff = interleaved_tx_buff.astype(numpy.single).tobytes()
                total_tx = 0
                tx_len = 0
                tx_unit = 4095
                while (total_tx < len(byte_buff)):
                    if ((len(byte_buff) - total_tx) > tx_unit ):
                        tx_len = tx_unit
                    else:
                        tx_len = len(byte_buff) - total_tx

                    self.tx_udp.sendto(byte_buff[total_tx:tx_len+total_tx], (self.UCONTROL_IP, self.TX_PORT))
                    total_tx = total_tx + tx_len

                self.tx_udp.sendto(bytearray(struct.pack("d",self.start_time)), (self.UCONTROL_IP, self.TX_PORT))
                self.tx_udp.sendto(bytearray(struct.pack("Q",self.num_chans)), (self.UCONTROL_IP, self.TX_PORT))
                self.tx_udp.sendto(bytearray(struct.pack("h",self.ref_power)), (self.UCONTROL_IP, self.TX_PORT))
                self.tx_udp.sendto(b'', (self.UCONTROL_IP, self.TX_PORT))

                while time.time() < self.start_time:
                    time.sleep(200/1000000.0)

                print("[Local USRP] Finished transmitting\n", flush=True)
                self.start_time = self.start_time + self.delay_time
        else:
            # Start building the buffer up from 0
            self.data_buffer = in0
        return len(input_items[0])

