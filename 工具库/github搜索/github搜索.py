#!/usr/bin/env python3
"""github搜索.py —— 按关键词在 GitHub 找仓库，按星数排序看谁在用。

输入：关键词（可多个词）
输出：仓库名 / 星数 / 语言 / 最后推送（距今天数）/ 描述

用法：
    python3 github搜索.py openfic
    python3 github搜索.py "novel writing agent" --top 20
    python3 github搜索.py 网文 skill --sort updated

只用标准库，无需 token（匿名 60 次/小时）。
"""
import os, sys, json, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if TOKEN:                      # 有 token 就带上，匿名每小时只有 60 次
    UA["Authorization"] = f"Bearer {TOKEN}"


def days(iso):
    if not iso:
        return 999
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - t).days


def main():
    argv = sys.argv[1:]
    top, sort, words, skip = 15, "stars", [], False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == "--top":
            top, skip = int(argv[i + 1]), True
        elif a == "--sort":
            sort, skip = argv[i + 1], True
        else:
            words.append(a)
    if not words:
        print(__doc__)
        return 1
    q = " ".join(words)

    url = ("https://api.github.com/search/repositories?q="
           + urllib.parse.quote(q) + f"&sort={sort}&order=desc&per_page={top}")
    try:
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=30).read())
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print("GitHub 限速了（匿名每小时 60 次）。等一小时，或设 GITHUB_TOKEN 环境变量。")
        else:
            print(f"搜索失败：{e.code} {e.reason}")
        return 2
    except Exception as e:
        print(f"搜索失败：{e}")
        return 2

    print(f"关键词「{q}」共 {d.get('total_count', 0)} 个结果，按 {sort} 排序：\n")
    for it in d.get("items", []):
        dd = days(it["pushed_at"])
        flag = "" if dd <= 90 else ("  ← 三个月没动" if dd <= 180 else "  ← 停滞")
        print(f"★{it['stargazers_count']:5d} {it['full_name']:42s} "
              f"{(it.get('language') or '-'):10s} {dd:4d}天前{flag}")
        desc = (it.get("description") or "").strip()
        if desc:
            print(f"        {desc[:88]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
