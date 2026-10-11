#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown -> PDF 构建脚本（无 pandoc 依赖）

链路：Markdown --(python-markdown)--> HTML --(Chrome headless --print-to-pdf)--> PDF

用法：
    python build_pdf.py                # 构建全部文档
    python build_pdf.py 简历           # 只构建指定文档（按名字模糊匹配）

依赖：
    pip install markdown
    Chrome 或 Edge（自动探测常见安装路径）
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "pdf"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# (源文件, 输出文件名, 样式)
DOCUMENTS = [
    ("interview/简历.md", "简历.pdf", "resume"),
    ("interview/自我介绍.md", "自我介绍.pdf", "doc"),
    ("interview/面试速查表.md", "面试速记表.pdf", "card"),
    ("interview/面试题速记卡.md", "面试题速记卡.pdf", "card"),
    ("interview/手撕速记卡.md", "手撕速记卡.pdf", "code"),
]

BASE_CSS = """
@page { size: A4; margin: 14mm 15mm 15mm 15mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "Microsoft YaHei", "Microsoft YaHei UI", "Segoe UI", sans-serif;
  color: #1f2328;
  line-height: 1.55;
  margin: 0;
  word-wrap: break-word;
}
h1, h2, h3, h4 { line-height: 1.3; margin: 0.7em 0 0.35em; break-after: avoid; page-break-after: avoid; }
h1 { font-size: 19pt; margin-top: 0; padding-bottom: 4pt; border-bottom: 2.2pt solid #1f6feb; color: #0b3d91; }
h2 { font-size: 13pt; margin-top: 0.85em; padding: 3pt 0 3pt 7pt; border-left: 4pt solid #1f6feb; background: #f2f6fc; color: #0b3d91; }
h3 { font-size: 11.4pt; color: #14508c; border-bottom: 0.6pt solid #d6dee8; padding-bottom: 2pt; }
h4 { font-size: 10.6pt; color: #14508c; }
p { margin: 0.32em 0; }
ul, ol { margin: 0.3em 0; padding-left: 1.35em; }
li { margin: 0.16em 0; }
li > ul, li > ol { margin: 0.12em 0; }
strong { color: #0b3d91; }
a { color: #1f6feb; text-decoration: none; }
hr { border: none; border-top: 0.7pt solid #d6dee8; margin: 0.7em 0; }
code {
  font-family: Consolas, "Cascadia Mono", "Courier New", monospace;
  font-size: 0.87em; background: #f2f4f7; padding: 0.5pt 2.5pt;
  border-radius: 2pt; color: #a3306b;
}
pre {
  background: #f7f9fb; border: 0.7pt solid #dde3ea; border-left: 3pt solid #1f6feb;
  border-radius: 3pt; padding: 5pt 8pt; margin: 0.45em 0;
  overflow-wrap: break-word; white-space: pre-wrap;
  break-inside: avoid; page-break-inside: avoid;
}
pre code { background: none; padding: 0; color: #1f2328; font-size: 0.84em; line-height: 1.42; }
blockquote {
  margin: 0.45em 0; padding: 4pt 9pt; background: #fff8e6;
  border-left: 3pt solid #e3a008; color: #4a3b12; font-size: 0.95em;
  break-inside: avoid; page-break-inside: avoid;
}
blockquote p { margin: 0.16em 0; }
table {
  border-collapse: collapse; width: 100%; margin: 0.5em 0;
  font-size: 0.88em; break-inside: auto;
}
th, td { border: 0.6pt solid #ccd4de; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eaf1fa; color: #0b3d91; font-weight: 600; }
tr { break-inside: avoid; page-break-inside: avoid; }
"""

