from pathlib import Path

current_dir = Path(__file__).parent

with open(current_dir / "urls.txt", "r") as f:
    urls = f.read().splitlines()
