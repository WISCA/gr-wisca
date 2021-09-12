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
import threading
import pmt

class wiscanet_source(gr.basic_block):
    """
    docstring for block wiscanet_source
    """

    rx_udp_con = None
    rx_udp = None
    UCONTROL_IP = "127.0.0.1"
    RX_PORT = 9944
    RX_PORTCON = 9945
    rx_thread = None

    def __init__(self, req_num_samps, num_chans, start_time, delay_time, ncycles):
        gr.basic_block.__init__(self,
            name="WISCANet Source",
            in_sig=None,
            out_sig=None)
        self.req_num_samps = req_num_samps
        self.num_chans = num_chans
        self.start_time = start_time
        self.delay_time = delay_time
        self.ncycles = ncycles
        self.data_buffer = []
        print("Connecting Receive Controller (Ports: 9944, 9945)\n", flush=True)
        self.rx_udp_con = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx_udp.bind((self.UCONTROL_IP, self.RX_PORT))
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.rx_thread = threading.Thread(target=self.rx_data, args=())

    def start(self):
        self.rx_thread.start()
        return True

    def stop(self):
        self.rx_thread.join()
        return True

    def rx_data(self):
        for i in range(0, self.ncycles):
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
            outInfo = pmt.make_dict()
            outData = pmt.to_pmt(self.data_buffer.astype(numpy.csingle))
            rxOut = pmt.cons(outInfo, outData)
            self.message_port_pub(pmt.intern('pdu_out'), rxOut)
            self.start_time = self.start_time + self.delay_time # Increment start_time by appropriate delay
