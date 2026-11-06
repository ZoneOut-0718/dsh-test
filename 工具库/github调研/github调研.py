#!/usr/bin/env python3
"""github调研.py —— 给定仓库，判断「能不能用、还活着吗」。

输入：owner/repo（如 syrizelink/OpenFic），可选 --pypi 包名
输出：星数 / 许可 / 最近提交 / 发布产物 / 维护状态判定 / PyPI 依赖数量

用法：
    python3 github调研.py syrizelink/OpenFic
    python3 github调研.py syrizelink/OpenFic --pypi openfic
    python3 github调研.py syrizelink/OpenFic --commits 20

只用标准库，无需 token（匿名 60 次/小时）。
"""
import os, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if TOKEN:                      # 有 token 就带上，匿名每小时只有 60 次
    UA["Authorization"] = f"Bearer {TOKEN}"


def get_json(url, timeout=30):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout).read())


def days_since(iso):
    if not iso:
        return None
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - t).days


def verdict(days, stars, archived, has_release_days):
    if archived:
        return "已归档，别碰"
    if days is None:
        return "无提交记录"
    if days <= 30:
        base = "活跃"
    elif days <= 90:
        base = "缓慢（一个月到三个月没动）"
    elif days <= 180:
        base = "半停滞（半年内动过）"
    else:
        base = "停滞（超过半年没动）"
    if stars < 50:
        base += "，小众，出问题只能自己修"
    if has_release_days is not None and has_release_days > 120:
        base += "，发布节奏慢"
    return base


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    repo = args[0]
    pypi = None
    n_commits = 12
    if "--pypi" in args:
        pypi = args[args.index("--pypi") + 1]
    if "--commits" in args:
        n_commits = int(args[args.index("--commits") + 1])

    try:
        d = get_json(f"https://api.github.com/repos/{repo}")
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print("GitHub 限速了（匿名每小时 60 次）。等一小时，或设 GITHUB_TOKEN 环境变量。")
        else:
            print(f"仓库不存在或访问失败：{repo} ({e.code})")
        return 2
    except Exception as e:
        print(f"网络失败：{e}")
        return 2

    days = days_since(d.get("pushed_at"))
    lic = (d.get("license") or {}).get("spdx_id") or "无"
    print(f"== {d['full_name']}  ★{d['stargazers_count']}  fork {d['forks_count']}")
    print(f"   语言 {d.get('language') or '?'} | 许可 {lic} | 体积 {d.get('size', 0)} KB")
    print(f"   建于 {d['created_at'][:10]} | 最后推送 {d['pushed_at'][:10]}（{days} 天前）")
    print(f"   开放 issue {d['open_issues_count']} | 归档 {d.get('archived')}")
    if d.get("homepage"):
        print(f"   主页 {d['homepage']}")
    if d.get("topics"):
        print(f"   标签 {', '.join(d['topics'][:10])}")

    try:
        cs = get_json(f"https://api.github.com/repos/{repo}/commits?per_page={n_commits}")
        print(f"\n-- 最近 {len(cs)} 次提交")
        for c in cs[:n_commits]:
            print("   ", c["commit"]["author"]["date"][:10],
                  c["commit"]["message"].split("\n")[0][:62])
    except Exception as e:
        print(f"\n-- 提交读取失败：{str(e)[:50]}")

    rel_days = None
    try:
        rs = get_json(f"https://api.github.com/repos/{repo}/releases?per_page=3")
        if rs:
            rel_days = days_since(rs[0]["published_at"])
            print(f"\n-- 最新发布 {rs[0]['tag_name']}（{rs[0]['published_at'][:10]}，{rel_days} 天前）"
                  f"，产物 {len(rs[0]['assets'])} 个")
            for a in rs[0]["assets"][:8]:
                print(f"     {a['name'][:52]:54s} {a['size'] // 1048576:4d} MB")
            if len(rs[0]["assets"]) > 8:
                print(f"     …共 {len(rs[0]['assets'])} 个")
        else:
            print("\n-- 无 GitHub Release（只能源码跑）")
    except Exception:
        print("\n-- 发布信息不可用")

    print(f"\n== 维护判定：{verdict(days, d['stargazers_count'], d.get('archived'), rel_days)}")

    if pypi:
        try:
            p = get_json(f"https://pypi.org/pypi/{pypi}/json")
            info = p["info"]
            deps = info.get("requires_dist") or []
            core = [x for x in deps if "extra ==" not in x]
            print(f"\n-- PyPI {pypi} {info['version']} | 要求 Python {info.get('requires_python')}")
            print(f"   依赖 {len(core)} 个（不含 extras）")
            for x in core[:12]:
                print("     ", x.split(";")[0].strip()[:60])
            if len(core) > 12:
                print(f"      …共 {len(core)} 个")
        except Exception as e:
            print(f"\n-- PyPI 查询失败：{str(e)[:50]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
