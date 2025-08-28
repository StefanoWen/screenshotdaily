# -*- coding: utf-8 -*-
"""
自动访问网址截图、推送到 GitHub、发送到企业微信
支持CI环境自动调用和本地调试
"""
import os
import sys
import time
import argparse
import logging
import requests
from playwright.sync_api import sync_playwright
from typing import List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_URLS = [
    "https://www.gd.gov.cn",
    "https://zfsg.gd.gov.cn",
    "https://www.gdjct.gd.gov.cn",
    "https://www.gdzz.gov.cn",
    "https://www.gdzwfw.gov.cn",
    "https://www.gdpc.gov.cn",

]

DEFAULT_IMG_DIR = "screenshots"

# 环境变量配置
def get_env_config():
    """获取环境变量配置"""
    webhook_key = os.getenv("WEBHOOK_KEY")
    webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}" if webhook_key else None
    
    return {
        'webhook_url': webhook_url,
        'webhook_key': webhook_key,
        'github_repository': os.getenv("GITHUB_REPOSITORY"),
        'github_ref_name': os.getenv("GITHUB_REF_NAME", "main"),
        'debug_local': os.getenv("DEBUG_LOCAL", "false").lower() == "true",
        'ci_mode': os.getenv("CI", "false").lower() == "true",
    }

def take_screenshot(url: str, save_path: str, config: dict, width: int = 1920, height: int = 1080) -> bool:
    """
    对指定URL进行截图
    
    Args:
        url: 目标网址
        save_path: 截图保存路径
        config: 配置字典
        width: 截图宽度
        height: 截图高度
    
    Returns:
        bool: 截图是否成功
    """
    logger.info(f"开始截图: {url} (尺寸: {width}x{height})")
    
    # 截图尺寸配置
    screenshot_width = width
    screenshot_height = height
    
    try:
        with sync_playwright() as p:
            # 根据环境配置浏览器启动参数
            launch_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-setuid-sandbox',
                '--disable-software-rasterizer',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps'
            ]
            
            # CI环境下添加额外参数
            if config['ci_mode']:
                launch_args.extend([
                    '--single-process',
                    '--disable-dev-shm-usage',
                    '--disable-software-rasterizer'
                ])
            
            browser = p.chromium.launch(
                headless=True,
                args=launch_args
            )
            
            # 创建页面并设置视窗大小
            page = browser.new_page()
            page.set_viewport_size({
                "width": screenshot_width,
                "height": screenshot_height
            })
            
            # 设置超时时间 - CI环境使用更长超时
            if config['ci_mode']:
                page.set_default_timeout(120000)  # CI环境：120秒
                page.set_default_navigation_timeout(180000)  # CI环境：180秒
            else:
                page.set_default_timeout(60000)  # 本地：60秒
                page.set_default_navigation_timeout(90000)  # 本地：90秒
            
            # 设置User-Agent
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            try:
                # 使用domcontentloaded策略 - CI环境使用更长超时
                goto_timeout = 90000 if config['ci_mode'] else 60000
                sleep_time = 5 if config['ci_mode'] else 3
                body_timeout = 20000 if config['ci_mode'] else 10000
                screenshot_timeout = 60000 if config['ci_mode'] else 30000
                
                page.goto(url, wait_until="domcontentloaded", timeout=goto_timeout)
                time.sleep(sleep_time)
                
                # 等待主要内容加载
                try:
                    page.wait_for_selector('body', timeout=body_timeout)
                except:
                    logger.warning(f"无法找到body元素，但仍尝试截图: {url}")
                
                # 截图
                page.screenshot(path=save_path, full_page=False, timeout=screenshot_timeout)
                logger.info(f"截图成功: {url}")
                return True
                
            except Exception as e:
                logger.error(f"截图失败 {url}: {e}")
                
                # 五次重试机制 - CI环境使用更长超时和间隔
                max_retries = 5
                for retry in range(1, max_retries + 1):
                    try:
                        logger.info(f"第 {retry} 次重试截图: {url}")
                        # CI环境使用更长超时
                        goto_timeout = 60000 if config['ci_mode'] else 30000
                        screenshot_timeout = 60000 if config['ci_mode'] else 30000
                        retry_interval = 5 if config['ci_mode'] else 1
                        
                        page.goto(url, wait_until="commit", timeout=goto_timeout)
                        time.sleep(retry_interval)
                        page.screenshot(path=save_path, full_page=False, timeout=screenshot_timeout)
                        logger.info(f"第 {retry} 次重试截图成功: {url}")
                        return True
                    except Exception as retry_e:
                        logger.error(f"第 {retry} 次重试截图失败 {url}: {retry_e}")
                        if retry == max_retries:
                            logger.error(f"截图重试 {max_retries} 次后仍然失败，放弃截图: {url}")
                            return False
                        # CI环境使用更长重试间隔
                        retry_interval = 5 if config['ci_mode'] else 1
                        time.sleep(retry_interval)
                
            finally:
                browser.close()
                
    except Exception as e:
        logger.error(f"浏览器启动失败 {url}: {e}")
        return False

