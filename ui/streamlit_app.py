#!/usr/bin/env python3
"""
streamlit_app.py — storybook-video-maker Web 界面

使用方式：
    streamlit run ui/streamlit_app.py

功能：
    - 输入故事文本
    - 一键生成完整绘本视频
    - 预览各阶段输出
    - 参数调整（声线、语速、视频时长）
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 将项目根目录加入 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import StorybookGenerator
from src.audio_gen import AudioGenerator
from src.subtitle import SubtitleGenerator
import yaml

st.set_page_config(
    page_title="storybook-video-maker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== 样式 ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #6B5B95;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ========== 侧边栏配置 ==========
def render_sidebar():
    """渲染侧边栏配置"""
    with st.sidebar:
        st.markdown("## ⚙️ 配置")

        # 加载配置
        config_path = PROJECT_ROOT / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        st.markdown("### 🎙️ 音频设置")

        voice_options = {
            "en-GB-RyanNeural": "🇬🇧 Ryan（英式男声，温暖）",
            "en-GB-SoniaNeural": "🇬🇧 Sonia（英式女声）",
            "en-US-Andrew": "🇺🇸 Andrew（美式男声）",
            "en-US-Aria": "🇺🇸 Aria（美式女声）",
        }

        selected_voice = st.selectbox(
            "声线",
            options=list(voice_options.keys()),
            format_func=lambda x: voice_options[x],
            index=0
        )

        speed = st.slider(
            "语速",
            min_value=0.7,
            max_value=1.3,
            value=0.9,
            step=0.05,
            help="0.9 = 正常速度减慢10%"
        )
        st.caption(f"当前: {speed:.0%} 正常速度（{'减慢' if speed < 1 else '加快'}）")

        pitch = st.slider(
            "音调",
            min_value=-20,
            max_value=20,
            value=-2,
            step=1,
            help="-2Hz = 音调略低，更温暖"
        )
        st.caption(f"当前: {pitch}Hz")

        st.markdown("### 🎬 视频设置")

        duration_per_image = st.slider(
            "每张图时长（秒）",
            min_value=3,
            max_value=10,
            value=5,
            step=1
        )

        zoom_range = st.slider(
            "运镜幅度",
            min_value=0,
            max_value=30,
            value=15,
            step=5,
            help="缩放范围，值越大运镜越明显"
        )
        st.caption(f"当前: 1.0x → 1.{zoom_range//10}{zoom_range%10}x")

        st.markdown("---")
        st.markdown("### 📁 路径")
        st.code(str(PROJECT_ROOT / "outputs"), language=None)

        st.markdown("---")
        st.markdown("**免费工具链**")
        st.markdown("""
        - 🎨 图片: MiniMax App（免费）
        - 🎬 视频: FFmpeg Ken Burns（$0）
        - 🎙️ 音频: edge-tts（$0）
        - 📝 字幕: Whisper（$0）
        - ⚙️ 合并: FFmpeg（$0）
        """)

        return {
            "voice": selected_voice,
            "speed": speed,
            "pitch": pitch,
            "duration_per_image": duration_per_image,
            "zoom_range": zoom_range / 100
        }


# ========== 主界面 ==========
def render_main(settings):
    st.markdown('<p class="main-header">📚 storybook-video-maker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">中英文儿童绘本视频生成工具 · $0成本 · 一键完成</p>',
        unsafe_allow_html=True
    )

    # ========== 故事输入 ==========
    st.markdown("### 📖 输入故事")

    col1, col2 = st.columns([3, 1])

    with col1:
        story = st.text_area(
            "英文故事文本",
            placeholder="A little rabbit hops through the forest, looking for a friend...",
            height=200,
            help="输入英文故事文本，工具会自动生成分段图片、音频、字幕"
        )

    with col2:
        project_name = st.text_input(
            "项目名称",
            value="my_first_story",
            help="用于文件夹命名，只用英文和下划线"
        )

        st.markdown("**快捷模板**")
        if st.button("🐰 小兔子找朋友"):
            st.session_state["story_template"] = """A little rabbit hops through the green forest.
