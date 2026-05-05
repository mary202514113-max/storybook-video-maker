#!/usr/bin/env python3
"""
audio_gen.py — edge-tts 音频生成模块

完全免费，使用微软 Azure 语音合成
支持 Ryan 英式英语声线，自动降速+降调适配儿童绘本
"""

import asyncio
import edge_tts
from pathlib import Path
from typing import Dict, Any


class AudioGenerator:
    """
    绘本音频生成器

    使用 edge-tts（免费）生成英式英语音频：
    - 声线：en-GB-RyanNeural（温暖男声，最接近童话感）
    - 语速：-10%（略慢，适合儿童）
    - 音调：-2Hz（降低，显得更成熟温暖）
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audio_cfg = config.get("audio", {})

    async def _generate_async(
        self,
        text: str,
        output_path: str,
        voice: str = "en-GB-RyanNeural",
        rate: str = "-10%",
        volume: str = "+0%",
        pitch: str = "-2Hz"
    ) -> Dict[str, Any]:
        """异步生成音频"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(
            text, voice=voice, rate=rate, volume=volume, pitch=pitch
        )
        await communicate.save(output_path)

        file_size = Path(output_path).stat().st_size
        if file_size == 0:
            raise ValueError(f"音频文件生成失败（0字节）: {output_path}")

        return {
            "audio": output_path,
            "voice": voice,
            "rate": rate,
            "pitch": pitch,
            "file_size": file_size
        }

    def generate(
        self,
        text: str,
        output_path: str,
        voice: str = "en-GB-RyanNeural",
        speed: float = 0.9
    ) -> Dict[str, Any]:
        """
        同步接口：生成音频

        Args:
            text: 故事英文文本
            output_path: 输出路径
            voice: 声线（默认 en-GB-RyanNeural）
            speed: 语速倍率（0.9 = -10%）
        """
        if speed == 1.0:
            rate = "+0%"
        elif speed < 1.0:
            pct = int((speed - 1.0) * 100)
            rate = f"{pct}%"
        else:
            pct = int((speed - 1.0) * 100)
            rate = f"+{pct}%"

        print(f"      voice={voice}, rate={rate}")

        try:
            return asyncio.run(
                self._generate_async(
                    text=text,
                    output_path=output_path,
                    voice=voice,
                    rate=rate,
                    volume=self.audio_cfg.get("volume", "+0%"),
                    pitch=self.audio_cfg.get("pitch", "-2Hz")
                )
            )
        except Exception as e:
            print(f"[!] 音频生成失败: {e}")
            return asyncio.run(
                self._generate_async(
                    text=text,
                    output_path=output_path,
                    voice="en-GB-RyanNeural",
                    rate="-10%",
                    volume="+0%",
                    pitch="-2Hz"
                )
            )
