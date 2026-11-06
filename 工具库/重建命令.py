#!/usr/bin/env python3
"""重建全局命令 wrapper。重装 App 或清 /usr/local/bin 后跑一次。"""
import os, stat

BASE = "/sdcard/Documents/dsh-tools/工具库"
CMDS = {
    "gh-search":     f"{BASE}/github搜索/github搜索.py",
    "gh-inspect":    f"{BASE}/github调研/github调研.py",
    "skill-install": f"{BASE}/装技能/装技能.py",
}

for name, target in CMDS.items():
    path = f"/usr/local/bin/{name}"
    with open(path, "w") as f:
        f.write(f'#!/bin/sh\nexec python3 "{target}" "$@"\n')
    os.chmod(path, 0o755)
    print("✓", name, "->", target)
