#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storybook-video-maker Agent 模块
模仿 Claude Code / Cursor 的 Agent Loop 设计
第一性原理：理解意图 → 制定计划 → 执行 → 验证 → 修复
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

# ── 第一性原理：意图理解层 ────────────────────────────────
class IntentUnderstanding:
    """
    模仿 Lovable 的自然语言理解
    将人话描述为结构化执行计划
    """
    def __init__(self, story_text: str):
        self.story_text = story_text
        self.plan = []

    def analyze(self) -> List[Dict]:
        """
        第一性原理拆解：
        1. 故事 → 场景拆分
        2. 场景 → 图片提示词
        3. 图片 → 视频片段
        4. 视频+音频+字幕 → 最终输出
        """
        # 简单按句子拆分场景（可升级为LLM理解）
        sentences = [s.strip() for s in self.story_text.split('.') if s.strip()]

        self.plan = []
        for i, sentence in enumerate(sentences, 1):
            self.plan.append({
                "step": i,
                "type": "scene",
                "text": sentence,
                "image_prompt": self._text_to_image_prompt(sentence),
                "duration": 5,  # 默认5秒/场景
                "status": "pending"
            })

        return self.plan

    def _text_to_image_prompt(self, text: str) -> str:
        """将句子转为 MiniMax 图片生成提示词"""
        # 基础吉卜力风格前缀
        prefix = "Ghibli style anime illustration, Miyazaki anime style, hand-drawn, watercolor, "
        # 简单处理：保留核心名词
        return prefix + text

    def get_summary(self) -> str:
        """返回计划摘要"""
        if not self.plan:
            return "❌ 未分析故事"
        return f"📋 计划：{len(self.plan)} 个场景\n" + "\n".join(
            f"  场景{i['step']}: {i['text'][:30]}..." for i in self.plan
        )


