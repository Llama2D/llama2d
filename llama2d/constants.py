import os

curr_dir = os.path.dirname(os.path.realpath(__file__))

# 3 times the resolution of a 1080p monitor
SCREEN_RESOLUTION = (1920, 1080 * 3)

DATA_DIR = f"{curr_dir}/../data"

MIND2WEB_MHTML_DIR = f"{DATA_DIR}/mind2web-mhtml"

MIND2WEB_CACHE_DIR = f"{DATA_DIR}/mind2web-cache"
PRETRAINING_CACHE_DIR = f"{DATA_DIR}/pretraining-cache"

# path to the Google Cloud credentials file
SECRETS_FILE = f"{curr_dir}/../secrets/gcp-vision.json"

# max number of tokens allowed in a page screenshot
# we will remove all page tokens after this number
MAX_PAGE_LEN = 1000

# max number of tokens inputted to Llama2d - between prompt, page, and completion
# we will truncate big inputs to this number
# we will also pad small inputs to this number
MAX_SEQ_LEN = 1500
