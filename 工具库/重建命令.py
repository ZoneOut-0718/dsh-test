#!/usr/bin/env python3
"""重建命令 —— App 升级 / 重装后一条命令恢复全部环境。

会做三件事：
  1. 重建 /usr/local/bin 下的全局命令 wrapper（gh-search / gh-inspect / skill-install）
  2. 检查 apt 装的工具（ssh、tesseract），缺了就用 apt 装回来
  3. 报告哪些还需要手动处理

用法：
    python3 重建命令.py            # 缺什么补什么
    python3 重建命令.py --check    # 只检查，不改动
"""
import os, subprocess, sys, shutil

BASE = "/sdcard/Documents/dsh-tools/工具库"
CMD_DIR = "/usr/local/bin"

# 名字 -> 脚本绝对路径
CMDS = {
    "gh-search":     f"{BASE}/github搜索/github搜索.py",
    "gh-inspect":    f"{BASE}/github调研/github调研.py",
    "skill-install": f"{BASE}/装技能/装技能.py",
}

# 命令名 -> apt 包名。App 换 runtime rootfs 时这些会消失。
APT_TOOLS = {
    "ssh":       "openssh-client",
    "tesseract": "tesseract-ocr tesseract-ocr-chi-sim",
}

check_only = "--check" in sys.argv


def rebuild_wrappers():
    print("== 全局命令")
    for name, target in CMDS.items():
        path = os.path.join(CMD_DIR, name)
        if not os.path.exists(target):
            print(f"  ✗ {name}: 目标脚本不存在 {target}")
            continue
        if check_only:
            state = "在" if os.path.exists(path) else "缺失"
            print(f"  {name:14s} {state}")
            continue
        with open(path, "w") as f:
            f.write(f'#!/bin/sh\nexec python3 "{target}" "$@"\n')
        os.chmod(path, 0o755)
        print(f"  ✓ {name}")


def ensure_packages():
    print("\n== apt 工具")
    missing = []
    for cmd, pkg in APT_TOOLS.items():
        if shutil.which(cmd):
            print(f"  ✓ {cmd}")
        else:
            print(f"  ✗ {cmd} 缺失（包 {pkg}）")
            missing.append(pkg)
    if not missing:
        return
    if check_only:
        print("  → 加 --check 不会自动装；去掉参数再跑一次即可恢复")
        return
    print("\n  正在安装：" + " ".join(missing))
    subprocess.run("apt-get update -q", shell=True, check=False)
    r = subprocess.run(f"apt-get install -y -q {' '.join(missing)}",
                       shell=True, check=False)
    for cmd in APT_TOOLS:
        print(f"  {'✓' if shutil.which(cmd) else '✗'} {cmd} 安装后状态")


def report():
    print("\n== 其余需要手动确认的")
    checks = [
        ("项目技能（9 个）", "/sdcard/Download/novel/.dsh/skills"),
        ("工具库仓库", "/sdcard/Documents/dsh-tools/.git"),
        ("全局指令", "/root/.agents/AGENTS.md"),
        ("SSH 密钥", os.path.expanduser("~/.ssh/id_ed25519")),
    ]
    for label, path in checks:
        print(f"  {'✓' if os.path.exists(path) else '✗'} {label}")
    print("\n  提醒：SSH 密钥和 ~/.agents 在 proot 的 /root 下，App 换 runtime 时也可能丢；")
    print("  丢了就重新 ssh-keygen，再把公钥加到 GitHub。")


if __name__ == "__main__":
    rebuild_wrappers()
    ensure_packages()
    report()
    print("\n完成。" + ("（仅检查，未改动）" if check_only else ""))
