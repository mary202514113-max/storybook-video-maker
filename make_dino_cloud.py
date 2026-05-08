# -*- coding: utf-8 -*-
"""
《小恐龙找云朵朋友》视频生成脚本
A Little Dinosaur Finds Cloud Friends

基于 FFmpeg Ken Burns 运镜 + 双字幕烧录
$0 成本，精品绘本标准

用法：python make_dino_cloud.py
"""

import os
import shutil
import subprocess
import sys

# ====== 配置 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = "E:/WorkBuddy/brown-bear-images/xiaokonglong"
AUDIO_DIR = "E:/WorkBuddy/storybook/ryan_audio/dino-cloud"
OUTPUT = os.path.join(BASE_DIR, "outputs", "dino-cloud-final.mp4")
TEMP_DIR = os.path.join(BASE_DIR, "temp_dino")

FPS = 24  # 帧率
CRF = 18  # 质量（越小越清晰，18=视觉无损）

# 9个场景：每段音频5秒
# 图片编号01-09一一对应（10_flying.png留作封面图）
SCENES = [
    {"img": "01_lonely_meadow.png",  "audio": "p01_trim.mp3", "dur": 5.0},
    {"img": "02_start_journey.png", "audio": "p02_trim.mp3", "dur": 5.0},
    {"img": "03_meet_rabbit.png",    "audio": "p03_trim.mp3", "dur": 5.0},
    {"img": "04_help_rabbit.png",    "audio": "p04_trim.mp3", "dur": 5.0},
    {"img": "05_climbing.png",       "audio": "p05_trim.mp3", "dur": 5.0},
    {"img": "06_meet_butterfly.png", "audio": "p06_trim.mp3", "dur": 5.0},
    {"img": "07_sunset.png",         "audio": "p07_trim.mp3", "dur": 5.0},
    {"img": "08_cloud_sea.png",      "audio": "p08_trim.mp3", "dur": 5.0},
    # 第9段：飞向星空（使用09_cloud_friend图），音频末句"never feel lonely again"
    {"img": "09_cloud_friend.png",   "audio": "p09_trim.mp3", "dur": 5.0},
]

# 双语字幕内容（ASS格式中 \N 表示硬换行）
SCENES_CONTENT = [
    {"en": "Deep in the lush green meadow,\\NA little dinosaur looked up\\nat the clouds drifting by.\\n'I wish I could have a cloud friend\\nto play with,' he sighed softly.",
     "zh": "在翠绿的草地上，\\N一只小恐龙抬头望着\\N飘过的白云。\\n'我好想有个云朵朋友\\N一起玩呀。'他轻轻叹了口气。"},
    {"en": "With a small backpack,\\nthe brave little dinosaur\\nset off on a journey.\\nDown the winding path he went,\\nhis heart full of hope.",
     "zh": "背着小小的背包，\\N勇敢的小恐龙\\N踏上了旅程。\\N沿着蜿蜒的小路走去，\\N心中满是期待。"},
    {"en": "On his way, he met\\na little rabbit who was lost and crying.\\n'Don't worry, little one.\\nLet me help you find your home.'",
     "zh": "在路上，他遇到了\\N一只迷路的小兔子，正伤心地哭着。\\n'别怕，小家伙。\\N我来帮你找到家。'"},
    {"en": "Together, they walked\\nthrough the flower fields\\nuntil the rabbit was safe.\\nThe dinosaur waved goodbye\\nand continued up the mountain.",
     "zh": "他们一起穿过花田，\\N直到小兔子平安回到了家。\\N小恐龙挥挥手告别，\\N继续攀登那座高高的山。"},
    {"en": "Higher and higher he climbed,\\nover rocks and through the wind.\\nAt last, he reached\\nthe beautiful mountaintop\\nwhere clouds floated all around.",
     "zh": "他越爬越高，\\N穿过岩石，迎着风。\\N终于，他登上了\\N美丽的山顶，\\N蓬松的白云就在身边轻轻飘浮。"},
    {"en": "A delicate butterfly danced\\nalongside him, its wings\\nshimmering in the golden light.\\nTogether they admired\\nthe breathtaking sunset.",
     "zh": "一只轻盈的蝴蝶\\N在他身边翩翩起舞，\\N翅膀在金色的光芒中闪闪发亮。\\N他们一起欣赏着\\N绚烂的日落。"},
    {"en": "As the first stars appeared,\\nthe little dinosaur stood amidst\\na magnificent sea of clouds.\\nEverything was silver and dreamy,\\nshimmering like a beautiful dream.",
     "zh": "第一颗星星出现的时候，\\N小恐龙站在\\N壮丽的云海之中。\\N一切都镀上了银色，\\N如梦似幻，像一场美丽的梦。"},
    {"en": "Then, out of the mist,\\na gentle cloud fairy appeared.\\nHer laughter like soft bells.\\n'You found me,' she said warmly.\\n'I've been waiting just for you.'",
     "zh": "忽然，云雾之中，\\N一位温柔的云朵仙子出现了。\\N她的笑声如风铃般轻柔。\\n'你找到我了。'她温暖地说。\\n'我一直在等你呢。'"},
    {"en": "Hand in wing, they soared\\ninto the starry sky together.\\nThe little dinosaur smiled.\\nHe had found his cloud friend,\\nand would never feel lonely again.",
     "zh": "手牵着手，翅膀迎着风，\\N他们一起飞向\\N满天星斗的夜空。\\N小恐龙微笑着。\\N从此，再也不会孤单了。"},
]


