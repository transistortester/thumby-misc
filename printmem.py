import gc
from micropython import mem_info
def printmem(reason=None):
    totalmem = 192064 #192064 is the total reported by mem_info
    print("\n" + "="*79)
    if reason: print(f"***{reason}***")
    print(f"{(totalmem-gc.mem_free())/totalmem*100}% RAM used")
    mem_info()
    print("="*79)