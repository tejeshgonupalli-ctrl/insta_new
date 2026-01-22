from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
import numpy as np
import os
import random


from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

def add_png_watermark_to_video(video_path, png_path, x=30, y=30):
    clip = VideoFileClip(video_path)

    logo = (
        ImageClip(png_path)
        .set_duration(clip.duration)
        .resize(height=int(clip.h * 0.15))  # 🔥 FINAL FIX
        .set_position((x, y))
        .set_opacity(0.7)
    )

    final = CompositeVideoClip([clip, logo])

    out = video_path.replace(".mp4", "_pngwm.mp4")
    final.write_videofile(out, codec="libx264", audio_codec="aac")

    return out



# ============================
#   AUTO SHRINK FONT
# ============================
def auto_shrink_font(draw, text, max_width, base_font_size):
    font_size = base_font_size
    while font_size > 10:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            return font
        font_size -= 2
    return font


# ============================
#   FINAL WATERMARK FUNCTION
# ============================
def add_story_watermark(video_path, watermark_text="@yourusername"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    # ✅ DEFINE BASE_DIR FIRST
    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # logo_path = os.path.join(BASE_DIR, "..", "assets", "bottom_logo.png")

    # print("LOGO PATH:", logo_path)
    # print("LOGO EXISTS:", os.path.exists(logo_path))

    # if not os.path.exists(logo_path):
    #     raise FileNotFoundError(f"Logo not found: {logo_path}")

    output_path = video_path.replace(".mp4", "_wm.mp4")

    video = VideoFileClip(video_path)
    vw, vh = video.size

    # =====================================================
    # 1️⃣ EXISTING MOVING WATERMARK (UNCHANGED)
    # =====================================================
    W = int(vw * 0.45)
    H = int(vh * 0.12)

    wm_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wm_img)

    base_font_size = int(W * 0.18)
    font = auto_shrink_font(draw, watermark_text, W * 0.95, base_font_size)

    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (W - tw) // 2
    ty = (H - th) // 2

    draw.text((tx, ty), watermark_text, font=font, fill=(255, 255, 255, 140))
    wm_array = np.array(wm_img)

    move_interval = 1.5
    random.seed(42)

    positions = []
    t = 0
    while t < video.duration + move_interval:
        x = random.randint(40, max(40, vw - W - 40))
        y = random.randint(40, max(40, vh - H - 40))
        positions.append((t, (x, y)))
        t += move_interval

    def random_move(t):
        for i in range(len(positions) - 1):
            t1, pos1 = positions[i]
            t2, pos2 = positions[i + 1]
            if t1 <= t <= t2:
                alpha = (t - t1) / (t2 - t1)
                x = int(pos1[0] * (1 - alpha) + pos2[0] * alpha)
                y = int(pos1[1] * (1 - alpha) + pos2[1] * alpha)
                return (x, y)
        return positions[-1][1]

    wm_clip = (
        ImageClip(wm_array)
        .set_duration(video.duration)
        .set_pos(random_move)
    )

    # =====================================================
    # 2️⃣ STATIC TEXT WATERMARK (PIL – lower-left center)
    # =====================================================
    text_layer = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    text_font_size = int(vw * 0.045)
    try:
        text_font = ImageFont.truetype("arial.ttf", text_font_size)
    except:
        text_font = ImageFont.load_default()

    tx2 = int(vw * 0.12)
    ty2 = int(vh * 0.55)

    text_draw.text(
        (tx2, ty2),
        watermark_text,
        font=text_font,
        fill=(255, 255, 255, 90)
    )

    text_clip = ImageClip(np.array(text_layer)).set_duration(video.duration)

    # =====================================================
    # 3️⃣ STATIC LOGO PNG (BOTTOM CENTER)
    # =====================================================
    # logo_clip = ImageClip(logo_path).resize(width=int(vw * 0.45))
    # logo_clip = (
    #     logo_clip
    #     .set_duration(video.duration)
    #     .set_position(("center", vh - int(vh * 0.08)))
    #     .set_opacity(1.0)
    # )

    # =====================================================
    # FINAL COMPOSITION
    # =====================================================
    final = CompositeVideoClip([
        video,
        wm_clip,
        text_clip
    ])

    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None
    )

    return output_path

# ------------------------------------
# from PIL import Image, ImageDraw, ImageFont
# from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
# import numpy as np
# import os
# import random


# # ============================
# #   AUTO SHRINK FONT (SAFE)
# # ============================
# def auto_shrink_font(draw, text, max_width, base_font_size):
#     font_size = base_font_size

#     while font_size > 10:
#         try:
#             font = ImageFont.truetype("arial.ttf", font_size)
#         except:
#             font = ImageFont.load_default()

#         bbox = draw.textbbox((0, 0), text, font=font)
#         text_w = bbox[2] - bbox[0]

