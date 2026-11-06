#!/usr/bin/env python3
"""装技能.py —— 把别人仓库 / npm 包里的 agent skill 装进本地技能目录。

两种源：
  gh   直接从 GitHub 仓库的某目录拉（走 jsDelivr CDN，国内可通）
  npm  从 npm 包解压（适合发版比 GitHub 还全的项目）

用法：
    python3 装技能.py gh  owner/repo story-review story-deslop --dest DIR
    python3 装技能.py npm @oh-story/dsh story-review --dest DIR --sub lib/oh-story/skills
    python3 装技能.py list gh owner/repo          # 只列仓库里有哪些 skill，不装

约定：仓库里的 skill 放在 <子路径>/<skill名>/SKILL.md，子路径默认 skills。
装完会自检每个 SKILL.md 引用的 references/ scripts/ 是否存在。
"""
import io, json, os, sys, tarfile, time, urllib.error, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if TOKEN:
    UA["Authorization"] = f"Bearer {TOKEN}"


def fetch(url, timeout=45, tries=3):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last


def jsdelivr_tree(repo):
    d = json.loads(fetch(f"https://data.jsdelivr.com/v1/packages/gh/{repo}@main", 40))
    return d.get("files", [])


def walk_files(nodes, path=""):
    for n in nodes:
        p = path + "/" + n["name"]
        if n["type"] == "directory":
            yield from walk_files(n.get("files", []), p)
        else:
            yield p


def list_gh(repo, sub="skills"):
    files = list(walk_files(jsdelivr_tree(repo)))
    names = sorted({p[len("/" + sub + "/"):].split("/")[0]
                    for p in files if p.startswith("/" + sub + "/")})
    return names, files


def install_gh(repo, names, dest, sub="skills"):
    _, files = list_gh(repo, sub)
    ok = fail = 0
    for name in names:
        want = [p for p in files if p.startswith(f"/{sub}/{name}/")]
        if not want:
            print(f"  ✗ {name}: 仓库里没这个 skill")
            fail += 1
            continue
        for p in want:
            rel = p[len(f"/{sub}/"):]
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            try:
                data = fetch(f"https://cdn.jsdelivr.net/gh/{repo}@main{p}")
                open(out, "wb").write(data)
                ok += 1
            except Exception as e:
                print(f"  ✗ {rel}: {str(e)[:50]}")
                fail += 1
        print(f"  ✓ {name}（{len(want)} 个文件）")
    return ok, fail


def install_npm(pkg, names, dest, sub="lib/oh-story/skills"):
    meta = json.loads(fetch(f"https://registry.npmmirror.com/{pkg}", 40))
    ver = meta["dist-tags"]["latest"]
    url = meta["versions"][ver]["dist"]["tarball"]
    print(f"  包 {pkg}@{ver}")
    raw = fetch(url, 120)
    tf = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    ok = fail = 0
    for name in names:
        prefix = f"package/{sub}/{name}/"
        members = [m for m in tf.getmembers() if m.name.startswith(prefix) and m.isfile()]
        if not members:
            print(f"  ✗ {name}: 包里没这个 skill")
            fail += 1
            continue
        for m in members:
            rel = m.name[len(f"package/{sub}/"):]
            out = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "wb").write(tf.extractfile(m).read())
            ok += 1
        print(f"  ✓ {name}（{len(members)} 个文件）")
    return ok, fail


def verify(dest):
    import re
    bad = 0
    for name in sorted(os.listdir(dest)):
        sk = os.path.join(dest, name, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        txt = open(sk, encoding="utf-8", errors="replace").read()
        refs = set(re.findall(
            r"(?:\./)?(references/[A-Za-z0-9_./-]+\.md|scripts/[A-Za-z0-9_.-]+)", txt))
        miss = [r for r in refs if not os.path.exists(os.path.join(dest, name, r))]
        bad += len(miss)
        print(f"   {'✓' if not miss else '!'} {name:24s} 引用 {len(refs):2d} 个，缺 {len(miss)}")
    return bad


def main():
    argv = sys.argv[1:]
    sub, dest, pos, skip = "skills", ".", [], False
    for i, x in enumerate(argv):
        if skip:
            skip = False
            continue
        if x == "--sub":
            sub, skip = argv[i + 1], True
        elif x == "--dest":
            dest, skip = argv[i + 1], True
        else:
            pos.append(x)
    if len(pos) < 2:
        print(__doc__)
        return 1

    # list 子命令：list gh owner/repo
    if pos[0] == "list":
        mode, src = pos[1], pos[2] if len(pos) > 2 else ""
        if mode != "gh":
            print("list 只支持 gh 源；npm 请先看包内容再装")
            return 1
        found, _ = list_gh(src, sub)
        print(f"{src} 共 {len(found)} 个 skill：")
        for n in found:
            print("   ", n)
        return 0

    mode, src, names = pos[0], pos[1], pos[2:]
    if not names:
        print("至少给一个 skill 名（或先用 list 看看有哪些）")
        return 1
    os.makedirs(dest, exist_ok=True)
    if mode == "gh":
        ok, fail = install_gh(src, names, dest, sub)
    elif mode == "npm":
        ok, fail = install_npm(src, names, dest, sub)
    else:
        print(__doc__)
        return 1

    print(f"\n文件：成功 {ok}，失败 {fail}")
    print("自检：")
    bad = verify(dest)
    if bad:
        print(f"\n结果：有 {bad} 处引用缺失。")
        print("gh 源偶尔有文件拉不到（CDN 缓存未命中），换 npm 源重装通常就齐了：")
        print(f"  python3 装技能.py npm <包名> {' '.join(names)} --dest {dest} --sub <包内路径>")
        return 3
    print("\n结果：干净")
    return 0 if bad == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
