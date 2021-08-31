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
import pmt

class wiscanet_sink(gr.sync_block):
    """
    docstring for block wiscanet_sink
    """

    tx_udp = None
    UCONTROL_IP = "127.0.0.1"
    TX_PORT = 9940
    data_buffer = []
    burst_len = 0
    ramp_offset = 10000
    txReady = False

    def __init__(self, req_num_samps, num_chans, start_time, delay_time, ref_power, ramp_offset):
        gr.sync_block.__init__(self,
                               name="wiscanet_sink",
                               in_sig=[numpy.complex64, ],
                               out_sig=None)
        self.req_num_samps = req_num_samps
        self.num_chans = num_chans
        self.start_time = start_time
        self.delay_time = delay_time
        self.ref_power = ref_power
        self.ramp_offset = ramp_offset
        self.tx_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def work(self, input_items, output_items):
        in0 = input_items[0]
        len0 = len(input_items[0])
        tags = self.get_tags_in_window(0,0,len0)

        for tag in tags:
            key = pmt.to_python(tag.key)
            if key == 'packet_len':
                self.burst_len = pmt.to_python(tag.value)

        print("Burst Length: " + str(self.burst_len))
        print("Input Sample Length: " + str(len0))
        print("Current Data Buffer Length: " + str(len(self.data_buffer)))

        # If the burst_len isn't provided in a tag, fall back to the strategy of filling with req_num_samps from a streaming set of samples
        if self.burst_len == 0:
            self.burst_len = self.req_num_samps
            print("Going to wait for ReqNumSamps")

        # If the there are fewer samples than the tag, append like we did before
        if len0 < self.burst_len:
            self.data_buffer = numpy.append(self.data_buffer, in0)
            print("Appended to buffer")

        # If we have the full thing, handle it, pack it and send
        if len0 == self.burst_len:
            prefix  = numpy.zeros((self.ramp_offset,1))
            postfix = numpy.zeros((self.req_num_samps-self.burst_len-self.ramp_offset,1))
            self.data_buffer = numpy.append(numpy.append(prefix, in0), postfix)
            self.txReady = True
            print("Ready to send!")

        # If we hit the full thing for a burst, wrap it up, pack it and send
        if len(self.data_buffer) == self.burst_len:
            prefix = numpy.zeros((self.ramp_offset,1))
            postfix = numpy.zeros((self.req_num_samps-self.burst_len-self.ramp_offset,1))
            self.data_buffer = numpy.append(numpy.append(prefix, self.data_buffer), postfix)
            self.txReady = True
            print("Ready to send!")

        # If the buffer is too long, truncate it
        if len(self.data_buffer) > self.req_num_samps:
            self.data_buffer = self.data_buffer[:self.req_num_samps]

        # We are finally full! Get ready to transmit
        if self.txReady:
            self.data_buffer = self.data_buffer.reshape(self.req_num_samps, self.num_chans)
            [in_rows, in_cols] = self.data_buffer.shape # Get shape of input
            assert in_rows == self.req_num_samps
            assert in_cols == self.num_chans
            tx_buff = self.data_buffer.reshape(in_rows*in_cols, 1)
            interleaved_tx_buff = numpy.zeros((2*in_rows*in_cols, 1))
            interleaved_tx_buff[::2] = tx_buff.real
            interleaved_tx_buff[1::2] = tx_buff.imag
            # in original right here we do a single(transpose(interleaved_tx_buff))
            print("[Local USRP] Transmitting at %f, %d bytes (%d samples)\n" % (start_time, len(interleaved_tx_buff), self.req_num_samps), flush=True)
            byte_buff = interleaved_tx_buff.astype(np.single).tobytes()
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

            self.tx_udp.sendto(bytearray(struct.pack("d",start_time)), (self.UCONTROL_IP, self.TX_PORT))
            self.tx_udp.sendto(bytearray(struct.pack("Q",num_chans)), (self.UCONTROL_IP, self.TX_PORT))
            self.tx_udp.sendto(bytearray(struct.pack("h",ref_power)), (self.UCONTROL_IP, self.TX_PORT))
            self.tx_udp.sendto(b'', (self.UCONTROL_IP, self.TX_PORT))

            while time.time() < start_time:
                time.sleep(200/1000000.0)

            time.sleep(0.2)
            print("[Local USRP] Finished transmitting\n", flush=True)

            self.start_time = self.start_time + self.delay_time
            self.data_buffer = []
            self.burst_len = 0

        return len0
