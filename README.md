# gr-wisca

This is a GNURadio OOT with a bunch of assorted blocks developed at the WISCA Center at ASU.

The WISCANet blocks are found here.
Temporal Mitigation blocks are also found here.
Some Packet Radio/Burst-y blocks are also found here.

## WISCANet Block Notes

- This block is currently limited to 1 channel, as opposed to the N channels Python/MATLAB wiscanet interfaces support.  This is not a technical limitation, just needs a little more code work
- Set start_time to be a GNURadio parameter, and then pass it in on the command line, makes things easy, and the WISCANet runtime will do this

## Temporal Mitigation Block Notes

- Some assumptions are made on the number of channels used, and some assumptions about how burst messages will be passed in.
