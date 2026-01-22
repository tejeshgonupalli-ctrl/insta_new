# auto_scheduler.py

from instagrapi import Client
from pathlib import Path
from utils.watermark_image import add_watermark_to_image
from utils.watermark_video import add_story_watermark
from utils.watermark_video import add_png_watermark_to_video
from utils.watermark_image import add_png_watermark_to_image


from pathlib import Path


BASE_DIR = Path(__file__).parent
FINAL_POSTS_DIR = BASE_DIR / "final_ready_to_post"

from pathlib import Path

def read_final_caption_from_media(media_path):
    cap = Path(media_path).parent / "final_caption.txt"
    if cap.exists():
        return cap.read_text(encoding="utf8").strip()
    return ""


from instagrapi import Client
import os

from instagrapi import Client

def get_client(session_file):
    cl = Client()
    cl.load_settings(session_file)

    try:
        cl.get_timeline_feed()  # session validity check
    except Exception:
        raise Exception("Session expired. Please login again.")

    return cl



# ---------- IMAGE ----------

def post_image(session_file, image_path, username, watermark_text=None):
    cl = get_client(session_file)
    caption = read_final_caption_from_media(str(image_path))

    if watermark_text:
        wm = add_watermark_to_image(image_path, watermark_text)
    else:
        wm = image_path

    cl.photo_upload(wm, caption)
    
    
def post_reel(session_file, video_path, username, job=None):
    cl = get_client(session_file)
    caption = read_final_caption_from_media(str(video_path))

    wm_video = Path(video_path)

    if job and isinstance(job, dict):

        if job.get("enable_text_wm") and job.get("watermark_text"):
            wm_video = Path(
                add_story_watermark(
                    str(wm_video),
                    job.get("watermark_text")
                )
            )

        if job.get("enable_png_wm") and job.get("watermark_png"):
            wm_video = Path(
                add_png_watermark_to_video(
                    str(wm_video),
                    job.get("watermark_png"),
                    x=job.get("wm_x", 30),
                    y=job.get("wm_y", 30)
                )
            )

    cl.clip_upload(str(wm_video), caption)



# ---------- STORY ----------
def post_story(session_file, path, username, job=None):
    cl = get_client(session_file)

    media_path = Path(path)
    suffix = media_path.suffix.lower()
    wm_media = media_path

    # 🎥 STORY VIDEO
    if suffix == ".mp4":

        if job and job.get("enable_png_wm") and job.get("watermark_png"):
            wm_media = Path(
                add_png_watermark_to_video(
                    str(wm_media),
                    job["watermark_png"],
                    x=job.get("wm_x", 30),
                    y=job.get("wm_y", 30)
                )
            )

        if job and job.get("enable_text_wm") and job.get("watermark_text"):
            wm_media = Path(
                add_story_watermark(
                    str(wm_media),
                    job["watermark_text"]
                )
            )

        cl.video_upload_to_story(str(wm_media))

    # 🖼 STORY IMAGE
    elif suffix in [".jpg", ".jpeg", ".png"]:

        if job and job.get("enable_png_wm") and job.get("watermark_png"):
            wm_media = add_png_watermark_to_image(
                str(wm_media),
                job["watermark_png"],
                x=job.get("wm_x", 30),
                y=job.get("wm_y", 30)
            )

        if job and job.get("enable_text_wm") and job.get("watermark_text"):
            wm_media = add_watermark_to_image(
                str(wm_media),
                job["watermark_text"]
            )

        cl.photo_upload_to_story(str(wm_media))



