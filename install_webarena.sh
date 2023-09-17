git clone https://github.com/web-arena-x/webarena/tree/main
cd webarena
conda create -n webarena python=3.10; conda activate webarena
pip install -r requirements.txt
playwright install
pip install -e .