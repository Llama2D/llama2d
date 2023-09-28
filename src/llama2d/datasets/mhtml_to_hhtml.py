import os

from tqdm import tqdm

from ..constants import (
    MIND2WEB_HHTML_DIR,
    MIND2WEB_IN_DIR,
    MIND2WEB_MHTML_DIR,
    MIND2WEB_OUT_DIR,
    MIND2WEB_VIZ_DIR,
    SCREEN_RESOLUTION,
)

mhtml_files = os.listdir(MIND2WEB_MHTML_DIR)
for mhtml_filename in tqdm(mhtml_files):
    # print(mhtml_filename)
    mhtml_path = os.path.join(MIND2WEB_MHTML_DIR, mhtml_filename)

    hhtml_path = os.path.join(MIND2WEB_HHTML_DIR, mhtml_filename)
    if os.path.exists(hhtml_path):
        os.remove(hhtml_path)

    mhtml_content = open(mhtml_path, "r").read()

    hhtml_content = mhtml_content.replace(":hover", ".hvvvr")

    with open(hhtml_path, "w") as f:
        f.write(hhtml_content)

print("Done!")
