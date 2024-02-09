#VLSB delta format specs:
#Header - ASCII "VDF", 1 byte FPS, 4 bytes frame count (little endian).
#If FPS is 0, each frame is prefixed with the timestamp in milliseconds (4 bytes little endian)
#Each frame starts with the compressed size (2 bytes little endian). If 0, the frame is uncompressed.
#Each compressed frame is made of step-xor pairs. The xor value is optional - if the highest bit of step is 0, it will reuse the last xor value. The position in the frame buffer is stored in the pos value.
#To decode a frame, initialize pos and xor to zero, then repeat the following:
#    Read a byte into step. Add the lower 7 bits to pos. If pos is >= the frame size, break - the frame is done.
#    If the highest bit of step is set, read a byte into xor.
#    Finally, xor the byte at pos with the xor value.

import thumbyGraphics
from time import ticks_ms
from struct import unpack

@micropython.viper
def readframe(framedata):
    data:ptr8 = ptr8(framedata)
    dpos:int = 0
    scr:ptr8 = ptr8(thumbyGraphics.display.display.buffer)
    spos:int = 0
    diff:int = 0
    
    while True:
        spos += data[dpos] & 127
        if spos >= 360: return
        dpos += 1
        if data[dpos-1] & 128:
            diff = data[dpos]
            dpos += 1
        scr[spos] ^= diff


def play(data):
    if data.read(3) != b"VDF":
        print("[SCREENREC] Invalid, unfinished, or corrupt file")
        return
    framerate = ord(data.read(1))
    oldframerate = thumbyGraphics.display.frameRate
    thumbyGraphics.display.setFPS(framerate)
    frames = unpack("<I", data.read(4))[0]
    thumbyGraphics.display.fill(0)
    starttime = ticks_ms()
    
    for frame in range(frames):
        if framerate == 0: frametime = unpack("<I", data.read(4))[0]
        size = unpack("<H", data.read(2))[0]
        if size == 0:
            data.readinto(thumbyGraphics.display.display.buffer)
        else:
            readframe(data.read(size))
        if framerate == 0:
            while frametime > ticks_ms() - starttime: pass
        if thumbyGraphics.buttonA.justPressed(): break
        thumbyGraphics.display.update()
    
    thumbyGraphics.display.setFPS(oldframerate)