STYLE_CSS = {
    # 简历：紧凑排版，目标 2 页
    "resume": """
@page { margin: 11mm 13mm 11mm 13mm; }
body { font-size: 9.7pt; line-height: 1.38; }
h1 { font-size: 15.5pt; margin-bottom: 2pt; }
h2 { font-size: 11.2pt; margin: 0.48em 0 0.2em; padding: 1.6pt 0 1.6pt 5pt; }
h3 { font-size: 10.2pt; margin: 0.4em 0 0.15em; }
p { margin: 0.16em 0; }
ul { margin: 0.16em 0; padding-left: 1.15em; }
li { margin: 0.05em 0; }
pre { font-size: 8.2pt; padding: 2.5pt 5pt; margin: 0.22em 0; }
blockquote { padding: 2.5pt 7pt; margin: 0.22em 0; font-size: 9pt; }
""",
    # 说明类文档：常规
    "doc": """
body { font-size: 10.15pt; line-height: 1.5; }
h1 { font-size: 17pt; }
h2 { font-size: 12.4pt; margin: 0.62em 0 0.24em; }
p { margin: 0.24em 0; }
li { margin: 0.09em 0; }
blockquote { padding: 3pt 8pt; margin: 0.3em 0; }
""",
    # 速查卡：紧凑 + 表格密集
    "card": """
body { font-size: 9.9pt; line-height: 1.45; }
h1 { font-size: 16pt; }
h2 { font-size: 12pt; margin: 0.6em 0 0.26em; }
h3 { font-size: 10.6pt; margin: 0.48em 0 0.2em; }
p { margin: 0.2em 0; }
ul, ol { margin: 0.2em 0; padding-left: 1.22em; }
li { margin: 0.08em 0; }
pre { font-size: 8.4pt; padding: 3pt 6pt; margin: 0.28em 0; break-inside: auto; page-break-inside: auto; }
table { font-size: 0.85em; margin: 0.34em 0; }
th, td { padding: 2.2pt 4pt; }
blockquote { padding: 3pt 8pt; margin: 0.28em 0; font-size: 9.2pt; }
""",
    # 代码卡：以骨架代码为主
    "code": """
body { font-size: 9.5pt; line-height: 1.44; }
h1 { font-size: 16pt; }
h2 { font-size: 11.6pt; margin: 0.55em 0 0.24em; }
h3 { font-size: 10.4pt; margin: 0.45em 0 0.18em; }
h4 { font-size: 10pt; margin: 0.4em 0 0.15em; }
p { margin: 0.18em 0; }
ul, ol { margin: 0.18em 0; padding-left: 1.2em; }
li { margin: 0.07em 0; }
pre { font-size: 7.9pt; line-height: 1.38; padding: 4pt 6pt; margin: 0.26em 0; break-inside: auto; page-break-inside: auto; }
pre code { font-size: 7.9pt; }
table { font-size: 0.84em; }
th, td { padding: 2.2pt 4pt; }
blockquote { padding: 3pt 8pt; margin: 0.26em 0; font-size: 9pt; }
""",
}

TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_chrome() -> str:
    for path in CHROME_CANDIDATES:
        if path and Path(path).exists():
            return path
    raise SystemExit("找不到 Chrome / Edge，请安装其中之一后重试。")


def to_html(md_text: str, title: str, style: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["extra", "tables", "fenced_code", "sane_lists", "attr_list", "toc"],
        output_format="html5",
    )
    return TEMPLATE.format(title=title, css=BASE_CSS + STYLE_CSS.get(style, ""), body=body)


def build(chrome: str, md_path: Path, pdf_path: Path, style: str) -> tuple:
    if not md_path.exists():
        print(f"  [跳过] 源文件不存在: {md_path}")
        return None
    md_text = md_path.read_text(encoding="utf-8")
    # 去掉顶层 HTML 注释（仅供作者阅读的填写说明）
    md_text = re.sub(r"^\s*<!--.*?-->\s*", "", md_text, flags=re.S)

    html_path = pdf_path.with_suffix(".html")
    html_path.write_text(to_html(md_text, md_path.stem, style), encoding="utf-8")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    url = "file:///" + str(html_path).replace("\\", "/")
    subprocess.run(
        [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=8000",
            f"--print-to-pdf={pdf_path}", url,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if not pdf_path.exists():
        print(f"  [失败] PDF 未生成: {pdf_path.name}")
        return None

    pages = None
    try:
        from pypdf import PdfReader
        pages = len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass
    size_kb = round(pdf_path.stat().st_size / 1024, 1)
    print(f"  [完成] {pdf_path.name}  {size_kb} KB" + (f"  共 {pages} 页" if pages else ""))
    return pages


def main() -> int:
    chrome = find_chrome()
    print(f"浏览器: {chrome}")
    keyword = sys.argv[1] if len(sys.argv) > 1 else None
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for rel, out_name, style in DOCUMENTS:
        if keyword and keyword not in rel and keyword not in out_name:
            continue
        print(f"-> {rel}")
        build(chrome, ROOT / rel, OUT_DIR / out_name, style)
    print(f"\n输出目录: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
