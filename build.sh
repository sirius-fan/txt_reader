#!/bin/bash
# PySide6 小说阅读器 - 一键打包脚本

set -e  # 遇到错误立即退出

echo "=== PySide6 小说阅读器打包脚本 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 环境
echo "🔍 检查环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装${NC}"
    exit 1
fi

python3 --version
echo ""

# 检查和安装依赖
echo "📦 检查依赖包..."

check_and_install() {
    package=$1
    echo -n "检查 $package... "
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✅ 已安装${NC}"
    else
        echo -e "${YELLOW}⚠️  未安装，正在安装...${NC}"
        pip3 install $package
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ $package 安装成功${NC}"
        else
            echo -e "${RED}❌ $package 安装失败${NC}"
            exit 1
        fi
    fi
}

check_and_install "PySide6"
check_and_install "chardet"
check_and_install "PyInstaller"

echo ""

# 清理之前的构建文件
echo "🧹 清理构建目录..."
rm -rf build dist __pycache__ *.spec NovelReader_Portable
echo "清理完成"
echo ""

# 检查主程序文件
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ 找不到主程序文件 main.py${NC}"
    exit 1
fi

# 开始打包
echo "🚀 开始打包..."
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

# PyInstaller 打包命令
pyinstaller \
    --onefile \
    --noconsole \
    --windowed \
    --clean \
    --noconfirm \
    --name "小说阅读器" \
    --add-data "test.txt:." \
    --add-data "README.md:." \
    --hidden-import chardet \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtGui \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module scipy \
    --exclude-module pandas \
    --exclude-module jupyter \
    --exclude-module IPython \
    main.py

# 检查打包结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 打包成功！${NC}"
    echo ""
    
    # 检查生成的文件
    if [ -f "dist/小说阅读器" ]; then
        echo "📄 输出文件: dist/小说阅读器"
        
        # 显示文件大小
        file_size=$(du -h "dist/小说阅读器" | cut -f1)
        echo "📏 文件大小: $file_size"
        
        # 设置执行权限
        chmod +x "dist/小说阅读器"
        echo "🔐 已设置执行权限"
        
        echo ""
        echo -e "${GREEN}🚀 使用方法:${NC}"
        echo "  ./dist/小说阅读器"
        echo ""
        echo "或者双击运行文件管理器中的可执行文件"
        
        # 创建便携版
        echo ""
        echo "📦 创建便携版..."
        mkdir -p NovelReader_Portable
        cp "dist/小说阅读器" NovelReader_Portable/
        cp README.md NovelReader_Portable/
        cp test.txt NovelReader_Portable/
        
        # 创建启动脚本
        cat > NovelReader_Portable/启动.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./小说阅读器
EOF
        chmod +x NovelReader_Portable/启动.sh
        
        echo -e "${GREEN}✅ 便携版已创建: NovelReader_Portable/${NC}"
        echo ""
        echo "便携版使用方法:"
        echo "  1. 复制整个 NovelReader_Portable 文件夹到任意位置"
        echo "  2. 运行 ./NovelReader_Portable/小说阅读器"
        echo "  3. 或运行 ./NovelReader_Portable/启动.sh"
        
    else
        echo -e "${RED}❌ 找不到生成的可执行文件${NC}"
        exit 1
    fi
    
else
    echo ""
    echo -e "${RED}❌ 打包失败！${NC}"
    echo "请检查上面的错误信息"
    exit 1
fi

echo ""
echo "=== 打包完成 ==="
