# dsh-tools

跨工作区通用的 agent 小工具。**索引是 `工具索引.md`，先查再写。**

## 有什么

| 工具 | 用途 |
|---|---|
| `github搜索` | 按关键词找 GitHub 仓库，标出三个月没动的 |
| `github调研` | 单个仓库体检：维护状态、发布产物、依赖规模 |
| `装技能` | 把仓库 / npm 包里的 agent skill 装进指定目录，装完自检 |

全部只用 Python 标准库，不需要装依赖。

**已建全局命令，任意目录直接敲：**

```bash
gh-search 网文 skill --top 10          # 找工作区
gh-inspect owner/repo                  # 单仓库体检
gh-inspect owner/repo --pypi 包名       # 顺便数依赖
skill-install list gh owner/repo       # 看仓库里有哪些 skill
```

命令是 `/usr/local/bin/` 下的 wrapper，因为 `sdcard` 分区**禁止直接执行**脚本（noexec），
所以用 `python3` 转一手。重装 App 或清了 `/usr/local/bin` 之后，跑一次恢复：

```bash
python3 工具库/重建命令.py
```

GitHub 接口匿名每小时 60 次，不够就设 `GITHUB_TOKEN` 环境变量。

## 规矩

- 一个文件一件事，万能脚本的标签永远写不准。
- 新建工具必须在 `工具索引.md` 加一行：名字、用途、标签、路径、用法、最后使用。
- 90 天没碰的标「废弃」，别删行。

## 仓库

`git@github.com:ZoneOut-0718/dsh-tools-.git`（GitHub 上显示为 dsh-tools-）

## 备份

```bash
cd /sdcard/Documents/dsh-tools
git add -A && git commit -m "update tools"
```

有远端时 `git push`。换手机前记得先推一次。
