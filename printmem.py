import gc
from micropython import mem_info
def printmem(reason=None, heap=False, collect=True):
    if collect: gc.collect()
    freemem = gc.mem_free()
    totalmem = gc.mem_alloc() + freemem
    print("\n" + "="*79)
    if reason: print(f"***{reason}***")
    print(f"{(totalmem-freemem)/totalmem*100}% RAM used")
    if heap: mem_info(1)
    else: mem_info()
    print("="*79)
