#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试编码支持功能
"""

import chardet
import os

def test_encoding_detection(file_path):
    """测试编码检测功能"""
    print(f"=== 测试文件: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 使用 chardet 检测
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        detected = chardet.detect(raw_data)
        print(f"Chardet 检测结果: {detected}")
    
    # 尝试不同编码读取
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()[:100]  # 只读前100个字符
                print(f"✓ {encoding}: 成功读取 - {repr(content)}")
        except Exception as e:
            print(f"✗ {encoding}: 失败 - {str(e)}")
    
    print()

def create_test_files():
    """创建不同编码的测试文件"""
    content = """第一章 测试章节

这是一个测试文件，包含中文字符。
测试编码检测和显示功能。

第二章 更多内容

包含各种中文字符和标点符号。
"""
    
    # 创建不同编码的文件
    encodings = [
        ('utf-8', 'test_utf8.txt'),
        ('gbk', 'test_gbk_manual.txt'),
        ('gb2312', 'test_gb2312.txt'),
    ]
    
    for encoding, filename in encodings:
        try:
            with open(filename, 'w', encoding=encoding) as f:
                f.write(content)
            print(f"✓ 创建文件: {filename} ({encoding})")
        except Exception as e:
            print(f"✗ 创建文件失败: {filename} - {str(e)}")

if __name__ == "__main__":
    print("=== 编码支持测试 ===\n")
    
    # 创建测试文件
    create_test_files()
    print()
    
    # 测试编码检测
    test_files = [
        'test.txt',
        'test_utf8.txt', 
        'test_gbk_manual.txt',
        'test_gb2312.txt',
        'test_gbk_encoded.txt'
    ]
    
    for file_path in test_files:
        test_encoding_detection(file_path)
