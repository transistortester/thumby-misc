import time
import thumby
import math

import machine
machine.freq(125000000)

thumby.display.setFPS(50)

screen = bytearray(72*40)
dithermask = bytearray(open("/Games/3Dtest/mask.bin", "rb").read())

#tx1, tx2, ty, bx1, bx2, by, shade brightness, shade timing, shade intensity
polygons = [
[-136, 136, -225, -136, 136, 225, 130, 0, 64], #face
[-75, 75, -167, -75, 75, -56, 50, 0, 32], #screen
[-78, -40, 12, -78, -40, 112, 50, 0, 32], #dpad vertical
[-109, -9, 43, -109, -9, 80, 50, 0, 32], #dpad horizontal
[37, 56, 51, 25, 67, 63, 50, 0, 32], #B top
[25, 67, 63, 25, 67, 82, 50, 0, 32], #B middle
[25, 67, 82, 37, 56, 93, 50, 0, 32], #B bottom
[83, 102, 21, 71, 113, 33, 50, 0, 32], #A top
[71, 113, 33, 71, 113, 52, 50, 0, 32], #A middle
[71, 113, 52, 83, 102, 63, 50, 0, 32], #A bottom
[-136, 136, 225, -136, 136, -225, 130, math.pi, 64], #back
]
for poly in polygons:
    for coord in range(6):
        poly[coord] /= 225.0 #scale down to fit in -1.0 to 1.0


