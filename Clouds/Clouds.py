#Scrolling clouds effect created by transistortester
#Inspired by the opening of the C64 demo "Uncensored" created by Booze Design: https://www.youtube.com/watch?v=9LFD4SzW3e0
#Press A to quit and B to toggle and outline

screen = bytearray(72*40) #allocate these early so they aren't affected by fragmentation
dithermask_gs = bytearray(open("/Games/Clouds/mask_gs.bin", "rb").read())

import machine
machine.freq(125000000) #ensure this is running at full speed

from sys import path as syspath
syspath.insert(0, "/Games/Clouds")
import thumby
thumby.display.update() #clear screen asap
from time import ticks_ms
from math import sin
import thumbyGrayscale
from random import randint

thumbyGrayscale.display.setFPS(60)
showoutline = False

#this assumes the 4 shades of gray are [0, 170, 227, 255]
#this was chosen by eye and may well be incorrect.
@micropython.viper
def ditherscreen_gray(offset:int):
    display = ptr8(thumbyGrayscale.display.buffer)
    shade = ptr8(thumbyGrayscale.display.shading)
    mask = ptr8(dithermask_gs)
    scr = ptr8(screen)
    index:int = 0
    bufpos:int = 0
    bit:int = 1
    x:int = 0
    y:int = 0
    
    for index in range(72*40//8):
        display[index] = 0 #clear screen
        shade[index] = 0
    
    index = 0
    for y in range(40):
        bit = 1 << (y & 7)
        bufpos = (y >> 3) * 72
        for x in range(72):
            if scr[index] < 170:
                if scr[index] > mask[index + offset]: shade[bufpos + x] |= bit
            elif scr[index] < 227:
                shade[bufpos + x] |= bit
                if scr[index] > mask[index + offset + 2880]: display[bufpos + x] |= bit
            else:
                display[bufpos + x] |= bit
                if scr[index] <= mask[index + offset + 5760]: shade[bufpos + x] |= bit
            index += 1

@micropython.viper
def fillscreen(fill:int):
    scr = ptr8(screen)
    i:int = 0
    for i in range(72*40):
        scr[i] = fill


cloudshape = bytearray([4,4,3,3,3,4,4,3,2,2,1,1,1,1,1,2,3,3,3,4,4,3,3,4,4,5,5,5,6,6,5,5,4,4,5,5,5,4,3,3,2,2,2,2,2,2,2,3,3,3,2,1,0,0,0,0,0,0,0,1,2,2,2,1,1,1,1,1,1,1,1,1,2,2,4,5,5,5,4,3,3,3,4,5,6,5,4,3,2,2,2,3,4,4,3,3,3,3,3,3,3,4,5,4,3,3,3,3,4,4,5,6,6,6,5,5,5,4,4,5,6,6,5,5,4,4,4,3,3,3,3,3,4,6,6,5,5,4,4,4,4,3,3,4])
clouds = [] #each is [xpos, ypos, shade]
nextcloud = 0
fill = 0 #background colour

@micropython.viper
def drawcloud(xoff:int, yoff:int, outline:int, shade:int, bgshade:int):
    xpos:int = 0
    ypos:int = 0
    bufpos:int = 0
    fill:int = 0
    cloudptr = ptr8(cloudshape)
    cloudsize:int = int(len(cloudshape))
    scr = ptr8(screen)
    while xpos < 72:
        bufpos = (yoff + cloudptr[(xpos+xoff)%cloudsize]) * 72 + xpos
        fill = outline
        if bufpos < 0:
            bufpos = xpos
            fill = shade
        while bufpos < 2880 and scr[bufpos] == bgshade: #small bug: if the previous cloud is *exactly* bgshade it will be overwritten
            scr[bufpos] = fill
            fill = shade
            bufpos += 72
        xpos += 1


while not thumby.buttonA.justPressed():
    if thumby.buttonB.justPressed():
        showoutline = not showoutline
    nextcloud -= 1
    if nextcloud <= 0:
        clouds.append([randint(0, len(cloudshape)-1), 40.0, int(sin(ticks_ms()/1000)*100+150)])
        nextcloud = 20
    if len(clouds) and clouds[0][1] < -6: #completely off screen
        fill = clouds.pop(0)[2] #remove layer, but set background colour just in case the next cloud isn't overlapping the top of the screen
    
    fillscreen(fill)
    
    t = ticks_ms()/2000
    for cloud in reversed(clouds):
        cloud[1] -= 0.35
        if showoutline:
            drawcloud(int(cloud[0] + sin(cloud[1]*0.13+t)*15), int(cloud[1]), 1, int(cloud[2]), fill)
        else:
            drawcloud(int(cloud[0] + sin(cloud[1]*0.13+t)*15), int(cloud[1]), int(cloud[2]), int(cloud[2]), fill)
    
    ditherscreen_gray(0)
    thumbyGrayscale.display.update()
    #print(len(clouds))

thumbyGrayscale.display.disableGrayscale()
thumby.reset()