"Where can I find a friend?" she asks.
A kind owl hoots, "What do you like to do?"
"I like to play and share," says the rabbit.
"Then you already have friends!" says the owl.
The rabbit smiles. She was looking for friendship, but it was inside her all along."""

        if "story_template" in st.session_state:
            story = st.session_state["story_template"]

    # ========== 分段预览 ==========
    if story:
        st.markdown("**📋 故事预览**")
        segments = [s.strip() for s in story.split("\n") if s.strip()]
        cols = st.columns(min(3, len(segments)))
        for i, seg in enumerate(segments[:9]):
            with cols[i % 3]:
                st.info(f"**场景{i+1}**\n{seg[:80]}{'...' if len(seg) > 80 else ''}")

    # ========== 生成按钮 ==========
    st.markdown("---")
    col_start, col_reset = st.columns([4, 1])
    with col_start:
        generate = st.button(
            "🚀 开始生成绘本视频",
            type="primary",
            use_container_width=True,
            disabled=not story.strip()
        )
    with col_reset:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ========== 执行流水线 ==========
    if generate and story:
        if not project_name.strip():
            st.error("请输入项目名称")
            return

        with st.status("🎬 绘本视频生成中...", expanded=True) as status:

            # 初始化生成器
            try:
                generator = StorybookGenerator(name=project_name)

                # --- Step 1: 音频 ---
                st.write("**Step 1/5** 🎙️ 生成英式英语音频...")
                audio_result = generator.audio_gen.generate(
                    text=story,
                    output_path=str(generator.audio_dir / f"{project_name}_audio.mp3"),
                    voice=settings["voice"],
                    speed=settings["speed"]
                )
                st.success(f"✅ 音频已生成: {Path(audio_result['audio']).name}")

                # --- Step 2: 字幕 ---
                st.write("**Step 2/5** 📝 识别音频生成字幕...")
                subtitle_result = generator.subtitle_gen.generate_from_audio(
                    audio_path=audio_result["audio"],
                    output_path=str(generator.subtitle_dir / f"{project_name}_subtitle.srt"),
                    language="en"
                )
                st.success(f"✅ 字幕已生成: {subtitle_result['segments']} 条")

                # --- Step 3: 图片 ---
                st.write("**Step 3/5** 🎨 请放入绘本图片...")
                st.info(
                    f"📁 请将图片放入: `{generator.images_dir}`\n"
                    "命名格式: `01.jpg`, `02.jpg`, ... 然后点击下方按钮"
                )

                # --- Step 4 & 5: 视频 + 最终输出 ---
                images = list(generator.images_dir.glob("*.jpg")) + \
                         list(generator.images_dir.glob("*.png"))

                if images:
                    images = sorted(images, key=lambda p: p.name)
                    st.write(f"**Step 4/5** 🎬 生成 Ken Burns 视频（{len(images)} 张图片）...")

                    durations = [settings["duration_per_image"]] * len(images)
                    video_result = generator._generate_video(
                        [str(p) for p in images],
                        force=True
                    )

                    if video_result.get("video"):
                        st.success("✅ 视频已生成")
                        st.write("**Step 5/5** 🎞️ 合并音视频 + 烧录字幕...")

                        try:
                            final = generator._merge_final(
                                video_path=video_result["video"],
                                audio_path=audio_result["audio"],
                                subtitle_path=subtitle_result["srt"]
                            )
                            st.success("✅ 最终视频完成！")

                            # 显示结果
                            st.markdown("---")
                            st.markdown("### 🎉 生成完成")

                            col_vid, col_info = st.columns([2, 1])

                            with col_vid:
                                if Path(final["final_video"]).exists():
                                    st.video(final["final_video"])
                                else:
                                    st.error("视频文件未找到")

                            with col_info:
                                st.markdown("**📋 输出信息**")
                                st.write(f"**视频路径**: `{final['final_video']}`")
                                st.write(f"**时长**: {final['duration']:.1f}秒")
                                st.write(f"**分辨率**: {final['resolution']}")
                                st.write(f"**音频声线**: {settings['voice']}")
                                st.write(f"**语速**: {settings['speed']:.0%}")
                                st.write(f"**图片数量**: {len(images)}张")

                                # 下载链接
                                with open(final["final_video"], "rb") as f:
                                    st.download_button(
                                        "📥 下载最终视频",
                                        f,
                                        file_name=Path(final["final_video"]).name
                                    )
                        except Exception as e:
                            st.error(f"合并失败: {e}")
                            st.info("提示: 字幕烧录可能失败，可尝试生成无字幕版本")
                    else:
                        st.error("❌ 视频生成失败")
                else:
                    st.warning("⚠️ 未找到图片，请先将图片放入指定目录")

                status.update(
                    label="✅ 生成完成！",
                    state="complete",
                    expanded=False
                )

            except Exception as e:
                st.error(f"❌ 生成过程出错: {e}")
                import traceback
                st.code(traceback.format_exc())


# ========== 环境检查页 ==========
def render_check_page():
    st.markdown("### 🔍 环境检查")

    from src.generator import check_environment
    import subprocess
    import sys

    checks = []

    # Python
    checks.append(("Python", f"{sys.version.split()[0]}", True))

    # FFmpeg
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    checks.append(("FFmpeg", result.stderr.decode().split("\n")[0][:50] if result.returncode == 0 else "未安装", result.returncode == 0))

    # edge-tts
    try:
        import edge_tts
        checks.append(("edge-tts", "✅ 已安装", True))
    except ImportError:
        checks.append(("edge-tts", "❌ 未安装 (pip install edge-tts)", False))

    # Whisper
    try:
        import whisper
        checks.append(("Whisper", "✅ 已安装", True))
    except ImportError:
        checks.append(("Whisper", "❌ 未安装 (pip install openai-whisper)", False))

    # Streamlit
    checks.append(("Streamlit", "✅ 当前运行中", True))

    for name, detail, ok in checks:
        if ok:
            st.success(f"✅ **{name}**: {detail}")
        else:
            st.error(f"❌ **{name}**: {detail}")

    st.markdown("---")
    st.markdown("### 📦 安装依赖")
    st.code("pip install edge-tts openai-whisper streamlit ffmpeg-python pyyaml", language="bash")


# ========== 主程序 ==========
def main():
    tab1, tab2 = st.tabs(["📚 生成绘本视频", "🔍 环境检查"])

    with tab1:
        settings = render_sidebar()
        render_main(settings)

    with tab2:
        render_check_page()


if __name__ == "__main__":
    main()