#         if text_w <= max_width:
#             return font

#         font_size -= 2

#     return font


# # ============================
# #   MOVING VIDEO WATERMARK
# # ============================
# def add_story_watermark(video_path, watermark_text="@yourusername"):
#     if not os.path.exists(video_path):
#         raise FileNotFoundError(video_path)

#     output_path = video_path.replace(".mp4", "_wm.mp4")

#     video = VideoFileClip(video_path)
#     vw, vh = video.size

#     # Watermark box size (responsive)
#     W = int(vw * 0.45)
#     H = int(vh * 0.12)

#     wm_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
#     draw = ImageDraw.Draw(wm_img)

#     base_font_size = int(W * 0.18)
#     font = auto_shrink_font(draw, watermark_text, W * 0.95, base_font_size)

#     bbox = draw.textbbox((0, 0), watermark_text, font=font)
#     tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

#     tx = (W - tw) // 2
#     ty = (H - th) // 2

#     # 🔹 Light transparent text (not bold)
#     draw.text(
#         (tx, ty),
#         watermark_text,
#         font=font,
#         fill=(255, 255, 255, 140)
#     )

#     wm_array = np.array(wm_img)

#     # ============================
#     # RANDOM SMOOTH MOVEMENT
#     # ============================
#     move_interval = 1.5
#     random.seed(42)

#     positions = []
#     t = 0
#     while t < video.duration + move_interval:
#         x = random.randint(40, max(40, vw - W - 40))
#         y = random.randint(40, max(40, vh - H - 40))
#         positions.append((t, (x, y)))
#         t += move_interval

#     def random_move(t):
#         for i in range(len(positions) - 1):
#             t1, pos1 = positions[i]
#             t2, pos2 = positions[i + 1]

#             if t1 <= t <= t2:
#                 alpha = (t - t1) / (t2 - t1)
#                 x = int(pos1[0] * (1 - alpha) + pos2[0] * alpha)
#                 y = int(pos1[1] * (1 - alpha) + pos2[1] * alpha)
#                 return (x, y)

#         return positions[-1][1]

#     wm_clip = (
#         ImageClip(wm_array)
#         .set_duration(video.duration)
#         .set_pos(random_move)
#     )

#     final = CompositeVideoClip([video, wm_clip])
#     final.write_videofile(
#         output_path,
#         codec="libx264",
#         audio_codec="aac",
#         threads=4,
#         preset="medium",
#         logger=None
#     )

#     return output_path

# --------------------------------------------
# import os
# import subprocess
# import uuid


# def add_story_watermark(video_path, watermark_text="@yourname"):
#     if not os.path.exists(video_path):
#         raise FileNotFoundError(video_path)

#     output_path = video_path.replace(".mp4", "_wm.mp4")
#     ass_path = f"temp_{uuid.uuid4().hex}.ass"

#     ass_content = f"""
# [Script Info]
# ScriptType: v4.00+
# PlayResX: 1080
# PlayResY: 1920

# [V4+ Styles]
# Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV

# ; 🔹 Moving watermark (slow, very subtle)
# Style: MOVE,Arial,56,&H40FFFFFF,&H80000000,&H00000000,0,0,1,2,0,7,20,20,40

# ; 🔹 Static centre watermark (anti-theft)
# Style: CENTER,Arial,72,&H25FFFFFF,&H80000000,&H00000000,0,0,1,1,0,5,20,20,20

# ; 🔹 Static bottom watermark (branding)
# Style: BOTTOM,Arial,42,&H70FFFFFF,&H80000000,&H00000000,0,0,1,1,0,2,20,20,40

# [Events]
# Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

# ; 🔁 Moving watermark – very slow diagonal movement
# Dialogue: 0,0:00:00.00,9:59:59.00,MOVE,,0,0,0,,{{\\pos(200,1600)\\t(0,20000,\\pos(880,200))}}{watermark_text}

# ; 🔒 Static centre watermark – anti-theft
# Dialogue: 1,0:00:00.00,9:59:59.00,CENTER,,0,0,0,,{{\\pos(540,960)}}{watermark_text}

# ; 🏷 Bottom watermark – branding
# Dialogue: 2,0:00:00.00,9:59:59.00,BOTTOM,,0,0,0,,{{\\pos(540,1820)}}{watermark_text}
# """

#     with open(ass_path, "w", encoding="utf-8") as f:
#         f.write(ass_content)

#     cmd = [
#         "ffmpeg",
#         "-y",
#         "-i", video_path,
#         "-vf", f"ass={ass_path}",
#         "-c:v", "libx264",
#         "-preset", "fast",
#         "-pix_fmt", "yuv420p",
#         "-c:a", "aac",
#         "-b:a", "128k",
#         output_path
#     ]

#     subprocess.run(cmd, check=True)
#     os.remove(ass_path)

#     return output_path
