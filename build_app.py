#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 小说阅读器 - 打包脚本
支持将程序打包为单个可执行文件
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class NovelReaderBuilder:
    def __init__(self):
        self.app_name = "小说阅读器"
        self.main_file = "main.py"
        self.system = platform.system().lower()
        
    def print_colored(self, message, color=""):
        """打印彩色消息"""
        colors = {
            "red": "\033[91m",
            "green": "\033[92m", 
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "bold": "\033[1m",
            "end": "\033[0m"
        }
        
        if color and color in colors:
            print(f"{colors[color]}{message}{colors['end']}")
        else:
            print(message)
    
    def check_python(self):
        """检查Python环境"""
        self.print_colored("🔍 检查Python环境...", "blue")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.print_colored("❌ 需要Python 3.7或更高版本", "red")
            return False
            
        self.print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro}", "green")
        return True
    
    def check_and_install_packages(self):
        """检查并安装必要的包"""
        self.print_colored("📦 检查依赖包...", "blue")
        
        packages = [
            ("PySide6", "PySide6"),
            ("chardet", "chardet"), 
            ("PyInstaller", "pyinstaller")
        ]
        
        for package_name, import_name in packages:
            try:
                __import__(import_name)
                self.print_colored(f"✅ {package_name} 已安装", "green")
            except ImportError:
                self.print_colored(f"⚠️  安装 {package_name}...", "yellow")
                result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_colored(f"✅ {package_name} 安装成功", "green")
                else:
                    self.print_colored(f"❌ {package_name} 安装失败: {result.stderr}", "red")
                    return False
        return True
    
    def clean_build_dirs(self):
        """清理构建目录"""
        self.print_colored("🧹 清理构建目录...", "blue")
        
        dirs_to_clean = ['build', 'dist', '__pycache__', 'NovelReader_Portable']
        files_to_clean = ['*.spec']
        
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                self.print_colored(f"  已清理: {dir_name}", "white")
        
        # 清理spec文件
        for spec_file in Path('.').glob('*.spec'):
            spec_file.unlink()
            self.print_colored(f"  已清理: {spec_file}", "white")
    
    def get_pyinstaller_args(self):
        """获取PyInstaller参数"""
        args = [
            "pyinstaller",
            "--onefile",           # 打包成单个文件
            "--noconsole",         # 不显示控制台
            "--windowed",          # 窗口模式
            "--clean",             # 清理临时文件
            "--noconfirm",         # 不需要确认
            "--name", self.app_name,  # 程序名称
            
            # 添加数据文件
            "--add-data", "test.txt:.",
            "--add-data", "README.md:.",
            
            # 隐式导入
            "--hidden-import", "chardet",
            "--hidden-import", "PySide6.QtCore",
            "--hidden-import", "PySide6.QtWidgets", 
            "--hidden-import", "PySide6.QtGui",
            
            # 排除不需要的模块
            "--exclude-module", "tkinter",
            "--exclude-module", "matplotlib",
            "--exclude-module", "numpy",
            "--exclude-module", "scipy", 
            "--exclude-module", "pandas",
            "--exclude-module", "jupyter",
            "--exclude-module", "IPython",
            "--exclude-module", "PIL",
            "--exclude-module", "cv2",
            
            self.main_file  # 主程序文件
        ]
        
        return args
    
    def build_executable(self):
        """构建可执行文件"""
        self.print_colored("🚀 开始打包...", "blue")
        self.print_colored("这可能需要几分钟时间，请耐心等待...", "yellow")
        
        args = self.get_pyinstaller_args()
        
        try:
            result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                self.print_colored("🎉 打包成功！", "green")
                return True
            else:
                self.print_colored("❌ 打包失败！", "red")
                self.print_colored("错误信息:", "red")
                print(result.stderr)
                return False
                
        except Exception as e:
            self.print_colored(f"❌ 打包过程中出现异常: {e}", "red")
            return False
    
    def create_portable_package(self):
        """创建便携版"""
        exe_name = self.app_name
        if self.system == "windows":
            exe_name += ".exe"
        
        exe_path = f"dist/{exe_name}"
        
        if not os.path.exists(exe_path):
            self.print_colored("❌ 可执行文件不存在", "red")
            return False
        
        self.print_colored("📦 创建便携版...", "blue")
        
        # 创建便携版目录
        portable_dir = "NovelReader_Portable"
        if os.path.exists(portable_dir):
            shutil.rmtree(portable_dir)
        
        os.makedirs(portable_dir)
        
        # 复制文件
        shutil.copy2(exe_path, f"{portable_dir}/{exe_name}")
        shutil.copy2("README.md", f"{portable_dir}/README.md")
        shutil.copy2("test.txt", f"{portable_dir}/test.txt")
        
        # 创建启动脚本
        if self.system != "windows":
            start_script = f"""#!/bin/bash
cd "$(dirname "$0")"
./{exe_name}
"""
            with open(f"{portable_dir}/启动.sh", "w", encoding="utf-8") as f:
                f.write(start_script)
            os.chmod(f"{portable_dir}/启动.sh", 0o755)
        
        # 创建说明文件
        readme_content = f"""# {self.app_name} 便携版

## 使用方法
1. 直接运行: ./{exe_name}
2. 使用启动脚本: ./启动.sh (Linux/macOS)

## 文件说明
- {exe_name}: 主程序
- README.md: 程序说明
- test.txt: 示例小说文件
- 启动.sh: 启动脚本 (Linux/macOS)

## 注意事项
- 本程序无需安装，可直接运行
- 支持拖拽打开txt文件
- 支持多种编码格式
"""
        
        with open(f"{portable_dir}/使用说明.txt", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        self.print_colored("✅ 便携版创建完成", "green")
        return True
    
    def show_results(self):
        """显示构建结果"""
        exe_name = self.app_name
        if self.system == "windows":
            exe_name += ".exe"
        
        exe_path = f"dist/{exe_name}"
        
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            
            self.print_colored(f"📄 输出文件: {exe_path}", "cyan")
            self.print_colored(f"📏 文件大小: {file_size:.1f} MB", "cyan")
            
            # 设置执行权限 (Linux/macOS)
            if self.system != "windows":
                os.chmod(exe_path, 0o755)
                self.print_colored("🔐 已设置执行权限", "green")
            
            self.print_colored("", "")
            self.print_colored("🚀 使用方法:", "bold")
            self.print_colored(f"  ./{exe_path}", "white")
            
            if os.path.exists("NovelReader_Portable"):
                self.print_colored("", "")
                self.print_colored("📦 便携版:", "bold") 
                self.print_colored("  NovelReader_Portable/ 文件夹", "white")
                self.print_colored("  可复制到任意位置使用", "white")
    
    def build(self):
        """主构建流程"""
        self.print_colored("=== PySide6 小说阅读器打包工具 ===", "bold")
        print()
        
        # 检查主程序文件
        if not os.path.exists(self.main_file):
            self.print_colored(f"❌ 找不到主程序文件 {self.main_file}", "red")
            return False
        
        # 执行构建步骤
        steps = [
            ("检查Python环境", self.check_python),
            ("检查依赖包", self.check_and_install_packages),
            ("清理构建目录", lambda: (self.clean_build_dirs(), True)[1]),
            ("构建可执行文件", self.build_executable),
            ("创建便携版", self.create_portable_package),
        ]
        
        for step_name, step_func in steps:
            print()
            if not step_func():
                self.print_colored(f"❌ {step_name} 失败", "red")
                return False
        
        print()
        self.show_results()
        
        print()
        self.print_colored("=== 打包完成 ===", "bold")
        return True

def main():
    """主函数"""
    builder = NovelReaderBuilder()
    success = builder.build()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
