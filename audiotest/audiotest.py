import time
import thumby

twelveroottwo = 1.059463094
czero = 8.175798916
pitches = []
for i in range(128):
    pitches.append(int(czero*twelveroottwo**i))

notes = "DFIFM~M~K~DFIFK~K~IHF~DFIFI~KH~FD~DKI~DFIFM~M~K~DFIFP~HI~HFDFIFI~KH~FD~DKI~"
times = "111121214211112121311111112222112224441111212142111131221121111222211222444" #1 == quarter note
bpm = 114

while True:
    for n, t in zip(notes, times):
        delay = 60000//bpm//4 * (ord(t)-48)
        if n == "~": time.sleep_ms(int(delay)) #using ~ as a rest since note 126 is unlikely to be used
        else: thumby.audio.playBlocking(pitches[ord(n)], delay)