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
from struct import pack, unpack

writefile = None
framerate = 0
numframes = 0
lastframe = None
starttime = None
streambuf = None


#buf is a file-like object opened for binary writing
#fps is the playback framerate. If 0, a variable framerate is used.
def init(buf, fps=0, start=None):
    global writefile, framerate, lastframe, streambuf, starttime, numframes
    writefile = buf
    framerate = fps
    numframes = 0
    lastframe = bytearray(360)
    streambuf = bytearray(768) #725 (360*2+5) is the largest compressed frame size, assuming no bugs
    if start == None:
        starttime = ticks_ms()
    
    writefile.write(b"\0\0\0") #VDF placeholder
    writefile.write(chr(fps))
    writefile.write(b"\0\0\0\0") #frame count placeholder
    print("[SCREENREC] Started recording")


@micropython.viper
def _addframe() -> int:
    scr:ptr8 = ptr8(thumbyGraphics.display.display.buffer)
    old:ptr8 = ptr8(lastframe)
    spos:int = 0
    
    buf:ptr8 = ptr8(streambuf)
    bpos:int = 0
    
    delta:int = 0
    lastdiff:int = 0
    diff:int = 0
    
    while spos < 360:
        if old[spos] != scr[spos]:
            diff = old[spos] ^ scr[spos]
            while delta > 127:
                buf[bpos] = 255 #add a dummy step if delta is too large
                bpos += 1
                buf[bpos] = 0
                bpos += 1
                delta -= 127
                lastdiff = 0
            if diff == lastdiff:
                buf[bpos] = delta
                bpos += 1
            else:
                buf[bpos] = delta | 128
                bpos += 1
                buf[bpos] = diff
                bpos += 1
                lastdiff = diff
            delta = 0
        delta += 1
        
        old[spos] = scr[spos]
        spos += 1
    
    while delta > 127: #get to the end of the frame
        buf[bpos] = 255 #add a dummy step if delta is too large
        bpos += 1
        buf[bpos] = 0
        bpos += 1
        delta -= 127
    buf[bpos] = delta
    bpos += 1
    
    return bpos


#if using a variable framerate (fps is 0), t is the time in milliseconds of the frame.
#when fps is 0 and t is None, it uses the current real time since recording started.
def addframe(t=None):
    global numframes
    numframes += 1
    if framerate == 0:
        if t == None: t = ticks_ms() - starttime
        writefile.write(pack("<I", t))
    compsize = _addframe()
    if compsize < 360:
        writefile.write(pack("<H", compsize))
        writefile.write(memoryview(streambuf)[:compsize])
    else:
        writefile.write(b"\0\0")
        writefile.write(lastframe)


def finish():
    writefile.seek(4)
    writefile.write(pack("<I", numframes))
    writefile.seek(0)
    writefile.write(b"VDF") #write this last as an indication the video was saved properly
    print("[SCREENREC] Finished recording")


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
        if thumbyGraphics.buttonA.justPressed(): return
        thumbyGraphics.display.update()
    
    thumbyGraphics.display.setFPS(oldframerate)


