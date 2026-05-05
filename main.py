#!/usr/bin/env python3
"""
storybook-video-maker
中英文儿童绘本视频生成工具 v1.0

Usage:
    python main.py --story "A little rabbit wants to make friends" --name "little_rabbit"
    streamlit run ui/streamlit_app.py
"""

import argparse
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generator import StorybookGenerator


def main():
    parser = argparse.ArgumentParser(
        description="storybook-video-maker: 中英文儿童绘本视频生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 用故事文本生成完整绘本视频
  python main.py --story "A little rabbit wants to make friends" --name "little_rabbit"

  # 只生成音频
  python main.py --name "little_rabbit" --audio-only

  # 只生成视频（需要已有图片）
  python main.py --name "little_rabbit" --video-only

  # 查看配置状态
  python main.py --check

  # 启动 Web 界面
  streamlit run ui/streamlit_app.py
        """
    )
    parser.add_argument("--story", type=str, help="英文故事文本")
    parser.add_argument("--name", type=str, required=True, help="项目名称（用于文件夹命名）")
    parser.add_argument("--audio-only", action="store_true", help="仅生成音频")
    parser.add_argument("--video-only", action="store_true", help="仅生成视频")
    parser.add_argument("--check", action="store_true", help="检查环境配置")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有文件")
    parser.add_argument("--lang", type=str, default="en-GB", help="音频语言，默认英式英语 en-GB")
    parser.add_argument("--speed", type=float, default=0.9, help="语速倍率，默认0.9（-10%）")

    args = parser.parse_args()

    # 检查模式
    if args.check:
        from src import check_environment
        check_environment()
        return

    if not args.story and not args.audio_only and not args.video_only:
        parser.print_help()
        print("\n[提示] 运行 'streamlit run ui/streamlit_app.py' 打开图形界面")
        return

    # 初始化生成器
    generator = StorybookGenerator(name=args.name)

    if args.audio_only:
        print(f"[*] 仅生成音频模式...")
        result = generator.generate_audio(story=args.story or "", speed=args.speed, voice=args.lang)
        print(f"[✓] 音频已生成: {result['audio']}")

    elif args.video_only:
        print(f"[*] 仅生成视频模式...")
        result = generator.generate_video(force=args.force)
        print(f"[✓] 视频已生成: {result['video']}")

    else:
        print(f"[*] 全流程生成模式...")
        print(f"[*] 故事: {args.story}")
        print(f"[*] 项目: {args.name}")
        print()
        result = generator.run_full_pipeline(
            story=args.story,
            speed=args.speed,
            voice=args.lang,
            force=args.force
        )
        print()
        print("=" * 50)
        print("✅ 绘本视频生成完成！")
        print(f"📁 输出目录: {result['output_dir']}")
        print(f"🎬 最终视频: {result['final_video']}")
        print("=" * 50)


if __name__ == "__main__":
    main()
