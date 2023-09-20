pip install gdown
Help(){
  echo "create HF dataset"
}
pip install -r reqs.txt
# install & Mind2Web mhtml dataset
html_zip="cached-pretrain/before_files.html"
  # output directory
data_html_dir=data/mind2web-html/
mhtml_url=https://drive.google.com/uc?id=1RGNcNTlQrZhF1KuGBcGenkON1u74_IYx
gdown -O $html_zip $mhtml_url
unzip $html_zip -d $data_html_dir && rm $html_zip