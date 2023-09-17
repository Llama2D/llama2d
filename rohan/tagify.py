from .mls_utils import (
    check_interactable_bs4,
    check_interactable_sel,
    clean_html,
    bs4_to_sel,
)
# from reworkd_platform.settings import settings

from bs4 import BeautifulSoup

# create webdriver

import undetected_chromedriver as uc
import json

driver = uc.Chrome(headless=False,use_subprocess=True,version_main=116)

def tagify_webpage(url):
    driver.get(url)
    html = clean_html(driver.page_source)
    soup = BeautifulSoup(html, "html.parser")

    num = 0
    for tag in soup.find_all(True):
        if check_interactable_bs4(tag):
            sel_tag = bs4_to_sel(tag, driver)
            tag_whitelist = ["input", "textarea", "select"]
            if sel_tag.text.strip() == "" and sel_tag.tag_name not in tag_whitelist:
                continue
            if check_interactable_sel(sel_tag, driver):
                num += 1
                new_text = f"{tag.text} [{num}]"

                script = f"""
                const el = arguments[0];

                const specialTags = ["input", "textarea", "select"];

                const tagLower = el.tagName.toLowerCase();

                if(!specialTags.includes(tagLower))
                    el.innerText = {json.dumps(new_text)};
                else if(tagLower === "input")
                    el.placeholder = {json.dumps(new_text)};
                else if(tagLower === "textarea")
                    el.placeholder = {json.dumps(new_text)};
"""

                driver.execute_script(script, sel_tag)