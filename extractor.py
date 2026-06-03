#!/usr/bin/env python3
"""
phagent/extractor.py — PH 提取辅助工具箱

功能：
- nutri：暴力组合提取（给定文本按指定模式排列组合）
- 词夹字 / 字夹词：从短语中按位置取字母
- 首尾字母提取：取每个单词/行的首字母或尾字母
- 索引提取：按给定索引序列取字母
- 对角线提取：从矩阵中取对角线字母
- 交叉比对：多组结果的交集分析

用法：
    python3 extractor.py nutri "文本内容" --pattern "数字模式"
    python3 extractor.py first "短语1 短语2 短语3"
    python3 extractor.py index "文本" --indices 1,3,5
    python3 extractor.py cross "abcd efgh ijkl" "3 2 4"
"""

import sys
import re
import argparse
from itertools import combinations, permutations
from collections import defaultdict

# ============================================================
# 工具函数
# ============================================================

def clean_word(w):
    """清理单词，只保留字母"""
    return re.sub(r'[^A-Za-z]', '', w)

def word_list(text):
    """将文本拆分为单词列表"""
    return [w for w in re.split(r'[\s,;:.!?()\[\]{}"\'\n]+', text) if w]

def split_lines(text):
    """按行拆分"""
    return [l.strip() for l in text.split('\n') if l.strip()]

# ============================================================
# Nutri 暴力组合
# ============================================================

def nutri_combine(items, pattern_str, item_sep=' '):
    """
    按数字模式组合提取
    
    "3 2 4" 表示：取第3项、第2项、第4项组合
    支持负数（从末尾数）："-1" 表示最后一项
    支持范围："1-3" 表示第1到第3项
    """
    parts = pattern_str.split()
    result = []
    for p in parts:
        if '-' in p:
            # 范围
            start, end = p.split('-')
            start = int(start)
            end = int(end)
            for i in range(start, end + 1):
                if 1 <= i <= len(items):
                    result.append(str(items[i - 1]))
        else:
            idx = int(p)
            if 1 <= idx <= len(items):
                result.append(str(items[idx - 1]))
            elif idx < 0 and abs(idx) <= len(items):
                result.append(str(items[idx]))
    return item_sep.join(result)

def nutri_bruteforce(items, pattern_str, item_sep=' '):
    """
    nutri 暴力：尝试多种组合方式
    支持命令式：每行长度不同的多种尝试
    """
    results = []
    # 直接按给定模式
    results.append(('direct', nutri_combine(items, pattern_str, item_sep)))
    
    # 如果模式中有逗号分隔的多组模式
    if ',' in pattern_str:
        for p in pattern_str.split(','):
            p = p.strip()
            if p:
                results.append((f'pattern({p})', nutri_combine(items, p, item_sep)))
    
    return results

def nutri_all_orders(items, length=None):
    """
    尝试所有排列组合（小规模用）
    items: 输入项列表
    length: 每组合取的项数，默认全取
    """
    results = []
    if length is None:
        length = len(items)
    
    # 如果项数太多，限制排列数量
    if len(items) > 6:
        results.append(('warning', '项数过多，只尝试前6项的首尾组合'))
        # 只取首尾各一些的组合
        prefix = ''.join(str(x)[0] for x in items[:3])
        suffix = ''.join(str(x)[0] for x in items[-3:])
        results.append(('prefix3', prefix))
        results.append(('suffix3', suffix))
        return results
    
    for perm in permutations(items, min(length, len(items))):
        result = ''.join(str(x) for x in perm)
        results.append((f'perm{"".join(str(items.index(x)) for x in perm)}', result))
    
    return results

# ============================================================
# 词夹字 / 字夹词
# ============================================================

def word_interleave(words):
    """
    词夹字：从多个单词中轮流取字母
    例如: "abc" + "def" → "adbecf"
    """
    if not words:
        return ""
    max_len = max(len(w) for w in words)
    result = []
    for i in range(max_len):
        for w in words:
            if i < len(w):
                result.append(w[i])
    return ''.join(result)

def nth_letter_each_word(text, n):
    """
    取每个单词的第 n 个字母（1-based）
    n=1: 首字母, n=-1: 尾字母
    """
    words = word_list(text)
    result = []
    for w in words:
        clean = clean_word(w)
        if clean:
            if n > 0 and n <= len(clean):
                result.append(clean[n-1])
            elif n < 0 and abs(n) <= len(clean):
                result.append(clean[n])
    return ''.join(result)

def first_letters(text):
    """取每个单词的首字母"""
    return nth_letter_each_word(text, 1)

def last_letters(text):
    """取每个单词的尾字母"""
    return nth_letter_each_word(text, -1)

def first_letters_lines(text):
    """取每行的首字母"""
    lines = split_lines(text)
    return ''.join(l[0] for l in lines if l and l[0].isalpha())

# ============================================================
# 索引提取
# ============================================================

def index_extract(text, indices_str, by='char'):
    """
    按索引序列取字符/单词
    
    by='char': 取第 N 个字符
    by='word': 取第 N 个单词
    支持范围如 "1,3,5" 或 "1-3,5"
    """
    if by == 'word':
        items = word_list(text)
    else:
        items = list(text)
    
    # 解析索引
    indices = []
    for part in indices_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            indices.extend(range(int(start.strip()), int(end.strip()) + 1))
        else:
            indices.append(int(part.strip()))
    
    result = []
    for idx in indices:
        if 1 <= idx <= len(items):
            result.append(str(items[idx - 1]))
    
    return ''.join(result) if by == 'char' else ' '.join(result)