# ── 第一性原理：环境操作层 ────────────────────────────────
class EnvironmentOperation:
    """
    模仿 Claude Code 的直接文件操作能力
    自动执行 FFmpeg / edge-tts 等命令
    """
    def __init__(self, work_dir: Path):
        self.work_dir = Path(work_dir)
        self.images_dir = self.work_dir / "images"
        self.audio_dir = self.work_dir / "audio"
        self.video_dir = self.work_dir / "videos"
        self.output_dir = self.work_dir / "output"

        for d in [self.images_dir, self.audio_dir, self.video_dir, self.output_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def generate_audio(self, text: str, output_path: Path, voice: str = "en-GB-RyanNeural") -> bool:
        """生成音频（edge-tts）"""
        try:
            cmd = [
                "edge-tts",
                "--voice", voice,
                "--rate", "-10%",
                "--text", text,
                "--write-media", str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and output_path.exists():
                print(f"  ✅ 音频生成成功: {output_path.name}")
                return True
            else:
                print(f"  ❌ 音频生成失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ 音频生成异常: {e}")
            return False

    def apply_ken_burns(self, image_path: Path, output_path: Path, duration: int, scene_num: int) -> bool:
        """应用 Ken Burns 效果（FFmpeg 电影感运镜）"""
        try:
            # 奇数场景：Zoom In；偶数场景：Zoom Out
            if scene_num % 2 == 1:
                zoom_filter = "zoompan=z='min(zoom+0.001,1.5)':x='iw/4':y='ih/4':d=1:s=1080x1920:fps=24"
            else:
                zoom_filter = "zoompan=z='max(zoom-0.001,1.0)':x='iw/4':y='ih/4':d=1:s=1080x1920:fps=24"

            cmd = [
                "ffmpeg", "-y",
                "-i", str(image_path),
                "-vf", zoom_filter,
                "-t", str(duration),
                "-s", "1080x1920",
                str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and output_path.exists():
                print(f"  ✅ Ken Burns 效果应用成功: {output_path.name}")
                return True
            else:
                print(f"  ❌ Ken Burns 失败: {result.stderr[-200:]}")
                return False
        except Exception as e:
            print(f"  ❌ Ken Burns 异常: {e}")
            return False

    def merge_audio_video(self, video_path: Path, audio_path: Path, output_path: Path) -> bool:
        """合并音频和视频"""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and output_path.exists():
                print(f"  ✅ 音视频合并成功: {output_path.name}")
                return True
            else:
                print(f"  ❌ 音视频合并失败: {result.stderr[-200:]}")
                return False
        except Exception as e:
            print(f"  ❌ 音视频合并异常: {e}")
            return False


# ── 第一性原理：验证反馈层 ────────────────────────────────
class ValidationFeedback:
    """
    模仿 Lovable 的自动验证能力
    检查输出质量，自动修复常见问题
    """
    @staticmethod
    def validate_file_exists(file_path: Path, description: str) -> bool:
        """验证文件是否存在"""
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"  ✅ {description} 验证通过: {file_path.name}")
            return True
        else:
            print(f"  ❌ {description} 验证失败: 文件不存在或为空")
            return False

    @staticmethod
    def validate_audio_duration(audio_path: Path, expected_duration: int) -> bool:
        """验证音频时长是否匹配"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            if abs(duration - expected_duration) < 2:
                print(f"  ✅ 音频时长验证通过: {duration:.1f}s")
                return True
            else:
                print(f"  ⚠️ 音频时长不匹配: 实际{duration:.1f}s, 预期{expected_duration}s")
                return False
        except Exception as e:
            print(f"  ❌ 音频时长验证异常: {e}")
            return False

    @staticmethod
    def auto_fix_ffmpeg_params(error_msg: str) -> Dict:
        """根据错误信息自动修复 FFmpeg 参数"""
        fixes = {}
        if "Permission denied" in error_msg:
            fixes["suggest"] = "检查文件是否被其他程序占用"
        if "Invalid data found" in error_msg:
            fixes["suggest"] = "输入文件可能损坏，尝试重新生成"
        if "No such file" in error_msg:
            fixes["suggest"] = "输入文件路径错误，检查文件是否存在"
        return fixes


# ── Agent Loop（模仿 Claude Code）────────────────────────────────
class VideoMakerAgent:
    """
    主 Agent：模仿 Claude Code 的 Agent Loop
    理解意图 → 制定计划 → 执行 → 验证 → 修复
    """
    def __init__(self, story_text: str, work_dir: str = "."):
        self.story_text = story_text
        self.work_dir = Path(work_dir)
        self.intent = IntentUnderstanding(story_text)
        self.operator = EnvironmentOperation(work_dir)
        self.validator = ValidationFeedback()
        self.plan = []

    def run(self) -> Path:
        """执行完整 Agent Loop"""
        print("🚀 VideoMakerAgent 启动...")
        print(f"📖 故事: {self.story_text[:50]}...")

        # Step 1: 理解意图，制定计划
        print("\n📋 Step 1: 理解意图，制定计划...")
        self.plan = self.intent.analyze()
        print(self.intent.get_summary())

        # Step 2: 执行计划（循环）
        print("\n🎬 Step 2: 执行计划...")
        completed_scenes = []

        for scene in self.plan:
            print(f"\n  📸 处理场景 {scene['step']}: {scene['text'][:30]}...")

            # 2.1 生成音频
            audio_path = self.operator.audio_dir / f"{scene['step']:02d}.mp3"
            if not self.operator.generate_audio(scene['text'], audio_path):
                print(f"  ⚠️ 场景 {scene['step']} 音频生成失败，跳过")
                continue

            # 2.2 验证音频
            if not self.validator.validate_file_exists(audio_path, "音频文件"):
                continue

            # 2.3 应用 Ken Burns 效果（需要图片，这里用占位符）
            # TODO: 实际使用时需要先用 MiniMax 生成图片
            image_path = self.operator.images_dir / f"{scene['step']:02d}.jpg"
            if not image_path.exists():
                print(f"  ⚠️ 图片不存在: {image_path}，跳过视频生成")
                continue

            video_path = self.operator.video_dir / f"{scene['step']:02d}.mp4"
            if not self.operator.apply_ken_burns(image_path, video_path, scene['duration'], scene['step']):
                continue

            # 2.4 验证视频
            if not self.validator.validate_file_exists(video_path, "视频文件"):
                continue

            # 2.5 合并音视频
            final_clip = self.operator.output_dir / f"{scene['step']:02d}_final.mp4"
            if not self.operator.merge_audio_video(video_path, audio_path, final_clip):
                continue

            # 2.6 最终验证
            if self.validator.validate_file_exists(final_clip, "最终片段"):
                scene['status'] = 'completed'
                completed_scenes.append(final_clip)
                print(f"  ✅ 场景 {scene['step']} 完成！")
            else:
                scene['status'] = 'failed'

        # Step 3: 汇总结果
        print(f"\n📊 执行完成: {len(completed_scenes)}/{len(self.plan)} 个场景成功")
        if completed_scenes:
            print(f"📁 输出目录: {self.operator.output_dir}")
            return self.operator.output_dir
        else:
            print("❌ 没有成功生成的场景")
            return None


# ── CLI 入口 ─────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(description="VideoMakerAgent - AI绘本书视频生成Agent")
    parser.add_argument("--story", type=str, help="故事文本（英文）")
    parser.add_argument("--story-file", type=str, help="故事文本文件")
    parser.add_argument("--work-dir", type=str, default=".", help="工作目录")

    args = parser.parse_args()

    if args.story:
        story_text = args.story
    elif args.story_file:
        with open(args.story_file, 'r', encoding='utf-8') as f:
            story_text = f.read()
    else:
        # 默认示例故事
        story_text = "A little rabbit hops through the garden. She sees a beautiful flower. The sun is warm and bright. She decides to take a nap under the tree."
        print(f"使用默认故事: {story_text[:50]}...")

    agent = VideoMakerAgent(story_text, args.work_dir)
    output_dir = agent.run()

    if output_dir:
        print(f"\n🎉 成功！输出在: {output_dir}")
    else:
        print("\n❌ 执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
