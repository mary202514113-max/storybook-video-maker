#!/usr/bin/env python3
"""
subtitle.py — Whisper 字幕生成模块

使用 OpenAI Whisper（免费）自动识别音频生成字幕
支持英语音频 → 英文字幕 + 中文翻译字幕
"""

import whisper
import subprocess
import srt
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any


class SubtitleGenerator:
    """
    字幕生成器

    使用 Whisper 自动识别音频生成字幕：
    - 英语音频 → 英文字幕（SRT格式）
    - 可扩展：调用翻译API → 中文字幕
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.whisper_cfg = config.get("whisper", {})
        self.model_name = self.whisper_cfg.get("model", "base")
        self.language = self.whisper_cfg.get("language", "en")
        self._model = None

    def _load_model(self):
        """懒加载 Whisper 模型"""
        if self._model is None:
            device = self.whisper_cfg.get("device", "cpu")
            if device == "auto":
                device = "cuda" if whisper.available() else "cpu"
            print(f"      [*] 加载 Whisper {self.model_name} 模型（{device}）...")
            self._model = whisper.load_model(self.model_name, device=device)
        return self._model

    def transcribe_audio(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """
        识别音频生成字幕

        Args:
            audio_path: 音频文件路径
            language: 音频语言（默认 en）

        Returns:
            Whisper 识别结果
        """
        model = self._load_model()
        print(f"      [*] 正在识别音频（Whisper {self.model_name}）...")

        result = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=False,
            initial_prompt=None
        )

        return result

    def result_to_srt(self, result: Dict, output_path: str) -> str:
        """将 Whisper 结果转为 SRT 字幕文件"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        subtitles = []
        for i, segment in enumerate(result["segments"], start=1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            start_td = timedelta(seconds=start)
            end_td = timedelta(seconds=end)

            subtitle = srt.Subtitle(
                index=i,
                start=start_td,
                end=end_td,
                content=text
            )
            subtitles.append(subtitle)

        srt_content = srt.compose(subtitles)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return output_path

    def generate_from_audio(
        self,
        audio_path: str,
        output_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        从音频文件直接生成字幕

        Args:
            audio_path: 音频文件路径
            output_path: 字幕输出路径（.srt）
            language: 音频语言

        Returns:
            包含字幕路径的字典
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        result = self.transcribe_audio(audio_path, language)
        srt_path = self.result_to_srt(result, output_path)

        print(f"      ✅ 生成 {len(result['segments'])} 条字幕")

        return {
            "srt": srt_path,
            "segments": len(result["segments"]),
            "language": result.get("language", language),
            "text": result.get("text", "")
        }

    def generate_bilingual_srt(
        self,
        audio_path: str,
        en_output_path: str,
        zh_output_path: str,
        # 中文翻译暂未实现（需调用翻译API）
        # zh_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成双语字幕（英文 + 中文）

        目前仅支持英文，中文字幕需配合翻译API
        """
        # 英文字幕
        en_result = self.generate_from_audio(audio_path, en_output_path, "en")

        # 中文字幕预留接口（需 Luna 确认翻译方案）
        # TODO: 调用 MiniMax/DeepL 翻译API

        return {
            "en_srt": en_result["srt"],
            "zh_srt": None,  # 待实现
            "segments": en_result["segments"]
        }
