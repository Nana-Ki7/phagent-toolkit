# PH Agent Toolkit

解谜代理工具链，逐步构建中。

## 模块一：解码工具箱 (decoder.py)

支持的编码/密码：
- 古典密码：凯撒（自动破解偏移）、Atbash、ROT13
- 现代编码：Base64/32/16、Hex、二进制、莫尔斯电码、培根密码
- 字符操作：A1Z26 数字转字母
- 辅助功能：自动检测编码类型、全面解码尝试

## 模块二：提取辅助 (extractor.py)

功能：
- **nutri 暴力组合**：按数字模式提取排列组合
- **词夹字**：多单词交错取字母
- **首尾字母**：取每个单词/行的首字母或尾字母
- **索引提取**：按索引序列取字符或单词
- **对角线提取**：从矩阵中取对角线
- **交叉比对**：多组结果的交集分析

## 模块三：搜索与知识库 (searcher.py)

功能：
- **本地知识库**：SQLite 存储的 PH 规则/套路笔记（21条预设条目）
- **Web 搜索建议**：生成搜索关键词
- **Blog/Memos 检索**：搜索已索引内容

## 模块四：纸笔求解器 (solver.py)

功能：
- 支持 21 种常见纸笔谜题类型（Slitherlink、数桥、数独、Akari 等）
- 生成 puzz.link / pzv.jp / cspuz-solver2 URL
- 提供示例盘面

### 用法

```bash
# 解码
python3 decoder.py "密文"

# 提取
python3 extractor.py first "word1 word2 word3"

# 搜索知识库
python3 searcher.py kb "caesar"

# 纸笔求解 URL 生成
python3 solver.py url slitherlink 5 5 "3a3a2a2a3a3a"
python3 solver.py example slitherlink
python3 solver.py list
```
