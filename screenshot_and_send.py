# -*- coding: utf-8 -*-
"""
自动访问网址截图、推送到 GitHub、发送到企业微信并清理图片
"""
import os
import time
import requests
from playwright.sync_api import sync_playwright

# 你要截图的网址列表，手动填写
URLS = [
    "https://www.gd.gov.cn",
]

# 截图保存目录
IMG_DIR = "screenshots"
os.makedirs(IMG_DIR, exist_ok=True)

# 企业微信机器人webhook配置
WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL", "")  # 企微机器人webhook

def take_screenshot(url, save_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        time.sleep(2)
        page.screenshot(path=save_path, full_page=True)
        browser.close()

def send_wechat_webhook_markdown(content):
    if not WEBHOOK_URL:
        print("未配置WECHAT_WEBHOOK_URL，跳过webhook发送")
        return False
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown_v2",
        "markdown_v2": {
            "content": content
        }
    }
    resp = requests.post(WEBHOOK_URL, headers=headers, json=data).json()
    if resp.get("errcode", 0) == 0:
        print("Webhook发送成功")
        return True
    else:
        print(f"Webhook发送失败: {resp}")
        return False

def clear_screenshots_dir():
    if os.path.exists(IMG_DIR):
        for f in os.listdir(IMG_DIR):
            file_path = os.path.join(IMG_DIR, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

def main():
    # 先清空截图目录
    clear_screenshots_dir()
    # 截图
    img_files = []
    img_urls = []
    for url in URLS:
        fname = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".png"
        save_path = os.path.join(IMG_DIR, fname)
        take_screenshot(url, save_path)
        img_files.append(save_path)
        # 生成GitHub raw图片地址（需根据你的repo实际路径修改）
        repo = os.getenv("GITHUB_REPOSITORY", "user/repo")
        branch = os.getenv("GITHUB_REF_NAME", "main")
        img_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{IMG_DIR}/{fname}"
        img_urls.append(img_url)
    # 推送到 GitHub（由 workflow 完成）
    # 发送到企业微信机器人webhook
    if img_urls:
        md = '# 截图日报\n' + '\n'.join([f'![]({u})' for u in img_urls])
        send_wechat_webhook_markdown(md)

if __name__ == "__main__":
    main()