# ============================================================
# 对角线提取
# ============================================================

def diagonal_extract(text, width=None):
    """
    从矩阵中提取对角线
    
    text: 多行文本或连续文本
    width: 矩阵宽度，自动检测
    """
    lines = split_lines(text)
    
    if width is None:
        # 尝试自动检测宽度（所有行等长）
        if lines:
            width = max(len(l) for l in lines)
    
    if not lines:
        return ""
    
    # 主对角线 (top-left to bottom-right)
    main_diag = []
    secondary_diag = []
    
    for i, line in enumerate(lines):
        if i < len(line):
            main_diag.append(line[i])
        if i < len(line):
            secondary_diag.append(line[-(i+1)])
    
    return {
        'main_diagonal': ''.join(main_diag),
        'secondary_diagonal': ''.join(secondary_diag),
    }

# ============================================================
# 交叉比对
# ============================================================

def cross_reference(groups, min_common=2):
    """
    多组结果的交叉比对，找出共同的字母/模式
    
    groups: 字符串列表，每组是一个结果
    min_common: 最少出现次数才算"共同"
    """
    from collections import Counter
    
    # 统计每个字符在所有组中的出现次数
    char_count = Counter()
    for g in groups:
        char_count.update(set(g.upper()))
    
    # 找出在至少 min_common 组中都出现的字符
    common = {c for c, count in char_count.items() if count >= min_common}
    
    # 找出每组独有的字符
    unique_per_group = []
    for g in groups:
        g_upper = g.upper()
        unique = set(g_upper) - common
        unique_per_group.append(''.join(sorted(unique)))
    
    return {
        'common_chars': ''.join(sorted(common)),
        'common_count': len(common),
        'unique_per_group': unique_per_group,
    }

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='PH 提取辅助工具箱')
    sub = parser.add_subparsers(dest='command', help='子命令')
    
    # nutri
    p_nutri = sub.add_parser('nutri', help='nutri 暴力组合')
    p_nutri.add_argument('text', help='输入文本')
    p_nutri.add_argument('--pattern', '-p', help='提取模式，如 "3 2 4"')
    p_nutri.add_argument('--all', '-a', action='store_true', help='尝试所有排列')
    
    # first
    p_first = sub.add_parser('first', help='取首字母')
    p_first.add_argument('text', help='输入文本')
    p_first.add_argument('--lines', '-l', action='store_true', help='按行取首字母（非按单词）')
    
    # last
    p_last = sub.add_parser('last', help='取尾字母')
    p_last.add_argument('text', help='输入文本')
    
    # nth
    p_nth = sub.add_parser('nth', help='取第 N 个字母')
    p_nth.add_argument('text', help='输入文本')
    p_nth.add_argument('--pos', '-p', type=int, required=True, help='位置（1-based）')
    
    # interleave
    p_int = sub.add_parser('interleave', help='词夹字（交错取字母）')
    p_int.add_argument('words', nargs='+', help='多个单词')
    
    # index
    p_idx = sub.add_parser('index', help='按索引取字符/单词')
    p_idx.add_argument('text', help='输入文本')
    p_idx.add_argument('--indices', '-i', required=True, help='索引，如 "1,3,5" 或 "1-3,5"')
    p_idx.add_argument('--by', choices=['char', 'word'], default='char', help='按字符还是按单词')
    
    # diagonal
    p_diag = sub.add_parser('diagonal', help='对角线提取')
    p_diag.add_argument('text', help='多行文本')
    
    # cross
    p_cross = sub.add_parser('cross', help='交叉比对')
    p_cross.add_argument('groups', nargs='+', help='多组结果')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'nutri':
        if args.all:
            items = word_list(args.text)
            results = nutri_all_orders(items)
            print(f"输入项: {items}")
            print(f"\n所有排列 (前{len(results)}个):")
            for name, result in results:
                print(f"  {name}: {result}")
        elif args.pattern:
            items = word_list(args.text) if ' ' in args.text else list(args.text)
            results = nutri_bruteforce(items, args.pattern)
            print(f"输入项: {items}")
            print(f"模式: {args.pattern}")
            for name, result in results:
                print(f"  [{name}] {result}")
        else:
            print("请指定 --pattern 模式或 --all 尝试所有排列")
    
    elif args.command == 'first':
        if args.lines:
            result = first_letters_lines(args.text)
            print(f"每行首字母: {result}")
        else:
            result = first_letters(args.text)
            print(f"每个单词首字母: {result}")
    
    elif args.command == 'last':
        result = last_letters(args.text)
        print(f"每个单词尾字母: {result}")
    
    elif args.command == 'nth':
        result = nth_letter_each_word(args.text, args.pos)
        print(f"每个单词第 {args.pos} 个字母: {result}")
    
    elif args.command == 'interleave':
        result = word_interleave(args.words)
        print(f"词夹字: {result}")
    
    elif args.command == 'index':
        result = index_extract(args.text, args.indices, args.by)
        print(f"按索引取{args.by}: {result}")
    
    elif args.command == 'diagonal':
        result = diagonal_extract(args.text)
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    elif args.command == 'cross':
        result = cross_reference(args.groups)
        print(f"共同字符 ({result['common_count']}个): {result['common_chars']}")
        for i, u in enumerate(result['unique_per_group']):
            print(f"  组{i+1}独有: {u}")


if __name__ == '__main__':
    main()
