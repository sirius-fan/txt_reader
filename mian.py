#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 文本小说阅读器
功能包括：
- 打开和阅读txt文件
- 章节导航和跳转
- 字体设置（字体、大小）
- 颜色设置（背景色、字体色）
- 页码显示
- 全文搜索
"""

import sys
import os
import re
import chardet
from typing import List, Tuple, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QPushButton,
    QLabel, QLineEdit, QSpinBox, QColorDialog, QFontDialog,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar, QMenu,
    QToolBar, QFrame, QScrollArea, QSlider, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings
from PySide6.QtGui import QFont, QColor, QPalette, QAction, QIcon, QTextCursor


DEBUG_MODE = False  # 是否启用调试模式

def print_debug(message: str):
    """打印调试信息"""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")


class ChapterParser:
    """章节解析器"""
    
    @staticmethod
    def parse_chapters(text: str) -> List[Tuple[str, int, int]]:
        """
        解析章节
        输出: [(章节名, 开始位置, 结束位置), ...]
        """
        chapters = []
        
        # 多种章节标题模式
        patterns = [
            r'^第[零一二三四五六七八九十百千万0-9]+章.*?$',
            r'^第[0-9]+章.*?$',
            r'^Chapter\s*[0-9]+.*?$',
            r'^章节[0-9]+.*?$',
            r'^[0-9]+\..*?$',
            r'^第[零一二三四五六七八九十百千万0-9]+节.*?$',
        ]
        
        combined_pattern = '|'.join(f'({pattern})' for pattern in patterns)
        
        lines = text.split('\n')
        print_debug(f"Lines to process: {(lines)}")  # Debug output
        current_pos = 0
        
        for i, line in enumerate(lines):
            line_match = line.strip()
            if line_match and re.match(combined_pattern, line_match, re.IGNORECASE):
                print_debug(f"Found chapter: {line} (pos: {current_pos})")  # Debug output
                if chapters:
                    # 更新上一章的结束位置
                    chapters[-1] = (chapters[-1][0], chapters[-1][1], current_pos)
                
                chapters.append((line, current_pos, len(text)))
            
            current_pos += len(line) + 1  # +1 for newline
            print_debug(f"Processing line {i+1}: {line} (pos: {current_pos})")  # Debug output

        print_debug(f"Total chapters found: {chapters}")  # Debug output

        # 如果没有找到章节，将整个文本作为一章
        if not chapters:
            chapters.append(("全文", 0, len(text)))
        
        return chapters


class SearchThread(QThread):
    """搜索线程"""
    result_found = Signal(int, str)  # 位置, 上下文
    finished_search = Signal(int)    # 总结果数
    
    def __init__(self, text: str, keyword: str, case_sensitive: bool = False):
        super().__init__()
        self.text = text
        self.keyword = keyword
        self.case_sensitive = case_sensitive
        self.results = []
    
    def run(self):
        if not self.keyword:
            self.finished_search.emit(0)
            return
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        pattern = re.escape(self.keyword)
        
        for match in re.finditer(pattern, self.text, flags):
            start = match.start()
            # 获取上下文（前后各50个字符）
            context_start = max(0, start - 50)
            context_end = min(len(self.text), start + len(self.keyword) + 50)
            context = self.text[context_start:context_end]
            
            self.results.append((start, context))
            self.result_found.emit(start, context)
        
        self.finished_search.emit(len(self.results))


class NovelReader(QMainWindow):
    """小说阅读器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("NovelReader", "Settings")
        self.text_content = ""
        self.chapters = []
        self.current_chapter = 0
        self.search_results = []
        self.current_search_index = -1
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("PySide6 小说阅读器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主界面
        self.create_main_widget()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 编码选择菜单
        encoding_menu = file_menu.addMenu("重新编码打开")
        
        common_encodings = [
            ('UTF-8', 'utf-8'),
            ('GBK (简体中文)', 'gbk'),
            ('GB2312 (简体中文)', 'gb2312'),
            ('Big5 (繁体中文)', 'big5'),
            ('UTF-16', 'utf-16'),
            ('ASCII', 'ascii'),
        ]
        
        for name, encoding in common_encodings:
            encoding_action = QAction(name, self)
            encoding_action.triggered.connect(lambda checked, enc=encoding: self.open_file_with_encoding(enc))
            encoding_menu.addAction(encoding_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        font_action = QAction("字体设置(&F)", self)
        font_action.setShortcut("Ctrl+Shift+F")
        font_action.triggered.connect(self.set_font)
        view_menu.addAction(font_action)
        
        view_menu.addSeparator()
        
        # 字体大小快捷菜单
        font_size_menu = view_menu.addMenu("字体大小")
        
        sizes = [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
        for size in sizes:
            size_action = QAction(f"{size}号", self)
            size_action.triggered.connect(lambda checked, s=size: self.set_font_size_direct(s))
            font_size_menu.addAction(size_action)
        
        view_menu.addSeparator()
        
        bg_color_action = QAction("背景颜色(&B)", self)
        bg_color_action.triggered.connect(self.set_background_color)
        view_menu.addAction(bg_color_action)
        
        text_color_action = QAction("字体颜色(&T)", self)
        text_color_action.triggered.connect(self.set_text_color)
        view_menu.addAction(text_color_action)
        
        view_menu.addSeparator()
        
        # 预设主题
        theme_menu = view_menu.addMenu("预设主题")
        
        default_theme = QAction("默认主题", self)
        default_theme.triggered.connect(self.apply_default_theme)
        theme_menu.addAction(default_theme)
        
        dark_theme = QAction("护眼深色", self)
        dark_theme.triggered.connect(self.apply_dark_theme)
        theme_menu.addAction(dark_theme)
        
        sepia_theme = QAction("护眼米黄", self)
        sepia_theme.triggered.connect(self.apply_sepia_theme)
        theme_menu.addAction(sepia_theme)
        
        # 搜索菜单
        search_menu = menubar.addMenu("搜索(&S)")
        
        search_action = QAction("查找(&F)", self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.show_search_panel)
        search_menu.addAction(search_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 打开文件
        open_action = QAction("打开", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 字体设置
        font_action = QAction("字体", self)
        font_action.triggered.connect(self.set_font)
        toolbar.addAction(font_action)
        
        # 字体大小调节
        toolbar.addWidget(QLabel("字体大小:"))
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(8, 72)
        self.font_size_slider.setValue(12)
        self.font_size_slider.setMaximumWidth(100)
        self.font_size_slider.valueChanged.connect(self.change_font_size)
        toolbar.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel("12")
        toolbar.addWidget(self.font_size_label)
        
        # 字体大小快捷按钮
        font_smaller_btn = QPushButton("-")
        font_smaller_btn.setMaximumWidth(30)
        font_smaller_btn.clicked.connect(self.decrease_font_size)
        toolbar.addWidget(font_smaller_btn)
        
        font_larger_btn = QPushButton("+")
        font_larger_btn.setMaximumWidth(30)
        font_larger_btn.clicked.connect(self.increase_font_size)
        toolbar.addWidget(font_larger_btn)
        
        toolbar.addSeparator()
        
        # 章节导航
        toolbar.addWidget(QLabel("章节:"))
        self.chapter_combo = QComboBox()
        self.chapter_combo.setMinimumWidth(200)
        self.chapter_combo.currentIndexChanged.connect(self.jump_to_chapter)
        toolbar.addWidget(self.chapter_combo)
    
    def create_main_widget(self):
        """创建主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 创建搜索面板
        self.create_search_panel()
        main_layout.addWidget(self.search_frame)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addLayout(QHBoxLayout())
        main_layout.addWidget(splitter)
        
        # 章节列表
        self.chapter_tree = QTreeWidget()
        self.chapter_tree.setHeaderLabel("章节目录")
        self.chapter_tree.setMaximumWidth(300)
        self.chapter_tree.itemClicked.connect(self.on_chapter_clicked)
        splitter.addWidget(self.chapter_tree)
        
        # 文本显示区域
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("微软雅黑", 12))
        splitter.addWidget(self.text_area)
        
        # 设置分割器比例
        splitter.setSizes([300, 900])
    
    def create_search_panel(self):
        """创建搜索面板"""
        self.search_frame = QFrame()
        self.search_frame.setFrameStyle(QFrame.StyledPanel)
        self.search_frame.hide()
        
        search_layout = QHBoxLayout(self.search_frame)
        
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_input = QLineEdit()
        self.search_input.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.search_input)
        
        self.case_sensitive_cb = QCheckBox("区分大小写")
        search_layout.addWidget(self.case_sensitive_cb)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.start_search)
        search_layout.addWidget(search_btn)
        
        prev_btn = QPushButton("上一个")
        prev_btn.clicked.connect(self.find_previous)
        search_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("下一个")
        next_btn.clicked.connect(self.find_next)
        search_layout.addWidget(next_btn)
        
        self.search_info_label = QLabel("")
        search_layout.addWidget(self.search_info_label)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.hide_search_panel)
        search_layout.addWidget(close_btn)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 页码信息
        self.page_label = QLabel("页码: 0/0")
        self.status_bar.addPermanentWidget(self.page_label)
        
        # 字符位置信息
        self.position_label = QLabel("位置: 0")
        self.status_bar.addPermanentWidget(self.position_label)
        
        # 连接光标位置变化信号
        self.text_area.cursorPositionChanged.connect(self.update_position_info)
    
    def detect_encoding(self, file_path):
        """
        检测文件编码，优先支持中文编码
        """
        # 常见的中文编码列表，按优先级排序
        encodings_to_try = [
            'utf-8',           # UTF-8
            'gbk',             # GBK (简体中文)
            'gb2312',          # GB2312 (简体中文)
            'big5',            # Big5 (繁体中文)
            'utf-16',          # UTF-16
            'utf-16le',        # UTF-16 Little Endian
            'utf-16be',        # UTF-16 Big Endian
            'ascii',           # ASCII
        ]
        
        try:
            # 读取文件前面部分进行编码检测
            with open(file_path, 'rb') as f:
                raw_data = f.read(10240)  # 读取前10KB用于检测
            
            # 使用 chardet 检测编码
            detected = chardet.detect(raw_data)
            detected_encoding = detected.get('encoding', '').lower()
            confidence = detected.get('confidence', 0)
            
            print_debug(f"Chardet 检测结果: {detected_encoding}, 置信度: {confidence}")
            
            # 如果 chardet 检测置信度很高，直接使用
            if confidence > 0.8 and detected_encoding:
                # 标准化编码名称
                if detected_encoding in ['gb2312', 'gbk', 'gb18030']:
                    return 'gbk'  # 统一使用 GBK，因为它兼容 GB2312
                elif detected_encoding.startswith('utf-8'):
                    return 'utf-8'
                elif detected_encoding.startswith('big5'):
                    return 'big5'
                else:
                    return detected_encoding
            
            # 如果 chardet 检测不够可靠，逐个尝试编码
            for encoding in encodings_to_try:
                try:
                    # 尝试解码整个文件
                    with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                        # 如果成功读取且包含中文字符，优先选择
                        if self.contains_chinese(content):
                            print(f"通过中文检测选择编码: {encoding}")
                            return encoding
                        elif encoding == 'utf-8':
                            print(f"默认使用 UTF-8 编码")
                            return encoding
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # 如果所有编码都失败，使用 chardet 的结果或默认 UTF-8
            return detected_encoding if detected_encoding else 'utf-8'
            
        except Exception as e:
            print(f"编码检测出错: {e}")
            return 'utf-8'  # 默认返回 UTF-8
    
    def contains_chinese(self, text):
        """
        检查文本是否包含中文字符
        """
        import re
        # 匹配中文字符范围
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        return bool(chinese_pattern.search(text[:1000]))  # 只检查前1000个字符
    
    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文本文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        
        if file_path:
            try:
                # 检测文件编码
                encoding = self.detect_encoding(file_path)
                
                # 读取文件内容
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    self.text_content = f.read()
                
                # 解析章节
                self.chapters = ChapterParser.parse_chapters(self.text_content)
                
                # 更新界面
                self.update_chapter_list()
                self.update_chapter_combo()
                self.display_chapter(0)
                
                self.status_bar.showMessage(f"已加载文件: {os.path.basename(file_path)} (编码: {encoding})")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")
    
    def open_file_with_encoding(self, encoding):
        """使用指定编码打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"使用 {encoding.upper()} 编码打开文本文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        
        if file_path:
            try:
                # 使用指定编码读取文件内容
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    self.text_content = f.read()
                
                # 解析章节
                self.chapters = ChapterParser.parse_chapters(self.text_content)
                
                # 更新界面
                self.update_chapter_list()
                self.update_chapter_combo()
                self.display_chapter(0)
                
                self.status_bar.showMessage(f"已加载文件: {os.path.basename(file_path)} (强制编码: {encoding.upper()})")
                
            except Exception as e:
                QMessageBox.critical(self, "编码错误", 
                                   f"使用 {encoding.upper()} 编码打开文件失败:\n{str(e)}\n\n"
                                   f"请尝试其他编码或使用自动检测。")
    
    def update_chapter_list(self):
        """更新章节列表"""
        self.chapter_tree.clear()
        
        for i, (title, start, end) in enumerate(self.chapters):
            item = QTreeWidgetItem([f"{i+1:02d}. {title}"])
            item.setData(0, Qt.UserRole, i)
            self.chapter_tree.addTopLevelItem(item)
    
    def update_chapter_combo(self):
        """更新章节下拉框"""
        self.chapter_combo.clear()
        
        for i, (title, start, end) in enumerate(self.chapters):
            self.chapter_combo.addItem(f"{i+1:02d}. {title}")
    
    def display_chapter(self, chapter_index: int):
        """显示指定章节"""
        if 0 <= chapter_index < len(self.chapters):
            self.current_chapter = chapter_index
            title, start, end = self.chapters[chapter_index]
            
            chapter_text = self.text_content[start:end]
            self.text_area.setPlainText(chapter_text)
            self.text_area.moveCursor(QTextCursor.Start)
            
            # 更新章节选择
            self.chapter_combo.setCurrentIndex(chapter_index)
            
            # 高亮当前章节
            for i in range(self.chapter_tree.topLevelItemCount()):
                item = self.chapter_tree.topLevelItem(i)
                if i == chapter_index:
                    item.setSelected(True)
                    self.chapter_tree.scrollToItem(item)
                else:
                    item.setSelected(False)
            
            self.update_position_info()
    
    def on_chapter_clicked(self, item, column):
        """章节列表点击事件"""
        chapter_index = item.data(0, Qt.UserRole)
        if chapter_index is not None:
            self.display_chapter(chapter_index)
    
    def jump_to_chapter(self, index):
        """跳转到指定章节"""
        if index >= 0:
            self.display_chapter(index)
    
    def change_font_size(self, size):
        """改变字体大小"""
        self.font_size_label.setText(str(size))
        font = self.text_area.font()
        font.setPointSize(size)
        self.text_area.setFont(font)
    
    def set_font_size_direct(self, size):
        """直接设置字体大小"""
        self.font_size_slider.setValue(size)
        self.change_font_size(size)
    
    def increase_font_size(self):
        """增大字体"""
        current_size = self.font_size_slider.value()
        new_size = min(72, current_size + 2)
        self.font_size_slider.setValue(new_size)
    
    def decrease_font_size(self):
        """减小字体"""
        current_size = self.font_size_slider.value()
        new_size = max(8, current_size - 2)
        self.font_size_slider.setValue(new_size)
    
    def set_font(self):
        """设置字体"""
        current_font = self.text_area.font()
        
        try:
            result = QFontDialog.getFont(current_font, self, "选择字体")
            
            # QFontDialog.getFont 返回 (ok, font) 元组，而不是(font, ok) 元组
            if isinstance(result, tuple) and len(result) == 2:
                ok,font = result
                
                if ok and isinstance(font, QFont):
                    self.text_area.setFont(font)
                    self.font_size_slider.setValue(font.pointSize())
                    self.font_size_label.setText(str(font.pointSize()))
                    
                    # 显示当前字体信息
                    font_info = f"字体已更改为: {font.family()} {font.pointSize()}号"
                    if font.bold():
                        font_info += " 粗体"
                    if font.italic():
                        font_info += " 斜体"
                    
                    self.status_bar.showMessage(font_info, 3000)  # 显示3秒
                else:
                    self.status_bar.showMessage("字体设置已取消", 2000)
            else:
                self.status_bar.showMessage("字体对话框返回异常", 2000)
                
        except Exception as e:
            QMessageBox.warning(self, "字体设置错误", f"设置字体时出现错误:\n{str(e)}")
            self.status_bar.showMessage("字体设置失败", 2000)
    
    def set_background_color(self):
        """设置背景颜色"""
        color = QColorDialog.getColor(Qt.white, self, "选择背景颜色")
        if color.isValid():
            palette = self.text_area.palette()
            palette.setColor(QPalette.Base, color)
            self.text_area.setPalette(palette)
            self.status_bar.showMessage(f"背景颜色已更改为: {color.name()}", 3000)
    
    def set_text_color(self):
        """设置文字颜色"""
        color = QColorDialog.getColor(Qt.black, self, "选择文字颜色")
        if color.isValid():
            palette = self.text_area.palette()
            palette.setColor(QPalette.Text, color)
            self.text_area.setPalette(palette)
            self.status_bar.showMessage(f"文字颜色已更改为: {color.name()}", 3000)
    
    def apply_default_theme(self):
        """应用默认主题"""
        # 白色背景，黑色文字
        palette = self.text_area.palette()
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        self.text_area.setPalette(palette)
        self.status_bar.showMessage("已应用默认主题", 2000)
    
    def apply_dark_theme(self):
        """应用深色主题"""
        # 深灰色背景，浅色文字
        palette = self.text_area.palette()
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.Text, QColor(220, 220, 220))
        self.text_area.setPalette(palette)
        self.status_bar.showMessage("已应用护眼深色主题", 2000)
    
    def apply_sepia_theme(self):
        """应用护眼米黄主题"""
        # 米黄色背景，深棕色文字
        palette = self.text_area.palette()
        palette.setColor(QPalette.Base, QColor(250, 240, 210))
        palette.setColor(QPalette.Text, QColor(101, 67, 33))
        self.text_area.setPalette(palette)
        self.status_bar.showMessage("已应用护眼米黄主题", 2000)
    
    def show_search_panel(self):
        """显示搜索面板"""
        self.search_frame.show()
        self.search_input.setFocus()
    
    def hide_search_panel(self):
        """隐藏搜索面板"""
        self.search_frame.hide()
        self.search_results.clear()
        self.current_search_index = -1
        
        # 清除高亮
        cursor = self.text_area.textCursor()
        cursor.clearSelection()
        self.text_area.setTextCursor(cursor)
    
    def start_search(self):
        """开始搜索"""
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        
        case_sensitive = self.case_sensitive_cb.isChecked()
        
        # 清空之前的搜索结果
        self.search_results.clear()
        self.current_search_index = -1
        
        # 在当前章节中搜索
        current_text = self.text_area.toPlainText()
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(keyword)
        
        for match in re.finditer(pattern, current_text, flags):
            self.search_results.append(match.start())
        
        if self.search_results:
            self.current_search_index = 0
            self.highlight_search_result()
            self.search_info_label.setText(f"找到 {len(self.search_results)} 个结果")
        else:
            self.search_info_label.setText("未找到结果")
    
    def find_next(self):
        """查找下一个"""
        if self.search_results and self.current_search_index < len(self.search_results) - 1:
            self.current_search_index += 1
            self.highlight_search_result()
    
    def find_previous(self):
        """查找上一个"""
        if self.search_results and self.current_search_index > 0:
            self.current_search_index -= 1
            self.highlight_search_result()
    
    def highlight_search_result(self):
        """高亮搜索结果"""
        if self.search_results and 0 <= self.current_search_index < len(self.search_results):
            position = self.search_results[self.current_search_index]
            keyword = self.search_input.text()
            
            # 设置光标位置并选中关键词
            cursor = self.text_area.textCursor()
            cursor.setPosition(position)
            cursor.setPosition(position + len(keyword), QTextCursor.KeepAnchor)
            self.text_area.setTextCursor(cursor)
            
            # 确保可见
            self.text_area.ensureCursorVisible()
            
            # 更新搜索信息
            self.search_info_label.setText(
                f"{self.current_search_index + 1}/{len(self.search_results)}")
    
    def update_position_info(self):
        """更新位置信息"""
        cursor = self.text_area.textCursor()
        position = cursor.position()
        
        # 计算页码（假设每页1000字符）
        chars_per_page = 1000
        current_page = position // chars_per_page + 1
        total_pages = len(self.text_area.toPlainText()) // chars_per_page + 1
        
        self.page_label.setText(f"页码: {current_page}/{total_pages}")
        self.position_label.setText(f"位置: {position}")
    
    def load_settings(self):
        """加载设置"""
        # 恢复窗口几何尺寸
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复字体设置
        font_family = self.settings.value("font_family", "微软雅黑")
        font_size = int(self.settings.value("font_size", 12))
        font_bold = self.settings.value("font_bold", "false") == "true"
        font_italic = self.settings.value("font_italic", "false") == "true"
        
        font = QFont(font_family, font_size)
        font.setBold(font_bold)
        font.setItalic(font_italic)
        
        self.text_area.setFont(font)
        self.font_size_slider.setValue(font_size)
        self.font_size_label.setText(str(font_size))
        
        # 恢复颜色设置
        bg_color = self.settings.value("bg_color", "#ffffff")
        text_color = self.settings.value("text_color", "#000000")
        
        palette = self.text_area.palette()
        palette.setColor(QPalette.Base, QColor(bg_color))
        palette.setColor(QPalette.Text, QColor(text_color))
        self.text_area.setPalette(palette)
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        
        font = self.text_area.font()
        self.settings.setValue("font_family", font.family())
        self.settings.setValue("font_size", font.pointSize())
        self.settings.setValue("font_bold", font.bold())
        self.settings.setValue("font_italic", font.italic())
        
        palette = self.text_area.palette()
        self.settings.setValue("bg_color", palette.color(QPalette.Base).name())
        self.settings.setValue("text_color", palette.color(QPalette.Text).name())
    
    def closeEvent(self, event):
        """关闭事件"""
        self.save_settings()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("PySide6 小说阅读器")
    app.setOrganizationName("NovelReader")
    
    reader = NovelReader()
    reader.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()