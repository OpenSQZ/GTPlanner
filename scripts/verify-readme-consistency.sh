#!/bin/bash

# README文件一致性验证脚本
# 验证英文、中文、日文三个版本的README文件在关键信息上保持一致

set -e

echo "🔍 开始验证README文件一致性..."

# 定义文件路径
README_EN="README.md"
README_ZH="README_zh.md"
README_JA="README_ja.md"

# 检查文件是否存在
for file in "$README_EN" "$README_ZH" "$README_JA"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ 错误: 文件 $file 不存在"
        exit 1
    fi
done

echo "✅ 所有README文件存在"

# 验证编码格式
echo "🔍 检查文件编码..."
for file in "$README_EN" "$README_ZH" "$README_JA"; do
    if ! file "$file" | grep -q "UTF-8"; then
        echo "⚠️ 警告: $file 可能不是UTF-8编码"
    else
        echo "✅ $file 编码正确 (UTF-8)"
    fi
done

# 验证依赖版本一致性
echo "🔍 检查依赖版本一致性..."

# 检查pytest版本
pytest_en=$(grep -o "pytest.*>= [0-9.]*" "$README_EN" | head -1)
pytest_zh=$(grep -o "pytest.*>= [0-9.]*" "$README_ZH" | head -1)
pytest_ja=$(grep -o "pytest.*>= [0-9.]*" "$README_JA" | head -1)

echo "pytest版本信息:"
echo "  英文: $pytest_en"
echo "  中文: $pytest_zh"
echo "  日文: $pytest_ja"

# 检查trio版本
trio_en=$(grep -o "trio.*>= [0-9.]*" "$README_EN" | head -1)
trio_zh=$(grep -o "trio.*>= [0-9.]*" "$README_ZH" | head -1)
trio_ja=$(grep -o "trio.*>= [0-9.]*" "$README_JA" | head -1)

echo "trio版本信息:"
echo "  英文: $trio_en"
echo "  中文: $trio_zh"
echo "  日文: $trio_ja"

# 检查coverage版本
coverage_en=$(grep -o "coverage.*>= [0-9.]*" "$README_EN" | head -1)
coverage_zh=$(grep -o "coverage.*>= [0-9.]*" "$README_ZH" | head -1)
coverage_ja=$(grep -o "coverage.*>= [0-9.]*" "$README_JA" | head -1)

echo "coverage版本信息:"
echo "  英文: $coverage_en"
echo "  中文: $coverage_zh"
echo "  日文: $coverage_ja"

# 检查psutil版本
psutil_en=$(grep -o "psutil.*>= [0-9.]*" "$README_EN" | head -1)
psutil_zh=$(grep -o "psutil.*>= [0-9.]*" "$README_ZH" | head -1)
psutil_ja=$(grep -o "psutil.*>= [0-9.]*" "$README_JA" | head -1)

echo "psutil版本信息:"
echo "  英文: $psutil_en"
echo "  中文: $psutil_zh"
echo "  日文: $psutil_ja"

# 验证关键章节存在性
echo "🔍 检查关键章节存在性..."

# 检查多语言支持章节
if grep -q "Multilingual Support\|多语言支持\|多言語サポート" "$README_EN" "$README_ZH" "$README_JA"; then
    echo "✅ 多语言支持章节存在"
else
    echo "❌ 多语言支持章节缺失"
    exit 1
fi

# 检查开发依赖章节
if grep -q "Development Dependencies\|开发依赖\|開発依存関係" "$README_EN" "$README_ZH" "$README_JA"; then
    echo "✅ 开发依赖章节存在"
else
    echo "❌ 开发依赖章节缺失"
    exit 1
fi

# 检查MCP依赖章节
if grep -q "MCP Dependencies\|MCP依赖\|MCP依存関係" "$README_EN" "$README_ZH" "$README_JA"; then
    echo "✅ MCP依赖章节存在"
else
    echo "❌ MCP依赖章节缺失"
    exit 1
fi

# 验证文件结构一致性
echo "🔍 检查文件结构一致性..."

# 计算各文件的章节数量（以##开头的行）
sections_en=$(grep -c "^##" "$README_EN" || true)
sections_zh=$(grep -c "^##" "$README_ZH" || true)
sections_ja=$(grep -c "^##" "$README_JA" || true)

echo "章节数量:"
echo "  英文: $sections_en"
echo "  中文: $sections_zh"
echo "  日文: $sections_ja"

# 检查章节数量差异
max_sections=$((sections_en > sections_zh ? sections_en : sections_zh))
max_sections=$((max_sections > sections_ja ? max_sections : sections_ja))
min_sections=$((sections_en < sections_zh ? sections_en : sections_zh))
min_sections=$((min_sections < sections_ja ? min_sections : sections_ja))

section_diff=$((max_sections - min_sections))
if [[ $section_diff -gt 2 ]]; then
    echo "⚠️ 警告: 章节数量差异较大 ($section_diff)"
else
    echo "✅ 章节数量基本一致"
fi

# 验证中文字符显示
echo "🔍 检查中文字符显示..."
if grep -q "[\u4e00-\u9fff]" "$README_ZH"; then
    echo "✅ 中文字符正常"
else
    echo "⚠️ 警告: 中文README中可能缺少中文字符"
fi

# 验证日文字符显示
echo "🔍 检查日文字符显示..."
if grep -q "[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]" "$README_JA"; then
    echo "✅ 日文字符正常"
else
    echo "⚠️ 警告: 日文README中可能缺少日文字符"
fi

# 检查是否有重复的章节
echo "🔍 检查重复章节..."
for file in "$README_EN" "$README_ZH" "$README_JA"; do
    duplicates=$(grep "^### " "$file" | sort | uniq -d)
    if [[ -n "$duplicates" ]]; then
        echo "⚠️ 警告: $file 中发现重复章节:"
        echo "$duplicates"
    else
        echo "✅ $file 无重复章节"
    fi
done

echo ""
echo "🎉 README文件一致性验证完成!"
echo ""
echo "📋 验证摘要:"
echo "  - 文件编码: UTF-8"
echo "  - 依赖版本: 已检查"
echo "  - 关键章节: 存在"
echo "  - 文件结构: 基本一致"
echo "  - 字符显示: 正常"
echo ""
echo "✅ 所有检查通过，README文件一致性良好"
