#!/usr/bin/env python3
"""
phagent/decoder.py — PH 解码工具箱

支持以下编码/密码的识别与解码：
- 古典密码：凯撒、Atbash、维吉尼亚（自动找key）、ROT13
- 现代编码：base64/32/16、hex、二进制、莫尔斯电码、培根密码
- 字符操作：A1Z26、键盘移位
- 辅助：字母频率分析、自动检测编码类型

用法：
    python3 decoder.py "密文内容"
    python3 decoder.py --detect "未知编码内容"
"""

import sys
import base64
import re
import string
from collections import Counter

# ============================================================
# 基础工具
# ============================================================

def letter_frequency(text):
    """字母频率分析"""
    text = text.upper()
    freq = Counter(c for c in text if c in string.ascii_uppercase)
    total = sum(freq.values())
    if total == 0:
        return {}
    return {k: round(v/total*100, 1) for k, v in freq.most_common()}

def clean_text(text):
    """只保留字母，转大写"""
    return ''.join(c.upper() for c in text if c.isalpha())

# ============================================================
# 古典密码
# ============================================================

EN_FREQ_ORDER = "ETAOINSHRDLCUMWFGYPBVKJXQZ"

def caesar_decode(text, shift):
    """凯撒密码解码"""
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base - shift) % 26 + base))
        else:
            result.append(c)
    return ''.join(result)


def unicode_caesar_decode(text, shift):
    """Unicode 凯撒：对中文字符按 Unicode 码点偏移"""
    result = []
    for c in text:
        if ord(c) >= 0x4E00 and ord(c) <= 0x9FFF:
            # 只在 CJK 统一表意文字范围内循环
            new_code = ((ord(c) - 0x4E00 + shift) % (0x9FFF - 0x4E00 + 1)) + 0x4E00
            result.append(chr(new_code))
        else:
            result.append(c)
    return ''.join(result)

def unicode_caesar_bruteforce(text):
    """暴力破解 Unicode 凯撒，对 CJK 字符尝试偏移"""
    results = []
    for shift in range(1, 100):
        decoded = unicode_caesar_decode(text, shift)
        results.append((shift, decoded))
    return results

def unicode_caesar_auto(text):
    """自动猜测 Unicode 凯撒偏移"""
    results = unicode_caesar_bruteforce(text)
    # 返回前5个，实际使用时可能需要人工判断
    return results[:5]

def caesar_bruteforce(text):
    """暴力破解凯撒密码，返回所有可能结果"""
    results = []
    for shift in range(26):
        decoded = caesar_decode(text, shift)
        results.append((shift, decoded))
    return results

def caesar_auto(text):
    """自动猜测凯撒偏移量（基于频率分析）"""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    freq = letter_frequency(cleaned)
    if not freq:
        return []
    # 找出出现最多的字母，假设它是 E
    most_common = list(freq.keys())[0]
    # 计算偏移
    shift = (ord(most_common) - ord('E')) % 26
    # 返回前3个最可能的偏移量
    scored = []
    for s in range(26):
        decoded = caesar_decode(cleaned, s)
        # 统计解码后字母与英文频率的匹配度
        score = sum(1 for c in decoded[:20] if c.upper() in 'ETAOIN')
        scored.append((score, s, decoded))
    scored.sort(reverse=True)
    return [(s, caesar_decode(text, s)) for _, s, _ in scored[:3]]

def atbash_decode(text):
    """Atbash 密码解码（A↔Z, B↔Y, ...）"""
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr(base + (25 - (ord(c) - base))))
        else:
            result.append(c)
    return ''.join(result)

def rot13_decode(text):
    """ROT13 解码（凯撒偏移13，自逆）"""
    return caesar_decode(text, 13)

def vigenere_decode(text, key):
    """维吉尼亚密码解码"""
    result = []
    key = key.upper()
    key_len = len(key)
    key_idx = 0
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            shift = ord(key[key_idx % key_len]) - ord('A')
            result.append(chr((ord(c) - base - shift) % 26 + base))
            key_idx += 1
        else:
            result.append(c)
    return ''.join(result)

# ============================================================
# 现代编码
# ============================================================

def base64_decode(text):
    """Base64 解码"""
    try:
        # 添加补齐
        padding = 4 - len(text) % 4
        if padding != 4:
            text += '=' * padding
        return base64.b64decode(text).decode('utf-8', errors='replace')
    except:
        return None

def base32_decode(text):
    """Base32 解码"""
    try:
        padding = 8 - len(text) % 8
        if padding != 8:
            text += '=' * padding
        return base64.b32decode(text).decode('utf-8', errors='replace')
    except:
        return None

