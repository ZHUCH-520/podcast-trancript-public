# podcast-trancript-public

把播客音频、视频、单集链接或粗转录，整理成可以阅读和校对的全文。

[英文说明](./README.md) · [中文介绍页](./docs/zh.html) · [English introduction](./docs/index.html)

## 示例文稿

下面这段是**文档示例**。它不是真实节目，也不是模型输出。

```markdown
# 周末实验室 · 第 12 期

## 摘要

主播林夏和嘉宾周衡讨论中英混说播客。产品名保留英文，中文论述保持完整。

## 全文

**林夏**: 欢迎来到周末实验室。今天我们聊 Whisper 在中英混说里怎么加标点。

**周衡**: faster-whisper 会把 GPU 留成英文，但同一句不该在下一分钟再印一遍。
```

命令行写出的 `transcript.md` 是分段原文的可读副本。上面的结构是 skill 校对后的目标。

## 快速开始

```bash
pipx install "git+https://github.com/ZHUCH-520/podcast-trancript-public.git"
podcast-transcript run episode.mp3 --output-dir ./episode --accept-download --language zh-en
```

`pipx install` 本身不下载模型。第一次运行会先打印安装计划，只有带上 `--accept-download` 才会下载。

| 语言参数 | 行为 |
|---|---|
| 省略或 `auto` | 由模型判断语言 |
| `zh` | 中文，并使用简短的中文标点提示 |
| `en` | 英文 |
| `zh-en` | 按中文识别，提示里保留英文专名和中文标点 |

专名写在 UTF-8 文本里，一行一个，然后：

```bash
podcast-transcript run episode.m4a --output-dir ./episode --language zh-en --glossary names.txt --accept-download
```

空行和以 `#` 开头的行会被忽略。faster-whisper 把这些词当作 hotwords。Apple Silicon 上的 MLX Whisper 没有 hotwords 参数，这些词会附加到提示里。

长音频会做语音活动检测，并在语音边缘留出空白，避免把轻声切掉。每一段不把上一段文字当作条件，避免长节目里同一句被反复印出来。时间重叠且文字相同的片段会合并成一次。上一句已经结束后又出现的重复，会保留。

## 单集链接

可以代替本地文件的地址：

- 直接的音频或视频 URL
- 小宇宙单集页：`https://www.xiaoyuzhoufm.com/episode/<id>`
- Apple Podcasts 单集链接：地址里要有 `i=<单集 id>`
- RSS 或 Atom 订阅。使用第一条条目的音频地址，并在下载前打印节目标题

下载音频之前，命令会打印解析出的音频主机名。节目主页、登录页、带账号密码的 URL 会被拒绝。付费墙、DRM 和需要登录的媒体不会被绕过。模型下载仍然要单独同意。

```bash
podcast-transcript run "https://www.xiaoyuzhoufm.com/episode/示例id" --output-dir ./episode --accept-download
```

只查看单集页对应的音频地址、不下载文件：

```bash
python podcast-trancript-public/scripts/resolve_media.py "https://www.xiaoyuzhoufm.com/episode/示例id"
```

## 模型

| 模型 | 适合 | 代价 |
|---|---|---|
| `small` | 先试一集，或机器比较小 | 更快，人名和噪音可能要多改 |
| `turbo` | 较新的 Apple Silicon，或有合适 GPU 的 Windows / Linux | 速度和准确度比较均衡 |
| `large-v3` | 人名多、口音重、录音不稳 | 下载最大，占用更高 |

Apple Silicon 使用 MLX Whisper。Intel Mac、Windows 和 Linux 使用 faster-whisper。Windows 和 Linux 在检测到 CUDA 时使用 float16，否则使用 CPU 和 int8。`large-v3` 不会被自动选中。已有粗转录时可以跳过模型下载，直接校对文本。

## 安装到中文编程助手

一条命令复制同一份 `SKILL.md` 和 `scripts/`，不改写说明文件：

```bash
podcast-transcript install-skill --list
podcast-transcript install-skill --target qoder
podcast-transcript install-skill --target trae-cn --scope project
```

已核对的目录：

| 目标 | 产品 | 用户级 | 项目级 |
|---|---|---|---|
| `qoder` | Qoder。没有叫 qcoder 的独立产品 | `~/.qoder/skills/` | `.qoder/skills/` |
| `qoder-cn` | Qoder CN CLI，仅项目级 | 当前技能页没有列出用户级目录 | `.qoder/skills/` |
| `lingma` | 通义灵码，以及 Qoder CN IDE | `~/.lingma/skills/` | `.lingma/skills/` |
| `codebuddy` | CodeBuddy | `~/.codebuddy/skills/` | `.codebuddy/skills/` |
| `trae` | TRAE 国际版文档 | `~/.trae/skills/` | `.trae/skills/` |
| `trae-cn` | TRAE 中文版 | `~/.trae-cn/skills/` | `.trae/skills/` |
| `qwen` | Qwen Code | `~/.qwen/skills/` | `.qwen/skills/` |
| `kimi` | Kimi Code CLI | `~/.kimi-code/skills/` | `.kimi-code/skills/` |

这次没有自动安装的：

- **CatPaw**：公开文档里没有核对到 `SKILL.md` 目录。旁路资料提到的 `.catpaw/rules` 是规则文件，不是这个 skill 文件夹。
- **WorkBuddy**：官方说明是上传技能包，但没有写出目录名。可以用 `--target workbuddy --dest ./workbuddy-skill` 准备一个文件夹再手动上传。第三方主目录路径不会被使用。

Codex 仍用仓库英文说明里的 `$skill-installer`。Claude Code 和 Cursor 的目录也在 `install-skill --list` 里。

## 它不会做的事

- 绕过付费墙、登录、DRM 或平台限制
- 保证认出每一个说话人
- 自动安装 FFmpeg、CUDA 或修改系统设置
- 自动上传或发布生成的文件
