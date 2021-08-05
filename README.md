# gr-wisca

This is a set of GNURadio blocks to interface with existing WISCANet tooling

## WISCANet Source

- This block is currently limited to 1 channel, as opposed to the N channels Python/MATLAB wiscanet interfaces support.  This is not a technical limitation, just needs a little more code work
- Set start_time to be a GNURadio parameter, and then pass it in on the command line, makes things easy, and the WISCANet runtime will do this
