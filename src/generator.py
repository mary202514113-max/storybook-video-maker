#!/usr/bin/env python3
"""
generator.py — 绘本视频主流水线

编排所有模块，完成从故事文本到最终视频的全流程：
  故事文本 → MiniMax生图 → FFmpeg Ken Burns → edge-tts音频
  → Whisper字幕 → FFmpeg合并 → 最终视频
"""

import os
import yaml
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from .video_maker import VideoMaker
from .audio_gen import AudioGenerator
from .subtitle import SubtitleGenerator


class StorybookGenerator:
    """
    绘本视频生成器

    一键完成：图片 → 视频 → 音频 → 字幕 → 最终输出
    """

    def __init__(self, name: str, config_path: str = "config.yaml"):
        self.name = name
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / config_path

        # 加载配置
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            print("[!] config.yaml 未找到，使用默认配置")
            self.config = self._default_config()

        # 设置项目目录
        self.project_dir = self.project_root / "outputs" / self.name
        self.images_dir = self.project_dir / "images"
        self.audio_dir = self.project_dir / "audio"
        self.video_dir = self.project_dir / "video"
        self.subtitle_dir = self.project_dir / "subtitles"
        self.final_dir = self.project_dir / "final"

        # 初始化子模块
        self.video_maker = VideoMaker(self.config)
        self.audio_gen = AudioGenerator(self.config)
        self.subtitle_gen = SubtitleGenerator(self.config)

    def _default_config(self) -> Dict[str, Any]:
        """默认配置（所有免费方案）"""
        return {
            "video": {
                "width": 1080,
                "height": 1920,
                "fps": 24,
                "ken_burns": {"enabled": True, "duration_per_image": 5, "zoom_range": [1.0, 1.15]},
                "portrait": {"fill_mode": "blur", "blur_strength": 50},
                "transitions": {"type": "crossfade", "duration": 1.0}
            },
            "audio": {"voice": "en-GB-RyanNeural", "rate": "-10%", "pitch": "-2Hz"},
            "whisper": {"model": "base", "language": "en"},
            "paths": {"output_dir": "outputs"}
        }

    def _ensure_dirs(self):
        """确保所有目录存在"""
        for d in [self.images_dir, self.audio_dir, self.video_dir,
                  self.subtitle_dir, self.final_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(
        self,
        story: str,
        speed: float = 0.9,
        voice: str = "en-GB-RyanNeural",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        执行完整流水线

        Args:
            story: 英文故事文本
            speed: 语速倍率（0.9 = -10%）
            voice: 语音（默认 en-GB-RyanNeural）
            force: 是否强制重新生成

        Returns:
            包含各阶段输出路径的字典
        """
        self._ensure_dirs()

        print(f"\n{'='*50}")
        print(f"📚 绘本视频生成流水线")
        print(f"   项目: {self.name}")
        print(f"   故事: {story[:60]}{'...' if len(story) > 60 else ''}")
        print(f"{'='*50}\n")

        # ========== Step 1: 生成音频 ==========
        print("[1/5] 🎙️ 生成英式英语音频...")
        audio_result = self.audio_gen.generate(
            text=story,
            output_path=str(self.audio_dir / f"{self.name}_audio.mp3"),
            voice=voice,
            speed=speed
        )
        print(f"      ✅ 音频已生成: {Path(audio_result['audio']).name}")

        # ========== Step 2: 生成字幕 ==========
        print("\n[2/5] 📝 生成字幕...")
        subtitle_result = self.subtitle_gen.generate_from_audio(
            audio_path=audio_result["audio"],
            output_path=str(self.subtitle_dir / f"{self.name}_subtitle.srt"),
            language="en"
        )
        print(f"      ✅ 字幕已生成: {Path(subtitle_result['srt']).name}")

        # ========== Step 3: 生成图片 ==========
        print("\n[3/5] 🎨 生成绘本图片...")
        images_result = self._generate_images(story, force)
        print(f"      ✅ 生成 {len(images_result['images'])} 张图片")

        # ========== Step 4: 生成视频 ==========
        print("\n[4/5] 🎬 生成Ken Burns视频...")
        video_result = self._generate_video(images_result["images"], force)
        print(f"      ✅ 视频已生成: {Path(video_result['video']).name}")

        # ========== Step 5: 合并音视频 + 烧录字幕 ==========
        print("\n[5/5] 🎞️ 合并最终视频...")
        final_result = self._merge_final(
            video_path=video_result["video"],
            audio_path=audio_result["audio"],
            subtitle_path=subtitle_result["srt"]
        )

        print(f"\n{'='*50}")
        print(f"🎉 生成完成！")
        print(f"   最终视频: {final_result['final_video']}")
        print(f"   视频时长: {final_result['duration']:.1f}秒")
        print(f"   分辨率: {final_result['resolution']}")
        print(f"{'='*50}")

        return {
            "name": self.name,
            "story": story,
            "output_dir": str(self.project_dir),
            "images": images_result["images"],
            "audio": audio_result["audio"],
            "subtitle": subtitle_result["srt"],
            "video_raw": video_result["video"],
            "final_video": final_result["final_video"],
            "duration": final_result["duration"],
            "resolution": final_result["resolution"]
        }

    def _generate_images(self, story: str, force: bool = False) -> Dict[str, Any]:
        """生成绘本图片"""
        # 优先使用本地图片目录
        local_images = list(self.images_dir.glob("*.jpg")) or \
                       list(self.images_dir.glob("*.png"))

        if local_images and not force:
            print(f"      [*] 发现本地图片 {len(local_images)} 张，跳过生成")
            return {"images": [str(p) for p in local_images]}

        # 检查 MiniMax API
        minimax_cfg = self.config.get("minimax", {})
        api_key = minimax_cfg.get("api_key", "").strip()

        if api_key:
            return self._generate_images_minimax(story)
        else:
            print(f"      [!] 无 MiniMax API Key，使用本地图片目录: {self.images_dir}")
            print(f"      [*] 请将图片放入: {self.images_dir}")
            return {"images": []}

    def _generate_images_minimax(self, story: str) -> Dict[str, Any]:
        """通过 MiniMax API 生成图片"""
        # MiniMax 图片生成逻辑（可扩展）
        print("      [*] MiniMax API 集成待实现")
        return {"images": []}

    def _generate_video(self, image_paths: List[str], force: bool = False) -> Dict[str, Any]:
        """生成 Ken Burns 视频"""
        if not image_paths:
            print("      [!] 无图片，跳过视频生成")
            return {"video": ""}

        output_path = str(self.video_dir / f"{self.name}_video.mp4")

        if Path(output_path).exists() and not force:
            print(f"      [*] 视频已存在，跳过: {output_path}")
            return {"video": output_path}

        success = self.video_maker.images_to_video_slideshow(
            image_paths=image_paths,
            output_path=output_path
        )

        if success:
            return {"video": output_path}
        else:
            print("      [!] 视频生成失败")
            return {"video": ""}

    def _merge_final(
        self,
        video_path: str,
        audio_path: str,
        subtitle_path: str
    ) -> Dict[str, Any]:
        """合并视频 + 音频 + 字幕，烧录最终成品"""
        if not video_path or not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        final_path = str(self.final_dir / f"{self.name}_final.mp4")

        # 获取视频时长
        info = self.video_maker.get_video_info(video_path)
        duration = 0
        resolution = "unknown"
        if info:
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    duration = float(info.get("format", {}).get("duration", 0))
                    resolution = f"{stream.get('width', 0)}x{stream.get('height', 0)}"

        subtitle_cfg = self.config.get("subtitle", {})

        # 构建字幕滤镜
        font_size = subtitle_cfg.get("fontsize_primary", 48)
        font_color = subtitle_cfg.get("color_primary", "white")
        gold_color = subtitle_cfg.get("color_secondary", "#FFD700")
        margin_bottom = subtitle_cfg.get("margin_bottom", 120)

        subtitle_filter = (
            f"subtitles='{subtitle_path}':"
            f"force_style='FontSize={font_size},"
            f"PrimaryColour=&H00{font_color.replace('#', '')},"
            f"Alignment=2,"
            f"MarginV={margin_bottom}'"
        )

        # 合并视频 + 音频 + 字幕
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-crf", str(self.config.get("video", {}).get("crf", 23)),
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            "-filter_complex", subtitle_filter,
            "-shortest",
            final_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                # 字幕烧录失败，尝试无字幕版本
                print(f"      [!] 字幕烧录失败，生成无字幕版本...")
                cmd_no_sub = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "libx264",
                    "-crf", str(self.config.get("video", {}).get("crf", 23)),
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest",
                    final_path
                ]
                subprocess.run(cmd_no_sub, capture_output=True, check=False)
        except Exception as e:
            print(f"      [!] 合并失败: {e}")

        return {
            "final_video": final_path,
            "duration": duration,
            "resolution": resolution
        }

    def generate_audio(self, story: str, speed: float = 0.9, voice: str = "en-GB-RyanNeural") -> Dict[str, Any]:
        """仅生成音频"""
        self._ensure_dirs()
        return self.audio_gen.generate(
            text=story,
            output_path=str(self.audio_dir / f"{self.name}_audio.mp3"),
            voice=voice,
            speed=speed
        )

    def generate_video(self, force: bool = False) -> Dict[str, Any]:
        """仅生成视频（需先有图片）"""
        self._ensure_dirs()
        local_images = [str(p) for p in self.images_dir.glob("*.jpg")] + \
                       [str(p) for p in self.images_dir.glob("*.png")]
        return self._generate_video(local_images, force)


def check_environment():
    """检查运行环境"""
    print("🔍 检查环境配置...\n")

    # 检查 Python 版本
    import sys
    print(f"  Python: {sys.version.split()[0]} ✅")

    # 检查 FFmpeg
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=False)
    if result.returncode == 0:
        version = result.stdout.decode().split("\n")[0]
        print(f"  FFmpeg: {version.split(' ')[2]} ✅")
    else:
        print(f"  FFmpeg: ❌ 未安装")

    # 检查 edge-tts
    try:
        import edge_tts
        print(f"  edge-tts: ✅ 已安装")
    except ImportError:
        print(f"  edge-tts: ❌ 未安装 (pip install edge-tts)")

    # 检查 Whisper
    try:
        import whisper
        print(f"  Whisper: ✅ 已安装")
    except ImportError:
        print(f"  Whisper: ❌ 未安装 (pip install openai-whisper)")

    # 检查 config.yaml
    cfg = Path("config.yaml")
    if cfg.exists():
        print(f"  config.yaml: ✅ 已配置")
    else:
        print(f"  config.yaml: ⚠️ 未找到（将使用默认配置）")

    print()