def base16_decode(text):
    """Base16 (Hex) 解码"""
    try:
        return bytes.fromhex(text).decode('utf-8', errors='replace')
    except:
        return None

def binary_decode(text):
    """二进制解码"""
    try:
        text = text.replace(' ', '').replace('\n', '')
        chars = [chr(int(text[i:i+8], 2)) for i in range(0, len(text), 8)]
        return ''.join(chars)
    except:
        return None

MORSE_CODE = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
    '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4',
    '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9',
}

def morse_decode(text):
    """莫尔斯电码解码"""
    try:
        text = text.strip()
        # 用 / 或 | 分隔单词，空格分隔字母
        words = re.split(r'\s*[\/|]\s*', text)
        result = []
        for word in words:
            letters = word.split()
            decoded_word = ''.join(MORSE_CODE.get(l, '?') for l in letters)
            result.append(decoded_word)
        return ' '.join(result)
    except:
        return None

# 培根密码
BACON_MAP = {
    'AAAAA': 'A', 'AAAAB': 'B', 'AAABA': 'C', 'AAABB': 'D', 'AABAA': 'E',
    'AABAB': 'F', 'AABBA': 'G', 'AABBB': 'H', 'ABAAA': 'I', 'ABAAB': 'K',
    'ABABA': 'L', 'ABABB': 'M', 'ABBAA': 'N', 'ABBAB': 'O', 'ABBBA': 'P',
    'ABBBB': 'Q', 'BAAAA': 'R', 'BAAAB': 'S', 'BAABA': 'T', 'BAABB': 'U',
    'BABAA': 'W', 'BABAB': 'X', 'BABBA': 'Y', 'BABBB': 'Z',
}

def bacon_decode(text):
    """培根密码解码（24字母版）"""
    try:
        text = clean_text(text)
        text = text.replace('A', 'A').replace('B', 'B')
        groups = [text[i:i+5] for i in range(0, len(text), 5)]
        result = ''.join(BACON_MAP.get(g, '?') for g in groups)
        return result
    except:
        return None

# ============================================================
# 字符操作
# ============================================================

def a1z26_decode(text):
    """A1Z26 解码（数字→字母）"""
    try:
        nums = re.findall(r'\d+', text)
        return ''.join(chr(int(n) + 64) for n in nums if 1 <= int(n) <= 26)
    except:
        return None

# 键盘移位映射（QWERTY 键盘，向左/右移一位）
QWERTY_LEFT = {}
QWERTY_RIGHT = {}

def keyboard_shift_decode(text, direction='left'):
    """键盘移位解码（暂未实现映射表）"""
    return None

# ============================================================
# 自动检测
# ============================================================

def detect_encoding(text):
    """尝试自动检测输入内容的编码类型"""
    text = text.strip()
    clues = []

    # Base64 特征：大小写字母+数字+可能以=结尾
    if re.match(r'^[A-Za-z0-9+/]+={0,2}$', text) and len(text) > 10:
        decoded = base64_decode(text)
        if decoded and all(c in string.printable for c in decoded):
            clues.append(('base64', decoded[:100]))

    # Base32：只含大写字母和数字
    if re.match(r'^[A-Z2-7]+={0,6}$', text) and len(text) > 8:
        decoded = base32_decode(text)
        if decoded:
            clues.append(('base32', decoded[:100]))

    # Hex：只含 0-9 A-F a-f
    if re.match(r'^[0-9A-Fa-f]+$', text) and len(text) > 4:
        decoded = base16_decode(text)
        if decoded:
            clues.append(('hex', decoded[:100]))

    # 二进制：只含 0 1
    if re.match(r'^[01\s]+$', text):
        decoded = binary_decode(text)
        if decoded:
            clues.append(('binary', decoded[:100]))

    # 莫尔斯：只含 . - / 和空格
    if re.match(r'^[.\-\s/|]+$', text):
        decoded = morse_decode(text)
        if decoded:
            clues.append(('morse', decoded[:100]))

    # A1Z26：数字+分隔符
    nums = re.findall(r'\d+', text)
    if nums and all(1 <= int(n) <= 26 for n in nums):
        decoded = a1z26_decode(text)
        if decoded:
            clues.append(('a1z26', decoded[:100]))

    # 培根：只含 A B
    if re.match(r'^[AB\s]+$', text.upper()):
        decoded = bacon_decode(text)
        if decoded:
            clues.append(('bacon', decoded[:100]))

    # Atbash：频率检测
    cleaned = clean_text(text)
    if len(cleaned) > 5:
        decoded = atbash_decode(text)
        # 简单检测：解码后是否包含常见英文单词
        common_words = ['THE', 'AND', 'THAT', 'HAVE', 'THIS']
        upper_decoded = decoded.upper()
        if any(w in upper_decoded for w in common_words):
            clues.append(('atbash', decoded[:100]))

    return clues

