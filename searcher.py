#!/usr/bin/env python3
"""
phagent/searcher.py — PH 搜索与知识库模块

功能：
1. Web 搜索：调用外部搜索引擎查 PH 相关冷知识
2. 博客检索：索引并搜索 MalanC43's blog 的文章
3. Memos 检索：从 memos 中查找相关记录
4. 本地知识库：管理 PH 规则/套路笔记

用法：
    python3 searcher.py web "古希腊数字表示法"
    python3 searcher.py blog "数桥"
    python3 searcher.py memo "纸笔"
    python3 searcher.py kb "caesar cipher" --add "凯撒密码: 偏移N位"
"""

import sys
import json
import re
import sqlite3
import os
from pathlib import Path

# ============================================================
# 配置
# ============================================================

DB_PATH = Path(__file__).parent / "ph_knowledge.db"
BLOG_BASE = "https://www.malanc43.blog"
MEMOS_BASE = "https://memos.malanc43.blog"

# ============================================================
# 本地知识库（SQLite）
# ============================================================

def init_db():
    """初始化 SQLite 知识库"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            keyword TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS blog_index (
            url TEXT PRIMARY KEY,
            title TEXT,
            tags TEXT,
            content_preview TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_keyword ON knowledge(keyword)
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)
    ''')
    conn.commit()
    return conn

def add_knowledge(category, keyword, content, source=""):
    """添加知识条目"""
    conn = init_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO knowledge (category, keyword, content, source) VALUES (?, ?, ?, ?)",
        (category, keyword, content, source)
    )
    conn.commit()
    conn.close()
    return c.lastrowid

def search_knowledge(query, category=None, limit=10):
    """搜索本地知识库"""
    conn = init_db()
    c = conn.cursor()
    
    if category:
        c.execute(
            "SELECT id, category, keyword, content, source FROM knowledge WHERE "
            "(keyword LIKE ? OR content LIKE ?) AND category = ? LIMIT ?",
            (f'%{query}%', f'%{query}%', category, limit)
        )
    else:
        c.execute(
            "SELECT id, category, keyword, content, source FROM knowledge WHERE "
            "keyword LIKE ? OR content LIKE ? LIMIT ?",
            (f'%{query}%', f'%{query}%', limit)
        )
    
    results = c.fetchall()
    conn.close()
    return results

def list_categories():
    """列出所有分类"""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM knowledge ORDER BY category")
    cats = [row[0] for row in c.fetchall()]
    conn.close()
    return cats

# ============================================================
# Web 搜索
# ============================================================

def web_search(query, max_results=5):
    """
    Web 搜索（通过 Tavily）
    返回搜索结果列表
    """
    import urllib.request
    import urllib.parse
    
    # 由于环境限制，这里输出搜索建议，实际搜索由调用方处理
    print(f"[搜索建议] 关键词: {query}")
    print(f"[搜索建议] 建议搜索: PH {query} puzzle")
    print(f"[搜索建议] 建议搜索: {query} 密码 编码")
    print("[搜索建议] 可通过 web_search_tavily tool 执行实际搜索")
    
    return [
        {"query": query},
        {"suggested": f"PH {query} puzzle"},
        {"suggested": f"{query} 密码"},
    ]

# ============================================================
# 博客检索
# ============================================================

def search_blog(query):
    """从本地索引的博客文章中搜索"""
    conn = init_db()
    c = conn.cursor()
    c.execute(
        "SELECT url, title, tags, content_preview FROM blog_index WHERE "
        "title LIKE ? OR tags LIKE ? OR content_preview LIKE ? LIMIT 10",
        (f'%{query}%', f'%{query}%', f'%{query}%')
    )
    results = c.fetchall()
    conn.close()
    
    if results:
        return [{"url": r[0], "title": r[1], "tags": r[2], "preview": r[3][:100]} for r in results]
    else:
        return [{"info": f"未找到匹配的文章，可访问 {BLOG_BASE} 搜索 '{query}'"}]

def index_blog_articles(articles):
    """
    索引博客文章到本地数据库
    articles: [{"url": "...", "title": "...", "tags": "...", "content": "..."}]
    """
    conn = init_db()
    c = conn.cursor()
    count = 0
    for art in articles:
        c.execute(
            "INSERT OR REPLACE INTO blog_index (url, title, tags, content_preview) VALUES (?, ?, ?, ?)",
            (art["url"], art["title"], art.get("tags", ""), art.get("content", "")[:500])
        )
        count += 1
    conn.commit()
    conn.close()
    return count

# ============================================================
# Memos 检索
# ============================================================

def search_memos(query, token=""):
    """从 memos 搜索"""
    import urllib.request
    
    if not token:
        return [{"info": "需要 memos token 才能检索"}]
    
    try:
        url = f"{MEMOS_BASE}/api/v1/memos?pageSize=20"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        memos = data.get("memos", [])
        
        results = []
        for m in memos:
            content = m.get("content", "")
            visibility = m.get("visibility", "")
            if query.lower() in content.lower():
                results.append({
                    "id": m.get("name", ""),
                    "content": content[:200],
                    "visibility": visibility,
                    "time": m.get("displayTime", ""),
                })
        return results if results else [{"info": f"memos 中未找到匹配 '{query}'"}]
    except Exception as e:
        return [{"error": f"检索 memos 失败: {e}"}]

# ============================================================
# 初始化预设知识
# ============================================================

DEFAULT_KNOWLEDGE = [
    ("cipher", "caesar", "凯撒密码：将字母按字母表偏移N位（1-25）。如 shift=3 时 A→D。暴力破解尝试所有25种偏移。"),
    ("cipher", "atbash", "Atbash密码：A↔Z, B↔Y, C↔X…即第N个字母替换为第(27-N)个字母。自逆。"),
    ("cipher", "rot13", "ROT13：凯撒密码偏移13位。自逆。常用于隐藏剧透内容。"),
    ("cipher", "vigenere", "维吉尼亚密码：用关键词确定每个字母的凯撒偏移量。需要知道关键词才能解码。"),
    ("cipher", "base64", "Base64：用64个可打印字符表示二进制数据。特征：大小写字母+数字+/，结尾可能为=或==。"),
    ("cipher", "morse", "莫尔斯电码：用.-表示字母。单词间用/或|分隔。"),
    ("cipher", "bacon", "培根密码：用A/B的5位组合表示字母（24字母版，缺J/U→I/V）。"),
    ("cipher", "a1z26", "A1Z26：数字1-26对应字母A-Z。如 1→A, 26→Z。"),
    ("cipher", "hex", "Hex（十六进制）：每两位十六进制数表示一个字节。特征：只含0-9A-Fa-f。"),
    ("cipher", "binary", "二进制：每8位0/1表示一个字符。特征：只含0和1。"),
    ("cipher", "keyboard_shift", "键盘移位：在QWERTY键盘上向左或向右移一位。如 's' 左移→'a'，右移→'d'。"),
    ("technique", "nutri", "Nutri：暴力组合提取，按数字模式从列表中提取元素组合成新词。如 '3 1 4' 表示取第三、第一、第四项。"),
    ("technique", "interleave", "词夹字：从多个单词中轮流取字母组成新词。如 'abc'+'def'→'adbecf'。"),
    ("technique", "first_letter", "首字母提取：取每个单词或每行的首字母组成消息。"),
    ("technique", "index_extract", "索引提取：从文本中按指定索引位置取字符或单词。支持范围 '1-3,5'。"),
    ("technique", "diagonal", "对角线提取：从矩阵中沿对角线方向取字母。"),
    ("technique", "cross_ref", "交叉比对：多组结果的交集分析，找出共同字符和独有字符。"),
    ("puzzle_type", "bridges", "数桥（Bridges/Hashiwokakuro）：岛屿上的数字表示需要连接出去的桥数。桥必须直连，不能交叉，最多2座桥连接同一对岛屿。所有岛屿最终必须全部连通。"),
    ("puzzle_type", "slitherlink", "数桥（Slitherlink）：画一条闭合回路，每个数字表示其四周属于回路的边的数量。回路不能交叉或分叉。"),
    ("puzzle_type", "sudoku", "数独：在空格中填1-9，使每行、每列、每个宫都恰好包含1-9各一次。"),
    ("puzzle_type", "nonogram", "数织（Nonogram/绘马）：涂黑格子，盘面外的数字表示每行/列中连续涂黑段的长度。"),
]

def init_default_knowledge(force=False):
    """初始化预设知识条目"""
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM knowledge")
    count = c.fetchone()[0]
    
    if count > 0 and not force:
        conn.close()
        return count
    
    if force:
        c.execute("DELETE FROM knowledge")
    
    for cat, kw, content in DEFAULT_KNOWLEDGE:
        c.execute(
            "INSERT INTO knowledge (category, keyword, content, source) VALUES (?, ?, ?, ?)",
            (cat, kw, content, "phagent 预设")
        )
    
    conn.commit()
    conn.close()
    return len(DEFAULT_KNOWLEDGE)

# ============================================================
# CLI
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法: python3 searcher.py <command> <query> [options]")
        print()
        print("命令:")
        print("  web <query>          — Web 搜索建议")
        print("  kb <query>           — 搜索本地知识库")
        print("  kb --list            — 列出所有分类")
        print("  kb --add <keyword> <content> [category] — 添加知识")
        print("  blog <query>         — 搜索已索引的博客文章")
        print("  memo <query> [token] — 搜索 memos")
        print("  init                 — 初始化预设知识库")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        count = init_default_knowledge(force=True)
        print(f"✅ 已初始化 {count} 条预设知识条目")
        return
    
    if cmd == "kb":
        if "--list" in sys.argv:
            cats = list_categories()
            print("知识库分类:")
            for c in cats:
                print(f"  - {c}")
            return
        
        if "--add" in sys.argv:
            idx = sys.argv.index("--add")
            if len(sys.argv) <= idx + 2:
                print("需要 keyword 和 content")
                return
            keyword = sys.argv[idx + 1]
            content = sys.argv[idx + 2]
            category = sys.argv[idx + 3] if len(sys.argv) > idx + 3 else "manual"
            id_ = add_knowledge(category, keyword, content)
            print(f"✅ 已添加 (id={id_}): [{category}] {keyword}")
            return
        
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = search_knowledge(query)
        if results:
            print(f"📚 知识库搜索结果 ({len(results)}条):")
            for r in results:
                print(f"\n  [{r[1]}] {r[2]}")
                print(f"  {r[3][:150]}")
                if r[4]:
                    print(f"  来源: {r[4]}")
        else:
            print(f"未找到匹配 '{query}' 的条目")
            print(f"可用分类: {', '.join(list_categories())}")
        return
    
    if cmd == "web":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = web_search(query)
        for r in results:
            for k, v in r.items():
                print(f"  {k}: {v}")
        return
    
    if cmd == "blog":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = search_blog(query)
        for r in results:
            print(f"  {r.get('title', '?')}")
            print(f"  URL: {r.get('url', '?')}")
            print(f"  标签: {r.get('tags', '?')}")
            print()
        return
    
    if cmd == "memo":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        token = sys.argv[3] if len(sys.argv) > 3 else ""
        results = search_memos(query, token)
        for r in results:
            if "error" in r:
                print(f"❌ {r['error']}")
            elif "info" in r:
                print(f"ℹ️ {r['info']}")
            else:
                print(f"  [{r.get('time','?')}] {r.get('content','')[:150]}")
        return


if __name__ == '__main__':
    main()
