SCREEN_RESOLUTION = (1920, 1080*3)
import os
curr_dir = os.path.dirname(os.path.realpath(__file__))
MIND2WEB_IN_DIR = f"{curr_dir}/../mind2web-data"
MIND2WEB_OUT_DIR = f"{curr_dir}/../mind2web-output"
SECRETS_FILE = f"{curr_dir}/secrets/llama2d-dee298d9a98d.json"

MAX_SEQ_LEN = 2048
MAX_PAGE_LEN = 1500