# dsh-tools

跨工作区通用的 agent 小工具。**索引是 `工具索引.md`，先查再写。**

## 有什么

| 工具 | 用途 |
|---|---|
| `github搜索` | 按关键词找 GitHub 仓库，标出三个月没动的 |
| `github调研` | 单个仓库体检：维护状态、发布产物、依赖规模 |
| `装技能` | 把仓库 / npm 包里的 agent skill 装进指定目录，装完自检 |

全部只用 Python 标准库，不需要装依赖。手机上直接跑：

```bash
python3 工具库/github调研/github调研.py owner/repo
```

GitHub 接口匿名每小时 60 次，不够就设 `GITHUB_TOKEN` 环境变量。

## 规矩

- 一个文件一件事，万能脚本的标签永远写不准。
- 新建工具必须在 `工具索引.md` 加一行：名字、用途、标签、路径、用法、最后使用。
- 90 天没碰的标「废弃」，别删行。

## 备份

```bash
cd /sdcard/Documents/dsh-tools
git add -A && git commit -m "update tools"
```

有远端时 `git push`。换手机前记得先推一次。
