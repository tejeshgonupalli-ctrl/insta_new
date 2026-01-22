from pathlib import Path
import shutil

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

# ===============================
# INPUT POSTS (SINGLE / BULK)
# ===============================
if len(sys.argv) > 1:
    # 🔥 Single post mode
    post_dirs = [Path(sys.argv[1])]
else:
    # 🔁 Bulk mode
    post_dirs = list((BASE_DIR / "filtered_downloads_watermarked").iterdir())



OUTPUT_DIR = BASE_DIR / "final_ready_to_post"
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_EXTS = (".mp4", ".mov")
IMAGE_EXTS = (".jpg", ".jpeg", ".png")

def build_ready_posts():
    for post_dir in post_dirs:
        if not post_dir.is_dir():
            continue

        # 1️⃣ Find media (already watermarked)
        media_files = [
            f for f in post_dir.iterdir()
            if f.suffix.lower() in VIDEO_EXTS + IMAGE_EXTS
        ]

        # Caption optional – allow media-only posts
        # 2️⃣ Read caption parts (OPTIONAL)
        parts = []

        hook = post_dir / "hook.txt"
        caption_file = post_dir / "caption.txt"
        cta = post_dir / "cta.txt"
        hashtags_file = post_dir / "hashtags.txt"

        if hook.exists():
            text = hook.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)
                
        if caption_file.exists():
            text = caption_file.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)
 
        if cta.exists():
            text = cta.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)

        # 3️⃣ Build final caption (caption OPTIONAL)
        final_caption = ""

        if parts:
            final_caption = "\n\n".join(parts)

        if hashtags_file.exists():
            hashtags = hashtags_file.read_text(encoding="utf8").strip()
            if hashtags:
                final_caption += "\n\n" + hashtags



        # 2️⃣ Read caption parts
        parts = []

        hook = post_dir / "hook.txt"
        caption_file = post_dir / "caption.txt"
        cta = post_dir / "cta.txt"
        hashtags_file = post_dir / "hashtags.txt"

        if hook.exists():
            text = hook.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)

        if caption_file.exists():
            text = caption_file.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)

        if cta.exists():
            text = cta.read_text(encoding="utf8").strip()
            if text:
                parts.append(text)

        if not parts:
            print(f"No caption content in {post_dir.name}")
            continue

        final_caption = "\n\n".join(parts)

        if hashtags_file.exists():
            hashtags = hashtags_file.read_text(encoding="utf8").strip()
            if hashtags:
                final_caption += "\n\n" + hashtags

        # 3️⃣ Create final post folder
        final_post_dir = OUTPUT_DIR / post_dir.name
        final_post_dir.mkdir(exist_ok=True)

        # 4️⃣ Copy media
        for media in media_files:
            shutil.copy(media, final_post_dir / media.name)

        # 5️⃣ Write final caption
        (final_post_dir / "final_caption.txt").write_text(
            final_caption,
            encoding="utf8"
        )

        print(f"Ready: {post_dir.name}")

if __name__ == "__main__":
    build_ready_posts()
