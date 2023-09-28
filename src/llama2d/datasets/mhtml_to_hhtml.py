from tqdm import tqdm

from src.llama2d.constants import MIND2WEB_HHTML_DIR, MIND2WEB_MHTML_DIR

mhtml_files = [f for f in MIND2WEB_MHTML_DIR.iterdir() if f.suffix == ".mhtml"]

for mhtml_filename in tqdm(mhtml_files):
    # print(mhtml_filename)
    mhtml_path = MIND2WEB_MHTML_DIR / mhtml_filename
    html_path = MIND2WEB_HHTML_DIR / mhtml_filename.with_suffix(".html")

    if html_path.exists():
        html_path.unlink()

    mhtml_content = open(mhtml_path, "r").read()
    hhtml_content = mhtml_content.replace(":hover", ".hvvvr")

    with open(html_path, "w") as f:
        f.write(hhtml_content)

print("Done!")