# ====== 辅助函数 ======

def fmt_time(s):
    """秒数转 ASS 时间格式 H:MM:SS.CC"""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s - int(s)) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


def build_ken_burns_filter(img_idx, dur):
    """
    构建 Ken Burns 效果滤镜

    FFmpeg zoompan 语法：
    - zoom 起始值 = 1.0，z='zoom+N' 每帧递增
    - z=1.0  → 显示裁剪后的中心区域（放大效果）
    - z=1.1  → 显示完整放大图（缩小效果）
    - 所以 'zoom+0.0008' 产生的是"放大/Zoom In"效果

    偶数图（0,2,4...）：Zoom In（放大，深入画面中心）
    奇数图（1,3,5...）：固定缩放（电影感静帧）
    """
    n_frames = int(dur * FPS)

    # 偶数：Zoom In（递增zoom）
    if img_idx % 2 == 0:
        # zoom 从 1.0 递增到约 1.1（5秒24fps × 0.0008 = 0.096）
        vf = (
            f"scale=1080*1.1:1920*1.1:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0008,1.1)':x=iw/2-(iw*zoom/2):y=ih/2-(ih*zoom/2):"
            f"s=1080x1920:d={n_frames}:fps={FPS}"
        )
    else:
        # 奇数：静态镜头（固定中心裁剪，Ken Burns 经典手法）
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920"
        )

    return vf



def create_segment(scene, seg_idx):
    """生成单个Ken Burns视频片段（含音频）"""
    img_path = os.path.join(IMG_DIR, scene["img"])
    audio_path = os.path.join(AUDIO_DIR, scene["audio"])
    dur = scene["dur"]
    out_seg = os.path.join(TEMP_DIR, f"seg_{seg_idx:02d}.mp4")

    vf = build_ken_burns_filter(seg_idx, dur)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", img_path,
        "-i", audio_path,
        "-vf", vf,
        "-map", "0:v", "-map", "1:a",
        "-t", str(dur),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(CRF),
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(FPS),
        "-shortest",
        out_seg
    ]

    print(f"  [{seg_idx+1}/9] {scene['img']} ({dur}s)...", end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"\n  [!] 失败: {result.stderr[-300:]}")
        return None
    print("✅")
    return out_seg


def make_ass(content, seg_idx):
    """生成单场景ASS字幕文件"""
    start = seg_idx * 5.0
    end = start + 4.8

    ass = f"""[Script Info]
Title: Dino Cloud Subtitle
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: English,Georgia,48,&H00FFFFFF,65535,&H001A1A1A,65535,0,0,0,0,100,100,0,0,1,2,1,2,20,20,60,1
Style: Chinese,Microsoft YaHei,42,&H00F5C518,65535,&H001A1A1A,65535,0,0,0,0,100,100,0,0,1,2,1,2,20,20,130,1

[Events]
Format: Layer, Start, End, Style, Text
Dialogue: 0,{fmt_time(start)},{fmt_time(end)},English,,0,0,0,,{content['en']}
Dialogue: 0,{fmt_time(start)},{fmt_time(end)},Chinese,,0,0,0,,{content['zh']}
"""
    ass_path = os.path.join(TEMP_DIR, f"sub_{seg_idx:02d}.ass")
    with open(ass_path, "w", encoding="utf-8-sig") as f:
        f.write(ass)
    return ass_path


