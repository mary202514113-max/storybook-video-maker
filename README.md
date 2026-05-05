# 📚 storybook-video-maker

> 中英文儿童绘本视频生成工具 — 专为0-6岁英语启蒙设计

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)

**$0成本 · 一键生成 · 完美适配吉卜力绘本风格**

---

## ✨ 功能特点

- 🎨 **图片生成** — 支持 MiniMax API / 本地图片 / Stable Diffusion
- 🎬 **图生视频** — FFmpeg Ken Burns 电影感运镜（$0）+ HuggingFace SVD API（可选）
- 🎙️ **英式音频** — edge-tts 微软免费语音，Ryan 声线，温暖有童话感
- 📝 **自动字幕** — Whisper AI 免费识别，双语字幕烧录
- ⚙️ **一键流水线** — CLI 或 Web 界面，单命令完成全流程
- 📱 **竖版输出** — 9:16 竖版（1080×1920），完美适配视频号/抖音

---

## 🛠️ 安装

```bash
# 克隆仓库
git clone https://github.com/mary202514113-max/storybook-video-maker.git
cd storybook-video-maker

# 安装依赖
pip install -r requirements.txt

# 安装 FFmpeg（必需）
# Windows: winget install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

---

## 🚀 快速开始

### 方式一：命令行（CLI）

```bash
# 全流程生成
python main.py --story "A little rabbit wants to make friends" --name "little_rabbit"

# 调整语速（0.9 = 减慢10%）
python main.py --story "..." --name "my_book" --speed 0.85

# 仅生成音频
python main.py --name "little_rabbit" --audio-only

# 查看环境配置
python main.py --check
```

### 方式二：Web 界面（推荐）

```bash
streamlit run ui/streamlit_app.py
```

然后在浏览器打开 `http://localhost:8501`

---

## 📖 工作原理

```
故事文本
   │
   ├──🎙️ edge-tts ────────────────────→ 音频文件（Ryan声线，英式英语）
   │
   ├──🔊 Whisper ──────────────────────→ 英文字幕（SRT）
   │
   └──🎨 MiniMax/SD ──────────────────→ 图片序列（01.jpg, 02.jpg, ...）
                                              │
                                              ├──🎬 FFmpeg Ken Burns ──→ 视频片段
                                              │
                                              └──🎞️ FFmpeg concat ──→ 完整视频
                                                           │
                                                           └──🔥 烧录字幕 ──→ 最终视频（MP4）
```

### Ken Burns 效果（$0成本核心）

无需任何AI模型，用 FFmpeg 实现电影感运镜：
- 缓慢缩放（Zoom In/Out）
- 微小平移（Pan）
- 交叉淡入淡出
- 竖版画面填充（模糊边框）

效果示例：静态绘本图片 → 电影感动画视频

---

## 📁 项目结构

```
storybook-video-maker/
├── main.py                    # CLI 入口
├── config.yaml                # 配置文件
├── requirements.txt           # 依赖列表
├── SPEC.md                    # 设计规格
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── generator.py          # 主流水线编排
│   ├── video_maker.py         # 图生视频（Ken Burns + SVD）
│   ├── audio_gen.py           # edge-tts 音频生成
│   └── subtitle.py            # Whisper 字幕识别
│
└── ui/
    └── streamlit_app.py       # Web 界面
```

---

## ⚙️ 配置

复制 `config.example.yaml` 为 `config.yaml`：

```yaml
# 音频配置（完全免费）
audio:
  voice: "en-GB-RyanNeural"    # 英式温暖男声
  speed: 0.9                   # 语速 -10%
  pitch: "-2Hz"                # 音调微降

# 视频配置
video:
  width: 1080
  height: 1920                 # 竖版
  fps: 24

  # Ken Burns 运镜（$0）
  ken_burns:
    enabled: true
    duration_per_image: 5      # 每张图5秒
    zoom_range: [1.0, 1.15]     # 缩放幅度

# 可选：MiniMax API（生成图片）
minimax:
  api_key: "your-api-key"

# 可选：HuggingFace SVD（AI增强视频）
huggingface:
  api_key: "your-hf-token"
```

---

## 🎛️ 输出规格

| 参数 | 值 |
|------|-----|
| 格式 | MP4 |
| 分辨率 | 1080×1920（竖版 9:16） |
| 帧率 | 24fps |
| 音频 | 英式英语，Ryan声线，-10%语速 |
| 字幕 | 白色英文 + 金色中文 |
| 时长 | 30-60秒/本 |

---

## 💰 成本

| 环节 | 工具 | 月成本 |
|------|------|-------|
| 图片 | MiniMax App | **$0**（免费额度） |
| 图生视频 | FFmpeg Ken Burns | **$0** |
| 图生视频（AI增强） | HuggingFace SVD | **$0**（有限免费） |
| 音频 | edge-tts | **$0**（微软免费） |
| 字幕 | Whisper | **$0**（本地运行） |
| **合计** | | **$0/月** |

---

## 🗺️ 路线图

- [x] v1.0 — FFmpeg Ken Burns + edge-tts + Whisper 基础流水线
- [ ] v1.1 — MiniMax API 图片生成集成
- [ ] v1.2 — HuggingFace SVD API 视频增强
- [ ] v1.5 — 自动分段（根据句子自动切分故事为多个场景）
- [ ] v2.0 — 中文翻译字幕集成
- [ ] v2.1 — EbSynth 动画化（免费方案升级）
- [ ] v2.5 — AniSora 本地部署（高配电脑用户）

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License — 可以商用，可以fork，可以自己用
