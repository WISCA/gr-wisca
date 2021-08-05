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

class wiscanet_source(gr.sync_block):
    """
    docstring for block wiscanet_source
    """

    rx_udp_con = None
    rx_udp = None
    UCONTROL_IP = "127.0.0.1"
    RX_PORT = 9944
    RX_PORTCON = 9945


    def __init__(self, req_num_samps, num_chans, start_time, delay_time):
        gr.sync_block.__init__(self,
            name="wiscanet_source",
            in_sig=None,
            out_sig=[numpy.complex64, ])
        self.req_num_samps = req_num_samps
        self.num_chans = num_chans
        self.start_time = start_time
        self.delay_time = delay_time
        self.data_buffer = []
        print("Connecting Receive Controller (Ports: 9944, 9945)\n", flush=True)
        self.rx_udp_con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx_udp.bind((self.UCONTROL_IP, self.RX_PORT))


    def work(self, input_items, output_items):
        out = output_items[0]
        out_len = len(output_items[0])
        if len(self.data_buffer) > 0:
            if len(self.data_buffer) < out_len:
                temp = numpy.zeros(out_len,numpy.complex64)
                temp[:len(self.data_buffer)] = self.data_buffer
                self.data_buffer = []
            else:
                out[:] = self.data_buffer[:out_len]
                self.data_buffer = self.data_buffer[out_len:]
        else:
            print("[Local USRP] Receiving at %f for %d channels\n" % (self.start_time, self.num_chans), flush=True)
            # Control Receive (aka send the self.start_time)
            self.rx_udp_con.sendto(bytearray(struct.pack("dd",self.start_time,0)), (self.UCONTROL_IP, self.RX_PORTCON)) # This has to send that zeroed second buffer, because the uControl/MEX version is sloppy
            self.rx_udp_con.sendto(bytearray(struct.pack("H",self.num_chans)), (self.UCONTROL_IP, self.RX_PORTCON))
            rx_unit = 4000*2
            input_len = self.num_chans * self.req_num_samps * 4
            buf_pos = 0
            byte_buff = bytearray()
            while True:
                readlen = input_len - buf_pos
                if (readlen > 0):
                    (temp_buff,_) = self.rx_udp.recvfrom(rx_unit)
                    retval = len(temp_buff)
                    byte_buff.extend(bytearray(temp_buff))
                    if (retval == 0):
                        print("[Local USRP] Completed one receiving cycle\n", flush=True)

                readlen = retval if retval > 0 else 0
                buf_pos = buf_pos + readlen

                if (buf_pos >= input_len):
                    break

            rx_buff = numpy.frombuffer(byte_buff,numpy.short)
            rx_buff_scaled = rx_buff / 2**15
            rx_buff_complex = rx_buff_scaled[::2] + rx_buff_scaled[1::2] * 1j
            self.data_buffer = rx_buff_complex.reshape((self.req_num_samps, self.num_chans)).flatten() # This only allows it to work for one dimension (1 channel for now)
            print("[Local USRP] Finished receiving %d complex samples at time %f\n" % (len(rx_buff), self.start_time), flush=True)
            out[:] = self.data_buffer[:out_len]
            self.data_buffer = self.data_buffer[out_len:]
            self.start_time = self.start_time + self.delay_time # Increment start_time by appropriate delay
        return out_len
