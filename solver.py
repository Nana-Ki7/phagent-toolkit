#!/usr/bin/env python3
"""
phagent/solver.py — 纸笔谜题求解器

功能：
1. 生成 puzz.link 盘面 URL（支持常见纸笔类型）
2. 盘面数据编码/解码（puzz.link URL 格式）
3. 常用纸笔类型的盘面生成辅助

用法：
    python3 solver.py url <type> <width> <height> <encoded_data>
    python3 solver.py example <type>
    python3 solver.py list
"""

import sys
import urllib.parse
import json

# ============================================================
# 支持的 puzzle 类型（puzz.link 简称）
# ============================================================

PUZZLE_TYPES = {
    "slitherlink": {"name": "スリザーリンク / Slitherlink", "url_key": "slitherlink"},
    "bridges": {"name": "橋をかけろ / Bridges / Hashiwokakuro", "url_key": "bridges"},
    "sudoku": {"name": "数独 / Sudoku", "url_key": "sudoku"},
    "akari": {"name": "美術館 / Akari", "url_key": "akari"},
    "fillomino": {"name": "フィルオミノ / Fillomino", "url_key": "fillomino"},
    "shikaku": {"name": "四角に切れ / Shikaku", "url_key": "shikaku"},
    "nurikabe": {"name": "ぬりかべ / Nurikabe", "url_key": "nurikabe"},
    "numlink": {"name": "ナンバーリンク / Numberlink", "url_key": "numlink"},
    "minesweeper": {"name": "マインスイーパ / Minesweeper", "url_key": "minesweeper"},
    "heyawake": {"name": "へやわけ / Heyawake", "url_key": "heyawake"},
    "hitori": {"name": "ひとりにしてくれ / Hitori", "url_key": "hitori"},
    "mashu": {"name": "ましゅ / Masyu", "url_key": "mashu"},
    "yajilin": {"name": "ヤジリン / Yajilin", "url_key": "yajilin"},
    "tentaisho": {"name": "天体ショー / Tentaisho", "url_key": "tentaisho"},
    "nonogram": {"name": "お絵かきロジック / Nonogram", "url_key": "nonogram"},
    "kakuro": {"name": "カックロ / Kakuro", "url_key": "kakuro"},
    "stostone": {"name": "ストストーン / Sto-Stone", "url_key": "stostone"},
    "norinori": {"name": "のりのり / Nori Nori", "url_key": "norinori"},
    "lits": {"name": "LITS", "url_key": "lits"},
    "satogaeri": {"name": "さとがえり / Satogaeri", "url_key": "satogaeri"},
    "chocobanana": {"name": "チョコバナナ / Choco Banana", "url_key": "chocobanana"},
}

# ============================================================
# URL 生成
# ============================================================

def make_puzzlink_url(puzzle_type, width, height, encoded_data):
    """
    生成 puzz.link 盘面 URL
    
    参数:
        puzzle_type: 谜题类型（小写英文）
        width: 盘面宽度
        height: 盘面高度
        encoded_data: 盘面编码数据
    
    返回:
        puzz.link URL
    """
    info = PUZZLE_TYPES.get(puzzle_type)
    if not info:
        return None
    
    url_key = info["url_key"]
    return f"https://puzz.link/p?{url_key}/{width}/{height}/{encoded_data}"

def make_pzv_url(puzzle_type, width, height, encoded_data):
    """
    生成 pzv.jp 盘面 URL（cspuz-solver2 可能支持的格式）
    """
    info = PUZZLE_TYPES.get(puzzle_type)
    if not info:
        return None
    
    url_key = info["url_key"]
    return f"https://pzv.jp/p.html?{url_key}/{width}/{height}/{encoded_data}"

def make_cspuz_url(puzzle_type, width, height, encoded_data):
    """
    生成 cspuz-solver2 盘面 URL
    """
    puzzlink_url = make_puzzlink_url(puzzle_type, width, height, encoded_data)
    if not puzzlink_url:
        return None
    
    encoded = urllib.parse.quote(puzzlink_url, safe='')
    return f"https://semiexp.net/apps/cspuz-solver2/index.html?url={encoded}"

# ============================================================
# 示例盘面
# ============================================================

EXAMPLES = {
    "slitherlink": {
        "desc": "5x5 Slitherlink 简单示例",
        "width": 5, "height": 5,
        "data": "3a3a2a2a3a3a",
    },
    "bridges": {
        "desc": "5x5 数桥 简单示例",
        "width": 5, "height": 5,
        "data": "2m2d2d2d2m2",
    },
    "sudoku": {
        "desc": "9x9 数独（中等难度）",
        "width": 9, "height": 9,
        "data": "000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    },
    "akari": {
        "desc": "7x7 Akari",
        "width": 7, "height": 7,
        "data": "..............",
    },
}

def show_example(puzzle_type):
    """显示示例盘面"""
    example = EXAMPLES.get(puzzle_type)
    if not example:
        return None
    
    results = {
        "type": puzzle_type,
        "description": example["desc"],
        "puzzlink": make_puzzlink_url(puzzle_type, example["width"], example["height"], example["data"]),
        "pzv": make_pzv_url(puzzle_type, example["width"], example["height"], example["data"]),
    }
    return results

# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法: python3 solver.py <command> [args]")
        print()
        print("命令:")
        print("  list                          — 列出支持的谜题类型")
        print("  url <type> <w> <h> <data>     — 生成 puzz.link URL")
        print("  example <type>                — 显示示例盘面")
        print("  all                           — 显示所有示例盘面")
        print()
        print("支持的谜题类型（共 {} 种）:".format(len(PUZZLE_TYPES)))
        for key, info in sorted(PUZZLE_TYPES.items()):
            print(f"  {key:15s} — {info['name']}")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        print(f"支持的谜题类型（共 {len(PUZZLE_TYPES)} 种）:")
        for key, info in sorted(PUZZLE_TYPES.items()):
            print(f"  {key:15s} — {info['name']}")
        return
    
    if cmd == "url":
        if len(sys.argv) < 6:
            print("用法: solver.py url <type> <width> <height> <encoded_data>")
            sys.exit(1)
        ptype = sys.argv[2]
        w = sys.argv[3]
        h = sys.argv[4]
        data = sys.argv[5]
        
        url = make_puzzlink_url(ptype, w, h, data)
        if url:
            print(f"支持的其他格式:")
            print(f"  Puzz.link: {url}")
            print(f"  PZV:       {make_pzv_url(ptype, w, h, data)}")
        else:
            print(f"未知谜题类型: {ptype}")
            print(f"可用类型: {', '.join(sorted(PUZZLE_TYPES.keys()))}")
        return
    
    if cmd == "example":
        if len(sys.argv) < 3:
            print("用法: solver.py example <type>")
            sys.exit(1)
        ptype = sys.argv[2]
        result = show_example(ptype)
        if result:
            print(f"示例: {result['description']}")
            print(f"  Puzz.link: {result['puzzlink']}")
            print(f"  PZV:       {result['pzv']}")
        else:
            print(f"未知或暂无示例: {ptype}")
        return
    
    if cmd == "all":
        print(f"所有示例盘面:")
        for ptype in sorted(EXAMPLES.keys()):
            result = show_example(ptype)
            if result:
                print(f"\n[{ptype}] {result['description']}")
                print(f"  {result['puzzlink']}")
        return


if __name__ == '__main__':
    main()
