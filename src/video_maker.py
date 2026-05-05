#!/usr/bin/env python3
"""
video_maker.py — 图生视频核心模块

使用 FFmpeg Ken Burns 效果实现 $0 成本的绘本视频生成。

Ken Burns 效果：让静态图片产生缩放+平移动画，
模拟专业电影摄影机的缓慢运镜效果，
完美适配儿童绘本的温馨治愈风格。

可选增强模式：HuggingFace Stable Video Diffusion API
"""

import subprocess
import os
import json
import time
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any


class VideoMaker:
    """
    绘本视频生成器

    支持两种模式：
    1. FFmpeg Ken Burns（免费，效果稳定）
    2. HuggingFace SVD API（AI增强，有免费额度）
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.video_cfg = config.get("video", {})
        self.kb_cfg = self.video_cfg.get("ken_burns", {})
        self.hf_cfg = config.get("huggingface", {})
        self.portrait_cfg = self.video_cfg.get("portrait", {})
        self.width = self.video_cfg.get("width", 1080)
        self.height = self.video_cfg.get("height", 1920)
        self.fps = self.video_cfg.get("fps", 24)

    def _run_ffmpeg(self, cmd: List[str], desc: str = "FFmpeg") -> bool:
        """运行 FFmpeg 命令"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                print(f"[!] {desc} 失败: {result.stderr[:200]}")
                return False
            return True
        except FileNotFoundError:
            print("[!] 未找到 ffmpeg，请先安装: https://ffmpeg.org/download.html")
            return False

    def _check_ffmpeg(self) -> bool:
        """检查 FFmpeg 是否可用"""
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=False
        )
        return result.returncode == 0

    def _get_image_duration(self, image_path: str) -> float:
        """获取图片对应的音频时长（秒）"""
        # 从文件名解析时长，格式: 01_5s.jpg（图片名_时长s.jpg）
        filename = Path(image_path).stem
        parts = filename.split("_")
        if len(parts) >= 2:
            try:
                return float(parts[-1].replace("s", ""))
            except ValueError:
                pass
        return self.kb_cfg.get("duration_per_image", 5)

    def _build_ken_burns_filter(
        self,
        duration: float,
        img_index: int,
        total_images: int
    ) -> str:
        """
        构建 Ken Burns 效果滤镜

        策略：
        - 奇数张：从小到大（Zoom In）
        - 偶数张：从大到小（Zoom Out）
        - 每次随机微小平移
        """
        zoom_in = (img_index % 2 == 0) if self.kb_cfg.get("zoom_in") is True else (img_index % 2 == 1)
        zoom_start = self.kb_cfg.get("zoom_range", [1.0, 1.15])[0]
        zoom_end = self.kb_cfg.get("zoom_range", [1.0, 1.15])[1]

        if not zoom_in:
            zoom_start, zoom_end = zoom_end, zoom_start

        # 计算缓慢平移偏移（基于图片索引，伪随机但可复现）
        pan_x = (img_index * 37 % 11 - 5) * self.kb_cfg.get("pan_strength", 0.05)
        pan_y = (img_index * 53 % 13 - 6) * self.kb_cfg.get("pan_strength", 0.05)

        zoom_diff = zoom_end - zoom_start

        # 缩放动画表达式
        zoom_expr = f"{zoom_start}+{zoom_diff}*t/{duration}"

        # 平移动画表达式（居中补偿）
        center_x = f"0.5+{pan_x}*t/{duration}"
        center_y = f"0.5+{pan_y}*t/{duration}"

        # Ken Burns 滤镜
        zoom_filter = (
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
            f"crop={self.width}:{self.height},"
            f"zoompan="
            f"z='{zoom_expr}':"
            f"x='iw*{center_x}-(iw*('{zoom_expr}')/2)':"
            f"y='ih*{center_y}-(ih*('{zoom_expr}')/2)':"
            f"s={self.width}x{self.height}:"
            f"d={int(duration * self.fps)}:"
            f"fps={self.fps}"
        )

        return zoom_filter

    def _build_portrait_filter(self, has_video: bool = False) -> str:
        """构建竖版画面滤镜（图片填充）"""
        fill_mode = self.portrait_cfg.get("fill_mode", "blur")

        if fill_mode == "blur":
            # 模糊放大填充竖版（适合绘本风格，有虚化边框效果）
            return (
                f"scale={self.width*2}:{self.height*2}:force_original_aspect_ratio=increase,"
                f"boxblur=50,"
                f"scale={self.width}:{self.height}"
            )
        elif fill_mode == "black":
            return f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:color=black"
        else:
            return f"scale={self.width}:{self.height}:force_original_aspect_ratio=expanda"

    def image_to_video_ffmpeg(
        self,
        image_path: str,
        output_path: str,
        duration: float
    ) -> bool:
        """
        用 FFmpeg Ken Burns 效果将单张图片转为视频片段

        Args:
            image_path: 图片路径
            output_path: 输出视频路径
            duration: 时长（秒）

        Returns:
            True if successful
        """
        if not self._check_ffmpeg():
            print("[!] FFmpeg 未安装")
            return False

        kb_filter = self._build_ken_burns_filter(duration, 0, 1)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-filter_complex", kb_filter,
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.video_cfg.get("crf", 23)),
            output_path
        ]

        return self._run_ffmpeg(cmd, f"Ken Burns 图片 → 视频 ({Path(image_path).name})")

    def images_to_video_slideshow(
        self,
        image_paths: List[str],
        output_path: str,
        durations: Optional[List[float]] = None
    ) -> bool:
        """
        将多张图片合成为幻灯片视频（Ken Burns 效果 + 场景切换）

        Args:
            image_paths: 图片路径列表
            output_path: 输出视频路径
            durations: 每张图的时长列表（秒）

        Returns:
            True if successful
        """
        if not self._check_ffmpeg():
            return False

        if durations is None:
            durations = [self.kb_cfg.get("duration_per_image", 5)] * len(image_paths)

        # Step 1: 为每张图片生成 Ken Burns 视频片段
        temp_clips = []
        for i, (img, dur) in enumerate(zip(image_paths, durations)):
            clip_path = output_path.replace(".mp4", f"_clip_{i:02d}.mp4")
            kb_filter = self._build_ken_burns_filter(dur, i, len(image_paths))

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img,
                "-filter_complex", kb_filter,
                "-t", str(dur),
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", str(self.video_cfg.get("crf", 23)),
                clip_path
            ]

            print(f"  [*] 处理图片 {i+1}/{len(image_paths)}: {Path(img).name}")
            if self._run_ffmpeg(cmd, f"片段 {i+1}"):
                temp_clips.append(clip_path)
            else:
                print(f"[!] 片段 {i+1} 生成失败，跳过")
                temp_clips.append(None)

        # 移除失败的片段
        temp_clips = [c for c in temp_clips if c is not None]
        if len(temp_clips) < 2:
            print("[!] 有效片段不足，无法合并")
            return False

        # Step 2: 合并视频片段（FFmpeg concat + 交叉淡入淡出）
        concat_list = output_path.replace(".mp4", "_concat.txt")
        transition = self.video_cfg.get("transitions", {})
        trans_type = transition.get("type", "crossfade")
        trans_dur = transition.get("duration", 1.0)

        with open(concat_list, "w") as f:
            for clip in temp_clips:
                f.write(f"file '{clip}'\n")

        # 使用 concat demuxer 合并
        cmd_merge = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c:v", "libx264",
            "-crf", str(self.video_cfg.get("crf", 23)),
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        success = self._run_ffmpeg(cmd_merge, "视频片段合并")

        # 清理临时文件
        try:
            for clip in temp_clips:
                Path(clip).unlink(missing_ok=True)
            Path(concat_list).unlink(missing_ok=True)
        except Exception:
            pass

        return success

    def image_to_video_svd(
        self,
        image_path: str,
        output_path: str,
        duration_frames: int = 25
    ) -> bool:
        """
        用 HuggingFace Stable Video Diffusion API 将图片转为视频

        需要在 config.yaml 中配置 huggingface.api_key

        Args:
            image_path: 图片路径
            output_path: 输出视频路径
            duration_frames: 视频帧数（25帧≈1秒，API上限约25-37帧）

        Returns:
            True if successful
        """
        api_key = self.hf_cfg.get("api_key", "").strip()
        if not api_key:
            print("[!] HuggingFace API Key 未配置，跳过 SVD 模式")
            return False

        endpoint = self.hf_cfg.get(
            "endpoint",
            "stabilityai/stable-video-diffusion-img2vid-xt"
        )
        url = f"https://api-inference.huggingface.co/models/{endpoint}"

        print(f"[*] 调用 HuggingFace SVD API（{duration_frames}帧）...")

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"image": image_data},
                data={"num_frames": min(duration_frames, 37)},
                timeout=120
            )

            if response.status_code == 200:
                with open(output_path.replace(".mp4", "_svd_raw.mp4"), "wb") as f:
                    f.write(response.content)
                print(f"[✓] SVD API 返回成功，保存到临时文件")
                return True
            elif response.status_code == 503:
                print(f"[!] SVD 模型正在加载（{response.status_code}），等待后重试...")
                time.sleep(30)
                return self.image_to_video_svd(image_path, output_path, duration_frames)
            else:
                print(f"[!] SVD API 错误 ({response.status_code}): {response.text[:200]}")
                return False

        except Exception as e:
            print(f"[!] SVD 请求失败: {e}")
            return False

    def upscale_to_portrait(
        self,
        input_video: str,
        output_video: str
    ) -> bool:
        """
        将16:9视频转为9:16竖版视频（上下模糊填充）
        """
        blur = self.portrait_cfg.get("blur_strength", 50)

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", (
                f"scale={self.width*2}:{self.height*2}:force_original_aspect_ratio=increase,"
                f"boxblur={blur}:{blur},"
                f"scale={self.width}:{self.height}"
            ),
            "-c:v", "libx264",
            "-crf", str(self.video_cfg.get("crf", 23)),
            "-c:a", "aac",
            output_video
        ]

        return self._run_ffmpeg(cmd, "竖版转换")

    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """获取视频信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception:
            return None
