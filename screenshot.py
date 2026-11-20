from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width":1600,"height":1000})
    pg.goto("file://" + os.path.abspath("dashboard_gtm.html"))
    pg.wait_for_timeout(2000)
    pg.screenshot(path="dashboard_gtm_28programas_2026-11-17.png", full_page=True)
    b.close()
