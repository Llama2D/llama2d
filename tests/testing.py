from playwright.sync_api import Playwright, sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(
        "file:///Users/andrewstelmach/Desktop/llama2d/data/mind2web-mhtml/961c3a5e-f8ce-4c71-a917-aa546dcea7fb_before.mhtml"
    )
    # do something with the page...
    browser.close()
