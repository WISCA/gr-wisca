# gr-wisca

This is a GNURadio OOT with a bunch of assorted blocks developed at the WISCA Center at ASU.

The WISCANet blocks are found here.
Temporal Mitigation blocks are also found here.
Some Packet Radio/Burst-y blocks are also found here.

## WISCANet Sink/Source Block Notes

- This block is currently limited to 1 channel, as opposed to the N channels Python/MATLAB wiscanet interfaces support.  This is not a technical limitation, just needs a little more code work
- Set start_time to be a GNURadio parameter, and then pass it in on the command line, makes things easy, and the WISCANet runtime will do this

## Temporal Mitigation Block Notes

- Some assumptions are made on the number of channels used, and some assumptions about how burst messages will be passed in.

## Sync and Eq Block

- This block does a very simple cross-correlation with a modulated training sequence and then MMSE equalization using those symbols
- It also chunks out a provided number of symbols
- It is very unoptimized (intentionally)

## MMSE Beamformer

- MMSE Beamformer that synchronizes and beamformers an N (currently just 4) channel receiver and remodulates symbols
- For use with the temporal mitigation block

## Print Bytes

- Just prints the UTF-8 value of the bytes provided on the input stream

## Build Process

- Follow the typical OOT build process for a GR 3.9 block (from the top of the module directory)
- `mkdir build`
- `cd build/`
- `cmake ../`
- `make`
- `sudo make install`
- This can be amended to other install prefixes as necessary (https://wiki.gnuradio.org/index.php/OutOfTreeModules)
