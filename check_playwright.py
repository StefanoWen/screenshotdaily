#!/usr/bin/env python3
"""
检查Playwright二进制文件的脚本
"""
import os
import sys
from pathlib import Path

def check_playwright_binaries():
    """检查Playwright二进制文件是否存在且有效"""
    binary_dir = Path('playwright-binaries/chromium')
    
    if binary_dir.exists() and any(binary_dir.iterdir()):
        print('✅ 本地二进制文件存在且有效，无需更新')
        return False
    else:
        print('📥 本地二进制文件缺失或无效，需要更新')
        return True

def verify_playwright_installation():
    """验证Playwright安装"""
    try:
        from playwright.sync_api import sync_playwright
        print('✅ Playwright模块导入成功')
        
        # 检查浏览器文件
        browser_path = os.path.expanduser('~/.cache/ms-playwright')
        found_files = []
        
        for root, dirs, files in os.walk(browser_path):
            for file in files:
                if file in ['headless_shell', 'chrome']:
                    found_files.append(os.path.join(root, file))
        
        if found_files:
            print(f'✅ 找到 {len(found_files)} 个浏览器文件')
            for f in found_files[:3]:  # 只显示前3个
                print(f'  {f}')
            return True
        else:
            print('❌ 未找到浏览器文件')
            return False
            
    except ImportError as e:
        print(f'❌ Playwright模块导入失败: {e}')
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        success = verify_playwright_installation()
        sys.exit(0 if success else 1)
    else:
        update_needed = check_playwright_binaries()
        print(f'UPDATE_NEEDED={"true" if update_needed else "false"}')
