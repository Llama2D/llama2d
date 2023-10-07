from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

# 3 times the resolution of a 1080p monitor
SCREEN_RESOLUTION = (1280, 1080 * 3)

DATA_DIR = ROOT_DIR / "data"

MIND2WEB_MHTML_DIR = DATA_DIR / "mind2web-mhtml"
MIND2WEB_HHTML_DIR = DATA_DIR / "mind2web-hhtml"

MIND2WEB_OUT_DIR = DATA_DIR / "mind2web-out"
MIND2WEB_IN_DIR = DATA_DIR / "mind2web-in"
MIND2WEB_VIZ_DIR = DATA_DIR / "mind2web-viz"

MIND2WEB_CACHE_DIR = DATA_DIR / "mind2web-cache"
PRETRAINING_CACHE_DIR = DATA_DIR / "pretraining-cache"

# path to the Google Cloud credentials file
SECRETS_FILE = ROOT_DIR / "secrets" / "gcp-vision.json"

# max number of tokens allowed in a page screenshot
# we will remove all page tokens after this number
MAX_PAGE_LEN = 1000

# max number of tokens inputted to Llama2d - between prompt, page, and completion
# we will truncate big inputs to this number
# we will also pad small inputs to this number
MAX_SEQ_LEN = 250

MAX_TAGS_LEN = 150
