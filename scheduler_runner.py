import time
import json
from datetime import datetime
from pathlib import Path
import shutil

from auto_scheduler import post_image, post_reel, post_story

JOBS_FILE = Path("scheduled_jobs.json")

print("⏰ Scheduler Runner started...")
print("📂 Watching:", JOBS_FILE.resolve())


def get_run_time(job):
    """
    Backward compatible scheduler time reader
    Supports:
    - scheduled_time (new)
    - run_at (old)
    """
    run_at = job.get("scheduled_time") or job.get("run_at")
    if not run_at:
        return None
    return datetime.fromisoformat(run_at)


while True:
    try:
        if not JOBS_FILE.exists():
            time.sleep(5)
            continue

        jobs = json.loads(JOBS_FILE.read_text())
        now = datetime.now()

        for job in jobs:
            # ✅ skip completed or already running jobs
            if job.get("status") in ("done", "running"):
                continue

            run_at = get_run_time(job)
            if run_at is None:
                job["status"] = "failed"
                job["last_error"] = "Missing scheduled_time / run_at"
                JOBS_FILE.write_text(json.dumps(jobs, indent=2))
                continue

            if now < run_at:
                continue

            print(f"🚀 Running job for @{job['username']}")

            # mark job as running BEFORE upload
            job["status"] = "running"
            JOBS_FILE.write_text(json.dumps(jobs, indent=2))

            try:
                # -----------------------------
                # Media handling
                # -----------------------------
                media_path = Path(job["media_path"])

                if not media_path.exists():
                    job["status"] = "failed"
                    job["last_error"] = f"Media file not found: {media_path}"
                    JOBS_FILE.write_text(json.dumps(jobs, indent=2))
                    print(f"❌ Media missing for @{job['username']}: {media_path}")
                    continue


                # 🔁 UNIQUE media per account (CRITICAL)
                unique_media = media_path.with_name(
                    f"{media_path.stem}_{job['username']}{media_path.suffix}"
                )

                if not unique_media.exists():
                    shutil.copy(media_path, unique_media)

                media_path = unique_media
                suffix = media_path.suffix.lower()

                # -----------------------------
                # IMAGE POSTS
                # -----------------------------
                if suffix in [".jpg", ".jpeg", ".png"]:
                    post_image(
                        job["session_file"],
                        str(media_path),
                        job["username"]
                    )

                # -----------------------------
                # VIDEO POSTS
                # -----------------------------
                elif suffix == ".mp4":
                    if job.get("post_type") == "story":
                        post_story(
                            job["session_file"],
                            str(media_path),
                            job["username"],
                            job
                        )
                    else:
                        post_reel(
                            job["session_file"],
                            str(media_path),
                            job["username"],
                            job
                        )
                        # anti-ban delay between reels
                        time.sleep(60)

                else:
                    raise Exception(f"Unsupported media type: {suffix}")

                print(f"✅ Done for @{job['username']}")

                # ✅ mark as completed
                job["status"] = "done"
                JOBS_FILE.write_text(json.dumps(jobs, indent=2))

            except Exception as e:
                job["status"] = "failed"
                job["last_error"] = str(e)
                JOBS_FILE.write_text(json.dumps(jobs, indent=2))
                print(f"❌ Failed for @{job['username']}: {e}")

    except Exception as e:
        print("❌ Scheduler error:", e)

    time.sleep(5)