def burn_subtitle(seg_path, content, seg_idx):
    """烧录单段字幕到视频"""
    ass_path = make_ass(content, seg_idx)

    # 复制ASS到BASE_DIR，用纯文件名引用（规避Windows路径冒号bug）
    temp_ass = os.path.join(BASE_DIR, f"burn_{seg_idx:02d}.ass")
    shutil.copy(ass_path, temp_ass)

    out_seg = os.path.join(TEMP_DIR, f"sub_{seg_idx:02d}.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", seg_path,
        "-vf", f"subtitles={os.path.basename(temp_ass)}",
        "-c:a", "copy",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(CRF),
        out_seg
    ]

    print(f"  字幕 {seg_idx+1}/9...", end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"\n  [!] 字幕烧录失败: {result.stderr[-300:]}")
        return None
    print("✅")
    return out_seg


def concat_final(segments, output):
    """拼接所有片段为最终视频"""
    concat_list = os.path.join(BASE_DIR, "concat_dino.txt")
    with open(concat_list, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c:a", "aac",
        "-b:a", "128k",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(CRF),
        output
    ]

    print("\n🎬 最终拼接中...")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"[!] 拼接失败: {result.stderr[-300:]}")
        return False
    return True


def cleanup():
    """清理临时文件"""
    print("\n🧹 清理临时文件...")
    for i in range(9):
        for fname in [f"seg_{i:02d}.mp4", f"sub_{i:02d}.mp4", f"sub_{i:02d}.ass"]:
            p = os.path.join(TEMP_DIR, fname)
            if os.path.exists(p): os.remove(p)
        burn = os.path.join(BASE_DIR, f"burn_{i:02d}.ass")
        if os.path.exists(burn): os.remove(burn)
    concat = os.path.join(BASE_DIR, "concat_dino.txt")
    if os.path.exists(concat): os.remove(concat)
    try:
        os.rmdir(TEMP_DIR)
    except OSError:
        pass

def main():
    print("=" * 55)
    print("  🦕 《小恐龙找云朵朋友》Ken Burns 视频生成")
    print("  9场景 × 5秒 = 45秒  |  1080×1920 竖版  |  双字幕")
    print("=" * 55)

    # 检查文件
    print("\n📁 检查文件...")
    for scene in SCENES:
        img = os.path.join(IMG_DIR, scene["img"])
        aud = os.path.join(AUDIO_DIR, scene["audio"])
        if not os.path.exists(img):
            print(f"  [!] 图片缺失: {scene['img']}")
            sys.exit(1)
        if not os.path.exists(aud):
            print(f"  [!] 音频缺失: {scene['audio']}")
            sys.exit(1)
    print("  ✅ 所有文件就绪 (9张图 + 9段音)")

    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    # Step 1: Ken Burns 运镜
    print("\n🎥 Step 1: Ken Burns 运镜生成...")
    segments_raw = []
    for i, scene in enumerate(SCENES):
        seg = create_segment(scene, i)
        if seg:
            segments_raw.append(seg)
        else:
            print(f"  [!] 片段{i+1}失败，退出")
            sys.exit(1)

    # Step 2: 双字幕烧录
    print("\n💬 Step 2: 双字幕烧录...")
    segments_final = []
    for i, (seg, content) in enumerate(zip(segments_raw, SCENES_CONTENT)):
        sub_seg = burn_subtitle(seg, content, i)
        if sub_seg:
            segments_final.append(sub_seg)
        else:
            print(f"  [!] 字幕{i+1}失败，退出")
            sys.exit(1)

    # Step 3: 拼接
    print("\n✂️  Step 3: 视频拼接...")
    if concat_final(segments_final, OUTPUT):
        print(f"  ✅ 最终视频: {OUTPUT}")

    # Step 4: 清理
    cleanup()

    # 视频信息
    print("\n📊 视频信息:")
    cmd_info = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", OUTPUT
    ]
    try:
        import json
        result = subprocess.run(cmd_info, capture_output=True, text=True)
        info = json.loads(result.stdout)
        fmt = info.get("format", {})
        duration = float(fmt.get("duration", 0))
        size_mb = int(fmt.get("size", 0)) // 1024 // 1024
        bitrate = int(fmt.get("bit_rate", 0)) // 1000
        print(f"  时长: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
        print(f"  大小: {size_mb} MB")
        print(f"  码率: {bitrate} kbps")
    except Exception:
        pass

    print(f"\n🎉 完成！输出: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    main()
