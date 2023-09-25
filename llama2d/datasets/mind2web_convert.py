from ..constants import MIND2WEB_OUT_DIR, MIND2WEB_CACHE_DIR

from glob import glob
import os
import time
import shutil
files = glob(f"{MIND2WEB_OUT_DIR}/*/input.pt")

# copy <uid>/input.pd to MIND2WEB_CACHE_DIR/<uid>.pt
# but only for input.pt files that are less than 1 day old

for f in files:
    # get date modified
    date_modified = os.path.getmtime(f)
    # get current time
    current_time = time.time()
    # get difference
    diff = current_time - date_modified
    # if less than 1 day old
    if diff < 60 * 60 * 15:
        # get uid
        uid = f.split("/")[-2]
        # copy file
        shutil.copy(f, f"{MIND2WEB_CACHE_DIR}/{uid}.pt")
        print(f"Copied {f} to {MIND2WEB_CACHE_DIR}/{uid}.pt")
    else:
        print(f"Skipping {f} because it is {diff//(60*60)} hrs old")