def send_wechat_webhook_markdown(content: str, config: dict) -> bool:
    """
    发送企业微信webhook消息
    
    Args:
        content: 消息内容
        config: 配置字典
    
    Returns:
        bool: 发送是否成功
    """
    webhook_url = config['webhook_url']
    
    if not webhook_url:
        logger.warning("未配置WECHAT_WEBHOOK_URL，跳过webhook发送")
        return False
    
    try:
        headers = {"Content-Type": "application/json"}
        data = {
            "msgtype": "markdown_v2",
            "markdown_v2": {
                "content": content
            }
        }
        
        logger.info("正在发送企业微信webhook消息...")
        resp = requests.post(webhook_url, headers=headers, json=data, timeout=30)
        resp_data = resp.json()
        
        if resp_data.get("errcode", 0) == 0:
            logger.info("Webhook发送成功")
            return True
        else:
            logger.error(f"Webhook发送失败: {resp_data}")
            return False
            
    except Exception as e:
        logger.error(f"Webhook发送异常: {e}")
        return False

def check_url_accessibility(url: str, timeout: int = 10) -> bool:
    """
    检查URL是否可访问
    
    Args:
        url: 要检查的URL
        timeout: 超时时间
    
    Returns:
        bool: URL是否可访问
    """
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            logger.info(f"URL可访问: {url}")
            return True
        else:
            logger.warning(f"URL不可访问: {url}，状态码: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"URL请求失败: {url}，原因: {e}")
        return False

def generate_github_image_url(repo: str, branch: str, img_dir: str, filename: str) -> str:
    """
    生成GitHub raw图片URL
    
    Args:
        repo: 仓库名
        branch: 分支名
        img_dir: 图片目录
        filename: 文件名
    
    Returns:
        str: GitHub raw图片URL
    """
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{img_dir}/{filename}"

def save_image_urls_to_file(img_urls: List[str], file_path: str = "image_urls.txt") -> bool:
    """
    保存图片URL列表到文件
    
    Args:
        img_urls: 图片URL列表
        file_path: 文件保存路径
    
    Returns:
        bool: 保存是否成功
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for url in img_urls:
                f.write(url + '\n')
        logger.info(f"图片URL已保存到文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存图片URL到文件失败: {e}")
        return False

def send_webhook_from_file(config: dict, file_path: str = "image_urls.txt") -> bool:
    """
    从文件读取图片URL并发送webhook消息
    
    Args:
        config: 配置字典
        file_path: 文件路径
    
    Returns:
        bool: 发送是否成功
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"图片URL文件不存在: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            img_urls = [line.strip() for line in f if line.strip()]
        
        if not img_urls:
            logger.warning("图片URL文件为空")
            return False
        
        md = '# 📸 截图日报\n\n' + '\n'.join([f'![]({u})' for u in img_urls])
        return send_wechat_webhook_markdown(md, config)
        
    except Exception as e:
        logger.error(f"从文件发送webhook失败: {e}")
        return False

def commit_and_push_screenshots(img_dir: str) -> bool:
    """
    提交并推送截图到GitHub
    
    Args:
        img_dir: 截图目录
    
    Returns:
        bool: 操作是否成功
    """
    try:
        logger.info("本地调试：自动git add/commit/push截图...")
        
        # 配置git用户信息
        os.system("git config --global user.email 'github-actions[bot]@users.noreply.github.com'")
        os.system("git config --global user.name 'github-actions[bot]'")
        
        # 添加、提交和推送
        result1 = os.system(f"git add {img_dir}/*")
        result2 = os.system("git commit -m 'feat: add daily screenshots' || echo 'No changes to commit'")
        result3 = os.system("git push")
        
        if result3 == 0:
            logger.info("截图推送成功")
            return True
        else:
            logger.error("截图推送失败")
            return False
            
    except Exception as e:
        logger.error(f"提交推送截图时发生异常: {e}")
        return False

def main():
    """
    主函数 - 支持命令行参数和环境变量
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='自动截图并发送到企业微信')
    parser.add_argument('--urls', nargs='*', help='要截图的URL列表')
    parser.add_argument('--img-dir', default=DEFAULT_IMG_DIR, help='截图保存目录')
    parser.add_argument('--width', type=int, default=1920, help='截图宽度 (默认: 1920)')
    parser.add_argument('--height', type=int, default=1080, help='截图高度 (默认: 1080)')
    parser.add_argument('--no-webhook', action='store_true', help='不发送webhook消息')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 获取环境配置
    config = get_env_config()
    
    # 确定要截图的URL列表
    urls = args.urls if args.urls else DEFAULT_URLS
    
    # 创建截图目录
    os.makedirs(args.img_dir, exist_ok=True)
    
    logger.info("开始执行截图任务")
    logger.info(f"目标URLs: {urls}")
    logger.info(f"截图目录: {args.img_dir}")
    logger.info(f"CI模式: {config['ci_mode']}")
    logger.info(f"本地调试: {config['debug_local']}")
    
    # 不再清空截图目录，直接覆盖现有文件
    logger.info("跳过清空截图目录，将直接覆盖现有文件")
    
    # 截图任务
    img_files = []
    img_urls = []
    success_count = 0
    
    for url in urls:
        # 检查URL可访问性
        if not check_url_accessibility(url):
            continue
        
        # 生成文件名和保存路径
        fname = url.replace("https://", "").replace("http://", "").replace("/", "_") + ".png"
        save_path = os.path.join(args.img_dir, fname)
        
        # 执行截图
        if take_screenshot(url, save_path, config, args.width, args.height):
            img_files.append(save_path)
            success_count += 1
            
            # 生成图片URL
            if config['debug_local']:
                repo = "StefanoWen/screenshotdaily"
            else:
                repo = config['github_repository'] or "user/repo"
            
            branch = config['github_ref_name']
            img_url = generate_github_image_url(repo, branch, args.img_dir, fname)
            img_urls.append(img_url)
        else:
            logger.error(f"截图失败: {url}")
    
    logger.info(f"截图完成，成功: {success_count}/{len(urls)}")
    
    # 保存图片URL到文件（CI环境下）
    if config['ci_mode'] and img_urls:
        save_image_urls_to_file(img_urls)
    
    # 本地调试模式下推送截图并发送webhook
    if config['debug_local'] and img_files:
        if not commit_and_push_screenshots(args.img_dir):
            logger.error("推送截图失败")
        else:
            # 等待GitHub同步
            logger.info("等待GitHub同步...")
            time.sleep(5)
        
        # 发送webhook消息（本地调试模式）
        if img_urls and not args.no_webhook:
            md = '# 📸 截图日报\n\n' + '\n'.join([f'![]({u})' for u in img_urls])
            if send_wechat_webhook_markdown(md, config):
                logger.info("企业微信消息发送成功")
            else:
                logger.error("企业微信消息发送失败")
                sys.exit(1)
    
    # CI环境下不立即发送webhook，由后续步骤处理
    if config['ci_mode'] and img_urls and not args.no_webhook:
        logger.info("CI模式下已保存图片URL到文件，将由后续步骤发送webhook")
    
    # 程序运行结束后不再清理截图目录
    logger.info("程序运行完成，保留截图文件")
    
    logger.info("任务执行完成")
    
    # 如果没有成功截图任何URL，返回错误码
    if success_count == 0:
        logger.error("没有成功截图任何URL")
        sys.exit(1)

if __name__ == "__main__":
    main()