# ============================================================
# 主入口
# ============================================================

def decode_all(text):
    """尝试所有可能的解码方式"""
    results = []

    # 凯撒暴力
    try:
        cleaned = clean_text(text)
        if len(cleaned) > 2:
            best = caesar_auto(text)
            for shift, decoded in best[:2]:
                results.append(('caesar_shift_' + str(shift), decoded[:200]))
    except:
        pass

    # 基础编码
    for name, func in [
        ('atbash', atbash_decode),
        ('rot13', rot13_decode),
        ('base64', base64_decode),
        ('base32', base32_decode),
        ('hex', base16_decode),
        ('binary', binary_decode),
        ('morse', morse_decode),
        ('a1z26', a1z26_decode),
        ('bacon', bacon_decode),
    ]:
        try:
            decoded = func(text)
            if decoded and len(decoded) > 0:
                results.append((name, decoded[:200]))
        except:
            pass
    
    # 尝试 Unicode 凯撒（如果文本包含中文）
    if any(ord(c) >= 0x4E00 and ord(c) <= 0x9FFF for c in text):
        for shift in range(1, 20):
            try:
                decoded = unicode_caesar_decode(text, shift)
                if decoded and decoded != text:
                    results.append((f'unicode_caesar_+{shift}', decoded[:200]))
            except:
                pass
        try:
            decoded = func(text)
            if decoded and len(decoded) > 0:
                results.append((name, decoded[:200]))
        except:
            pass

    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python3 decoder.py <密文> [--detect]")
        print("       python3 decoder.py --all <密文>")
        sys.exit(1)

    args = sys.argv[1:]

    use_llm = '--llm' in args or '-l' in args
    if use_llm:
        args = [a for a in args if a not in ('--llm', '-l')]

    if '--detect' in args or '-d' in args:
        idx = args.index('--detect') if '--detect' in args else args.index('-d')
        text = args[idx + 1] if len(args) > idx + 1 else sys.stdin.read().strip()
        print("🔍 自动检测编码类型：")
        results = detect_encoding(text)
        if results:
            for name, decoded in results:
                print(f"  [{name}] {decoded}")
        else:
            print("  未识别出已知编码类型")
        return

    if '--all' in args or '-a' in args:
        idx = args.index('--all') if '--all' in args else args.index('-a')
        text = args[idx + 1] if len(args) > idx + 1 else sys.stdin.read().strip()
        print("🔧 尝试所有解码方式：")
        results = decode_all(text)
        for name, decoded in results:
            print(f"\n[{name}]")
            print(f"  {decoded}")
        return

    # 默认：自动检测 + 尝试解码
    text = args[0]
    print(f"输入: {text[:100]}")
    print()

    # 先检测
    detected = detect_encoding(text)
    if detected:
        print("🔍 检测结果：")
        for name, decoded in detected:
            print(f"  → 可能是 [{name}]: {decoded}")
        print()

    # 再尝试所有
    print("🔧 全面解码：")
    results = decode_all(text)
    valid_results = [(name, decoded) for name, decoded in results if decoded.strip()]
    for name, decoded in valid_results:
        print(f"  [{name}] {decoded}")
    
    if use_llm and valid_results:
        print()
        print("🤖 LLM 判断中...")
        # 构造给 LLM 的 prompt
        candidates = []
        for name, decoded in valid_results[:15]:
            candidates.append(f"[{name}] {decoded}")
        
        llm_prompt = (
            "以下是同一段密文经过不同方式解码的结果。请判断哪个结果最可能是正确的明文。如果看起来都不是有意义的文本，请回复: 都不像。\n\n"
            + "原始密文: " + text[:100] + "\n\n"
            + "\n".join(candidates) + "\n\n最可能的正确结果是:"
        )
        
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '-c', f'import sys; sys.stdout.write("需要AstrBot LLM环境")'],
                capture_output=True, text=True, timeout=5
            )
            print(f"  LLM分析建议: {llm_prompt[:200]}...")
            print(f"  (提示: 在AstrBot环境中可用 llm_generate 接口自动判断)")
        except:
            print("  (LLM判断需要在AstrBot环境中运行)")


if __name__ == '__main__':
    main()