@micropython.viper
def ditherscreen(offset:int):
    display = ptr8(thumby.display.display.buffer)
    mask = ptr8(dithermask)
    scr = ptr8(screen)
    index:int = 0
    bufpos:int = 0
    bit:int = 1
    x:int = 0
    y:int = 0
    
    for index in range(72*40//8):
        display[index] = 0 #clear screen
    
    index = 0
    for y in range(40):
        bit = 1 << (y & 7)
        bufpos = (y >> 3) * 72
        for x in range(72):
            if scr[index] > mask[index + offset]: display[bufpos + x] |= bit
            index += 1

@micropython.viper
def ditherscreen_white(offset:int): #optimized for mainly white screens
    display = ptr8(thumby.display.display.buffer)
    mask = ptr8(dithermask)
    scr = ptr8(screen)
    index:int = 0
    bufpos:int = 0
    bit:int = 1
    x:int = 0
    y:int = 0
    
    for index in range(72*40//8):
        display[index] = 255 #clear screen
    
    index = 0
    for y in range(40):
        bit = (1 << (y & 7)) ^ 255
        bufpos = (y >> 3) * 72
        for x in range(72):
            if scr[index] <= mask[index + offset]: display[bufpos + x] &= bit
            index += 1


@micropython.viper
def fillscreen(fill:int):
    scr = ptr8(screen)
    i:int = 0
    for i in range(72*40):
        scr[i] = fill


@micropython.viper
def fquad(tx1:int, tx2:int, ty:int, bx1:int, bx2:int, by:int, fill:int): #draws a quad with flat top and bottom
    scr = ptr8(screen)
    bufpos:int = 0
    left:int = 0
    right:int = 0
    xpos:int = 0
    ypos:int = 0
    
    if tx1 > tx2: #ensure all points are oriented correctly, just in case
        tx1, tx2 = tx2, tx1
    if bx1 > bx2:
        bx1, bx2 = bx2, bx1
    if ty > by:
        tx1, bx1 = bx1, tx1 #viper has an (undocumented?) limit of 3 vars in these expressions before things break
        tx2, bx2 = bx2, tx2
        ty, by = by, ty#tx1, tx2, ty, bx1, bx2, by = bx1, bx2, by, tx1, tx2, ty
    
    if ty == by: #straight horizontal line
        if tx1 < bx1: left = tx1
        else: left = bx1
        if tx2 > bx2: right = tx2
        else: right = bx2
        if ty < 0 or ty >= 40 or right < 0 or left >= 72: return #entirely off-screen
        if left < 0: left = 0 #clamp to screen
        if right >= 72: right = 71
        bufpos = ty * 72
        for xpos in range(left, right+1, 1):
            scr[bufpos+xpos] = fill
        return
    
    increment1:int = 1 #set up all constants needed during the loop
    increment2:int = 1
    xdelta1:int = bx1 - tx1 #this uses a cut-down naive run-length slice algorithm for the edges
    xdelta2:int = bx2 - tx2
    if xdelta1 < 0:
        xdelta1 = 0 - xdelta1
        increment1 = -1
    if xdelta2 < 0:
        xdelta2 = 0 - xdelta2
        increment2 = -1
    ydelta:int = by - ty
    stepsize1:int = xdelta1 // ydelta * increment1 #Bresenham's would be cheaper but need more special cases
    stepsize2:int = xdelta2 // ydelta * increment2
    adderror1:int = (xdelta1 % ydelta) << 2
    adderror2:int = (xdelta2 % ydelta) << 2
    suberror:int = ydelta << 2
    error1:int = (adderror1 >> 2) - suberror
    error2:int = (adderror2 >> 2) - suberror
    
    x1:int = tx1
    x2:int = tx2
    runlength:int = 0
    
    for ypos in range(ty, by+1, 1):
        if ypos >= 40: return #don't draw off-screen
        
        runlength = stepsize1 #advance left edge
        error1 += adderror1
        if error1 > 0:
            runlength += increment1
            error1 -= suberror
        left = x1
        x1 += runlength
        
        runlength = stepsize2 #advance right edge
        error2 += adderror2
        if error2 > 0:
            runlength += increment2
            error2 -= suberror
        right = x2
        x2 += runlength
        
        if ypos < 0: continue #lazily skip over off-screen section
        
        if left < 0: left = 0 #clamp to screen
        if right >= 72: right = 71
        bufpos = ypos * 72
        for xpos in range(left, right+1, 1):
            scr[bufpos+xpos] = fill


@micropython.viper
def drawfloor_fixedpoint(x:int, y:int, z:int): #this uses 24.8 bit fixed point numbers
    scr = ptr8(screen)
    bufpos:int = 0
    xpos:int = 0
    ypos:int = 0
    gridz:int = 0
    gridx:int = 0
    depth:int = 0
    
    for gridz in range(10):
        depth = 65536 // z #equivalent to depth = 1.0 / z
        ypos = (((y * depth) >> 8) * 40 >> 8) + 20  #equivalent to ypos = y * depth * 40 + 40 / 2
        z -= 256
        if ypos < 0 or ypos >= 40: continue
        bufpos = 72 * ypos
        for gridx in range(-10*256, 10*256, 1*256):
            xpos = (x + gridx) * depth // 256 * 40 // 256 + 36 #not bitshifting because of negatives
            if 0 <= xpos < 72:
                scr[bufpos+xpos] = 0

def drawfloor(gpos): #preps vars for drawing - wrangling viper into doing this step is more effort than it's worth
    x = int(gpos[0] % 1 * 256)
    y = int((gpos[1] + 2) * 256) #draw grid 2 units below 0
    z = int(gpos[2] % 1 * 256) + 10*256# + max(0, int(gpos[1]*3)*256)
    drawfloor_fixedpoint(x, y, z)


gpos = [0.0,0.0,3.0]
frames = 0
nexttime = time.ticks_ms()
while True: #all of this is temporary for testing
    rot = time.ticks_ms() / 1000.0 * math.pi * 2 / 3
    fillscreen(255)
    
    if thumby.buttonU.pressed(): gpos[2] -= 0.1
    if thumby.buttonD.pressed(): gpos[2] += 0.1
    if thumby.buttonL.pressed(): gpos[0] += 0.1
    if thumby.buttonR.pressed(): gpos[0] -= 0.1
    if thumby.buttonB.pressed(): gpos[1] -= 0.1
    if thumby.buttonA.pressed(): gpos[1] += 0.1
    
    drawfloor(gpos)
    
    sin, cos = math.sin(rot), math.cos(rot)
    
    for poly in polygons:
        ztop = sin * poly[2]
        depth = 1.0 / max(ztop + gpos[2], 0.1)
        xs1top = int((poly[0]+gpos[0])*depth*40+72/2)
        xs2top = int((poly[1]+gpos[0])*depth*40+72/2)
        ystop = int((cos*poly[2]+gpos[1])*depth*40+40/2)
        zbot = sin*poly[5]
        depth = 1.0 / max(zbot + gpos[2], 0.1)
        xs1bot = int((poly[3]+gpos[0])*depth*40+72/2)
        xs2bot = int((poly[4]+gpos[0])*depth*40+72/2)
        ysbot = int((cos*poly[5]+gpos[1])*depth*40+40/2)
    
        if ysbot > ystop and (ztop + gpos[2] > 0 or zbot + gpos[2] > 0): #polygon is in front of and facing camera
            shade = int(math.sin(rot+math.pi/2+poly[7])*poly[8])
            fquad(xs1top, xs2top, ystop, xs1bot, xs2bot, ysbot, shade+poly[6])
    
    points = [] #rotating pentagonal prism
    for point in range(5):
        sin = math.sin(rot + math.pi*2/5*point)
        cos = math.cos(rot + math.pi*2/5*point)
        depth = 1.0 / max(sin + gpos[2], 0.1)
        xs1 = int((-4+gpos[0])*depth*40+72/2)
        xs2 = int((-4.5+gpos[0])*depth*40+72/2)
        ys = int((cos+gpos[1])*depth*40+40/2)
        if sin + gpos[2] > 0: onscreen = True
        else: onscreen = False
        points.append([xs1, xs2, ys, onscreen])
    
    for poly in range(5): #inner faces
        top = points[poly]
        bot = points[(poly+1)%5]
        if not (top[3] or bot[3]): continue #points are behind camera
        
        if top[2] > bot[2]: #inner face visible
            shade = int(math.sin(rot+math.pi/2 + math.pi*2/5*poly)*64) + 80
            fquad(top[0], top[1], top[2], bot[0], bot[1], bot[2], shade)
    
    for poly in range(5): #outer faces
        top = points[poly]
        bot = points[(poly+1)%5]
        if not (top[3] or bot[3]): continue #points are behind camera
        
        if not top[2] > bot[2]: #outer face visible
            shade = int(math.sin(rot+math.pi/2 + math.pi*2/5*poly + math.pi)*64) + 128
            fquad(bot[0], bot[1], bot[2], top[0], top[1], top[2], shade)
            
    #ditherscreen(0)
    ditherscreen_white(0)
    thumby.display.update()
    frames += 1
    if time.ticks_ms() > nexttime:
        nexttime += 1000
        print(f"{frames} FPS")
        frames = 0
    #gc.collect()