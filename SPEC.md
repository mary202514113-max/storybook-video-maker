# storybook-video-maker

> 中英文儿童绘本视频生成工具 — 专为0-6岁英语启蒙设计

## 定位

自己造的工具链，完美贴合我们的绘本风格，GitHub 开源自己用。

## 核心功能

### v1.0 功能清单

| 功能 | 实现方式 | 状态 |
|------|---------|------|
| 图片生成 | MiniMax API / 本地 SD | 🔧 开发中 |
| **图生视频（自研）** | FFmpeg 电影感运镜 + HuggingFace SVD | 🔧 开发中 |
| 英式音频生成 | edge-tts（Ryan声线，-10%语速） | ✅ 已完成 |
| 视频合并 | FFmpeg concat | ✅ 已完成 |
| 字幕生成 | Whisper 自动识别 | ✅ 已完成 |
| 字幕烧录 | FFmpeg burn-in | ✅ 已完成 |
| Web 界面 | Streamlit（一键操作） | 🔧 开发中 |
| 全自动流水线 | Python CLI / 单按钮 | 🔧 开发中 |

## 技术方案

### 图生视频：两条腿走路

**免费腿（FFmpeg电影感运镜）**
- 不用任何AI模型，$0成本
- FFmpeg Ken Burns effect：图片自动缩放+平移
- 叠加光晕、色温微调、柔焦边缘
- 场景切换：淡入淡出 + 交叉溶解
- 适用：每张图5秒，竖版9:16

**增强腿（HuggingFace SVD API）**
- 调用 Stable Video Diffusion 免费额度
- 真实AI动画效果
- 当免费腿不够用时升级使用

### 流水线架构

```
storybook-video-maker
│
├── config.yaml          # API密钥、参数配置
├── src/
│   ├── generator.py     # 主流水线编排
│   ├── image_gen.py    # 图片生成（MiniMax）
│   ├── video_maker.py  # 图生视频（FFmpeg运镜 + SVD）
│   ├── audio_gen.py    # edge-tts 音频
│   ├── subtitle.py     # Whisper 字幕
│   └── merger.py       # FFmpeg 视频合并
├── ui/
│   └── streamlit_app.py # Web界面
├── main.py              # CLI入口
└── requirements.txt
```

## 输出规格（固定标准）

- 格式：MP4，9:16 竖版（1080×1920）
- 帧率：24fps
- 音频：英式英语，Ryan声线，-10%语速
- 字幕：白色英文（主）+ 金色中文（译）
- 时长：30-60秒/本

## GitHub 仓库

- 地址：`github.com/mary202514113-max/storybook-video-maker`
- 许可：MIT（自己用/商用均可）
- README：中文 + 英文双语

## 依赖工具

```txt
streamlit>=1.28
edge-tts>=6.1
openai-whisper
ffmpeg-python
httpx
pyyaml
```

## 状态

- [x] 确认工具定位和架构
- [ ] 开发 generator.py 流水线
- [ ] 开发 video_maker.py（图生视频核心）
- [ ] 开发 streamlit_app.py Web界面
- [ ] 初始化 GitHub 仓库
- [ ] 编写 README
