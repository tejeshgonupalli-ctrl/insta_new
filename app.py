import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import os
import streamlit as st
import uuid
from utils.reel_downloader import download_media_from_url
import shutil
from utils.watermark_video import add_png_watermark_to_video
from utils.watermark_image import add_png_watermark_to_image
from instagrapi.exceptions import TwoFactorRequired, ChallengeRequired

from instagrapi import Client
from pathlib import Path
import json
import streamlit as st

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

ACCOUNTS_FILE = Path("accounts.json")
if ACCOUNTS_FILE.exists():
    accounts = json.loads(ACCOUNTS_FILE.read_text())
else:
    accounts = []

def save_account(username):
    session_file = f"sessions/session_{username}.json"

    for acc in accounts:
        if acc["username"] == username:
            return  # already exists

    accounts.append({
        "username": username,
        "session_file": session_file
    })

    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2))
    

def get_logged_client(username: str) -> Client:
    session_path = SESSIONS_DIR / f"session_{username}.json"

    if not session_path.exists():
        raise Exception(f"Session not found for @{username}")

    cl = Client()
    cl.load_settings(session_path)

    # ✅ session valid or not check
    cl.get_timeline_feed()

    return cl




from pathlib import Path

def read_final_caption_from_media(media_path):
    cap = Path(media_path).parent / "final_caption.txt"
    if cap.exists():
        return cap.read_text(encoding="utf8").strip()
    return ""



def show_downloaded_posts():
    st.subheader("📥 Downloaded Instagram Posts")

    files = [f for f in os.listdir(".") if f.endswith(".mp4")]

    if not files:
        st.warning("No downloaded posts found")
        return

    for file in sorted(files, reverse=True):
        st.markdown(f"**{file}**")

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.video(file)

        st.divider()


# ==========================
# CONFIG
# ==========================

BASE_DIR = Path(__file__).parent
JOBS_FILE = BASE_DIR / "scheduled_jobs.json"

SCRIPTS = {
    "instaloader": BASE_DIR / "instaloader.py",
    "fetch_medias" : BASE_DIR / "fetch_medias.py",
    "filter": BASE_DIR / "filter.py",
    "watermark": BASE_DIR / "watermark.py",
    "feature_engine": BASE_DIR / "feature4_engine.py",
    "ready_to_post": BASE_DIR / "ready_to_post.py",
    "auto_bulk": BASE_DIR / "auto_bulk_scheduler.py",
}

STATUS_COLORS = {
    "pending": "badge-pending",
    "running": "badge-running",
    "failed": "badge-failed",
    "done": "badge-done",
}

# ==========================
# HELPERS
# ==========================

def run_script(label: str, script_path: Path, args=None):
    """
    Run one of your existing Python scripts (instaloader, filter, watermark, etc.)
    and show stdout/stderr nicely in the UI.
    """
    if args is None:
        args = []
    cmd = [sys.executable, str(script_path)] + list(args)
    st.write(f"🔄 Running: `{' '.join(cmd)}`")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()

        if out:
            st.markdown("**stdout:**")
            st.code(out, language="bash")
        if err:
            st.markdown("**stderr:**")
            st.code(err, language="bash")

        if proc.returncode == 0:
            st.success(f"✅ {label} completed successfully.")
        else:
            st.error(f"❌ {label} failed with code {proc.returncode}.")
    except Exception as e:
        st.error(f"❌ Error running {label}: {e}")


def load_jobs():
    if not JOBS_FILE.exists():
        return []
    try:
        return json.loads(JOBS_FILE.read_text(encoding="utf8"))
    except Exception:
        return []


def save_jobs(jobs):
    JOBS_FILE.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf8")


def status_badge(status: str) -> str:
    css_class = STATUS_COLORS.get(status, "badge-pending")
    label = status.upper()
    return f"<span class='badge {css_class}'>{label}</span>"


def parse_time(j):
    try:
        return datetime.fromisoformat(j["scheduled_time"].replace(" ", "T"))
    except Exception:
        return datetime.max


# ==========================
# PAGE CONFIG & GLOBAL STYLE
# ==========================

st.set_page_config(
    page_title="Insta Automation Control Center",
    page_icon="🚀",
    layout="wide",
)

# Premium CSS
st.markdown(
    """
    <style>
    body {
        background: radial-gradient(circle at top left, #020617, #020617 40%, #020617 100%);
        color: #e5e7eb;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    /* Sidebar glass */
    [data-testid="stSidebar"] > div {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(22px);
        border-right: 1px solid rgba(148, 163, 184, 0.35);
    }

    /* Glass cards */
    .glass-card {
        background: radial-gradient(circle at top left, rgba(30,64,175,0.18), rgba(15,23,42,0.96));
        padding: 18px 20px;
        border-radius: 20px;
        border: 1px solid rgba(148, 163, 184, 0.4);
        box-shadow: 0 18px 45px rgba(15,23,42,0.85);
        backdrop-filter: blur(26px);
        margin-bottom: 14px;
        transition: 0.22s ease;
    }
    .glass-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 26px 60px rgba(15,23,42,0.95);
    }

    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #f9fafb;
        margin-bottom: 4px;
    }
    .section-sub {
        font-size: 12px;
        color: #9ca3af;
    }

    /* KPI cards */
    .metric-box {
        background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(30,64,175,0.35));
        border-radius: 18px;
        border: 1px solid rgba(129, 140, 248, 0.75);
        padding: 16px 18px;
        text-align: left;
        backdrop-filter: blur(18px);
        box-shadow: 0 18px 45px rgba(15,23,42,0.95);
        transition: .22s;
    }
    .metric-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 26px 65px rgba(59,130,246,0.75);
    }
    .metric-label {
        font-size: 11px;
        color: #cbd5f5;
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #e5e7ff;
    }
    .metric-sub {
        font-size: 11px;
        color: #9ca3af;
        margin-top: 3px;
    }

    /* Neon badges */
    .badge {
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: .06em;
        color: #f9fafb;
    }
    .badge-pending {
        background: rgba(250, 204, 21, 0.22);
        box-shadow: 0 0 16px rgba(250, 204, 21, 0.55);
    }
    .badge-running {
        background: rgba(59, 130, 246, 0.32);
        box-shadow: 0 0 16px rgba(59, 130, 246, 0.75);
    }
    .badge-done {
        background: rgba(34, 197, 94, 0.28);
        box-shadow: 0 0 16px rgba(34, 197, 94, 0.75);
    }
    .badge-failed {
        background: rgba(239, 68, 68, 0.3);
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.85);
    }

    /* Jobs cards */
    .job-card {
        padding: 10px 12px;
        border-radius: 16px;
        background: radial-gradient(circle at top left, rgba(15,23,42,0.95), rgba(15,23,42,0.98));
        border: 1px solid rgba(55, 65, 81, 0.85);
        margin-bottom: 8px;
    }
    .job-path {
        color: #e5e7eb;
        font-size: 13px;
        font-weight: 500;
    }
    .job-meta {
        color: #9ca3af;
        font-size: 11px;
        margin-top: 2px;
    }

    /* Top title */
    .top-title {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #e5e7eb;
    }
    .top-sub {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================
# SIDEBAR NAV
# ==========================

st.sidebar.title("🚀 Insta Automation")
st.sidebar.caption("Full pipeline control · Tejesh edition")

page = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "📥 Downloaded Posts",
        "1) Download & Filter",
        "2) Watermark",
        "3) AI Generation",
        "4) Ready-to-Post",
        "5) Bulk Scheduler",
        "6) Jobs Monitor",
        "Settings / Info",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("Pipeline: Download → Filter → Watermark → AI → Ready → Schedule → Post")
# ": Download → Filter → Watermark → AI → Ready → Schedule → Post"

# ==========================
# COMMON DATA
# ==========================

jobs = load_jobs()
total_jobs = len(jobs)
pending_jobs = sum(1 for j in jobs if j.get("status") == "pending")
running_jobs = sum(1 for j in jobs if j.get("status") == "running")
failed_jobs = sum(1 for j in jobs if j.get("status") == "failed")
done_jobs = sum(1 for j in jobs if j.get("status") == "done")


# ==========================
# PAGE: DASHBOARD
# ==========================


# ---------------- CONFIG ----------------
ACCOUNTS_FILE = "accounts.json"
JOBS_FILE = "scheduled_jobs.json"
UPLOAD_DIR = Path("posts/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# st.set_page_config(page_title="Instagram Automation", layout="centered")

# st.title("📸 Instagram Automation Panel")

# ---------------- LOAD ACCOUNTS ----------------
if Path(ACCOUNTS_FILE).exists():
    accounts = json.loads(Path(ACCOUNTS_FILE).read_text())
else:
    accounts = []

# ---------------- ADD ACCOUNT ----------------
st.subheader("🔐 Instagram Login (One Time Only)")

login_username = st.text_input("Instagram Username")
login_password = st.text_input("Instagram Password", type="password")

if st.button("Login & Create Session"):
    cl = Client()
    try:
        cl.login(login_username, login_password)

        session_path = SESSIONS_DIR / f"session_{login_username}.json"
        cl.dump_settings(session_path)

        st.success("✅ Login successful. Session saved.")
        st.info("ℹ️ You can now select this account and post.")

    except TwoFactorRequired:
        st.error("❌ 2FA enabled. Disable 2FA once OR use mobile app login once.")

    except ChallengeRequired:
        st.error("❌ Instagram security challenge. Login once in mobile app.")

    except Exception as e:
        st.error(f"❌ Login failed: {e}")




# ---------------- SELECT ACCOUNT ----------------
st.subheader("👥 Select Accounts")

accounts = [p.stem.replace("session_", "") for p in SESSIONS_DIR.glob("session_*.json")]

selected_accounts = st.multiselect(
    "Choose accounts to post",
    accounts
)

# 반드시 account selection check
if not selected_accounts:
    st.warning("⚠️ Please select at least one account")
    st.stop()

# Use first selected account safely
username = selected_accounts[0]
session_file = (BASE_DIR / "sessions" / f"session_{username}.json").resolve()



# ---------------- CREATE POST ----------------
st.divider()
st.subheader("📝 Create Post")

from pathlib import Path

PIPELINE_BASE = Path("filtered_downloads_watermarked")
PIPELINE_BASE.mkdir(exist_ok=True)

if "post_dir" not in st.session_state:
    existing_posts = sorted(PIPELINE_BASE.glob("post_*"))
    next_index = len(existing_posts) + 1
    st.session_state.post_dir = PIPELINE_BASE / f"post_{next_index:03d}"
    st.session_state.post_dir.mkdir(exist_ok=True)

post_dir = st.session_state.post_dir
st.caption(f"📁 Current Post Folder: {post_dir.name}")


if st.button("➕ New Post"):
    existing_posts = sorted(PIPELINE_BASE.glob("post_*"))
    next_index = len(existing_posts) + 1
    st.session_state.post_dir = PIPELINE_BASE / f"post_{next_index:03d}"
    st.session_state.post_dir.mkdir(exist_ok=True)

    # 🔥 Reset reel download trigger for new post
    st.session_state.pop("last_reel_url", None)
    st.session_state.pop("reel_downloaded", None)

    st.rerun()



# 🔗 Reel URL input (STEP 1 already added)
reel_url = st.text_input(
    "🔗 Paste Instagram Reel URL (optional)",
    placeholder="https://www.instagram.com/reel/xxxxxxxx/"
)



uploaded_file = st.file_uploader(
    "Upload Image / Reel / Story (or use Reel URL above)",
    type=["jpg", "jpeg", "png", "mp4"]
)

# ==============================
# LOCAL FILE UPLOAD (SAME FLOW AS LINK)
# ==============================
if uploaded_file is not None:
    post_dir = st.session_state.post_dir
    post_dir.mkdir(exist_ok=True)

    uploaded_path = post_dir / uploaded_file.name

    with open(uploaded_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # 🔥 Ensure caption.txt exists
    caption_file = post_dir / "caption.txt"
    if not caption_file.exists():
        caption_file.write_text("", encoding="utf8")

    st.success(f"✅ Uploaded file saved to {post_dir.name}")



file_path = None
auto_caption = ""

# 🔐 Session file path (ABSOLUTE STRING)
# 🔐 Session file path (ABSOLUTE STRING)
session_file_path = str(
    (BASE_DIR / "sessions" / f"session_{username}.json").resolve()
)


# ==============================
# INSTAGRAM REEL DOWNLOAD (ONLY ONCE)
# ==============================
if reel_url:
    try:
        st.info("⬇️ Downloading media from Instagram link...")

        media_files, auto_caption, detected_type = download_media_from_url(
            str(reel_url),
            session_file_path
        )

        src_media = Path(media_files[0])
        
        # ✅ Always use session-based post folder
        post_dir = st.session_state.post_dir


        dst_media = post_dir / src_media.name
        shutil.copy(src_media, dst_media)

        (post_dir / "caption.txt").write_text(
            auto_caption or "",
            encoding="utf8"
        )

        file_path = dst_media

        st.session_state["reel_downloaded"] = True
        st.success("✅ Reel downloaded successfully")
        st.session_state["reel_downloaded"] = True
        st.session_state["last_reel_url"] = reel_url


    except Exception as e:
        st.error(f"❌ Failed to download Instagram link: {e}")
        
# --------watermark ---------
        
st.subheader("💧 Watermark Settings")

enable_text_wm = st.checkbox("Enable Text Watermark", value=True)
enable_png_wm  = st.checkbox("Enable PNG Watermark", value=False)

watermark_text = None
watermark_png_path = None
wm_x, wm_y = 30, 30

# 🔹 TEXT WATERMARK
if enable_text_wm:
    watermark_text = st.selectbox(
        "Select watermark text",
        [
            "@brand_main",
            "@brand_backup",
            "@tej123",
            "@company_official",
            "@The Get Now"
        ]
    )


# 🔹 PNG WATERMARK
if enable_png_wm:
    uploaded_png = st.file_uploader(
        "Upload PNG watermark",
        type=["png"]
    )

    col1, col2 = st.columns(2)
    with col1:
        wm_x = st.number_input("PNG X position", min_value=0, value=30)
    with col2:
        wm_y = st.number_input("PNG Y position", min_value=0, value=30)

    if uploaded_png:
        watermark_dir = Path("watermarks")
        watermark_dir.mkdir(exist_ok=True)

        watermark_png_path = watermark_dir / uploaded_png.name
        watermark_png_path.write_bytes(uploaded_png.getbuffer())

        st.image(uploaded_png, caption="Selected PNG Watermark", width=120)

# ---------------- CAPTION ------------

st.subheader("⚙️ Auto Prepare Posts")

if st.button("🚀 Prepare Posts (Filter → Watermark → Rewrite → Ready)"):
    # 1️⃣ Run AI generation ONLY for current post
    run_script(
        "AI Rewrite",
        SCRIPTS["feature_engine"],
        args=[str(post_dir)]
    )

    # 2️⃣ Build final_ready_to_post/post_xxx
    run_script(
        "Ready to Post",
        SCRIPTS["ready_to_post"],
        args=[str(post_dir)]
    )

    st.success(f"✅ Post prepared successfully: {post_dir.name}")
    st.info("👉 Now click POST NOW")


# ---------------- POST TYPE ----------------
st.subheader("📌 Post Type")

ui_post_type = st.selectbox(
    "Select post type",
    ["Image", "Reel", "Story"],
    index=1
)


# ---------------- SCHEDULE POST ----------------
st.divider()
st.subheader("⏰ Schedule Post")

with st.form("schedule_form"):
    date = st.date_input("📅 Select date")
    time_ = st.time_input("⏰ Select time")
    submit_schedule = st.form_submit_button("📅 Schedule Later")

if submit_schedule:
    run_at = datetime.combine(date, time_).isoformat()

    # 🔥 Always pick FINAL prepared post (same as Post Now)
    final_base = Path("final_ready_to_post")
    
    # ✅ pick media ONLY from CURRENT post folder
    current_post_dir = max(
        [p for p in final_base.iterdir() if p.is_dir()],
        key=lambda d: d.stat().st_mtime
)
    # 🔥 pick BOTH image & video (same as Post Now)
    prepared_media = sorted(
        list(final_base.glob("post_*/*.mp4")) +
        list(final_base.glob("post_*/*.jpg")) +
        list(final_base.glob("post_*/*.jpeg")) +
        list(final_base.glob("post_*/*.png")),
        key=lambda p: p.stat().st_mtime
    )


    if not prepared_media:
        st.error("❌ No prepared posts found. Click Prepare Posts first.")
        st.stop()

    final_media = prepared_media[-1]   # 👈 LATEST prepared post

    jobs = []
    if Path(JOBS_FILE).exists():
        jobs = json.loads(Path(JOBS_FILE).read_text())

    for acc in selected_accounts: 
        username = acc
        session_file = f"sessions/session_{username}.json"

        job = {
            "id": uuid.uuid4().hex,
            "username": username,
            "session_file": session_file,
            "post_type": ui_post_type.lower(),
            "media_path": str(final_media),
            "scheduled_time": run_at,

            # watermark flags
            "enable_text_wm": enable_text_wm,
            "enable_png_wm": enable_png_wm,
            "watermark_text": watermark_text,
            "watermark_png": str(watermark_png_path) if watermark_png_path else None,
            "wm_x": wm_x,
            "wm_y": wm_y,

            "status": "pending"
        }

        jobs.append(job)


    Path(JOBS_FILE).write_text(json.dumps(jobs, indent=2))

    st.success("✅ Scheduled successfully")
    st.info("ℹ️ Scheduler runner will post automatically")


# ---------------- ACTION BUTTONS ----------------

# ---------------- POST NOW ----------------

import shutil
from pathlib import Path
from utils.watermark_video import add_story_watermark
from auto_scheduler import post_reel, post_story, post_image

from auto_scheduler import get_client
# col1, col2 = st.columns(2)


# ---------------- POST NOW ----------------
post_now = st.button("🚀 Post Now")

if post_now:
    current_post = st.session_state.post_dir
    final_base = Path("final_ready_to_post") / current_post.name

    # 1️⃣ Detect prepared media
    video_files = sorted(final_base.glob("*.mp4"))
    image_files = sorted(
        list(final_base.glob("*.jpg")) +
        list(final_base.glob("*.jpeg")) +
        list(final_base.glob("*.png"))
    )
    # UI selected post type (string)
    ui_post_type_val = ui_post_type.lower()


    # 🔍 Detect prepared media
    if video_files:
        original_path = video_files[-1]

        if ui_post_type_val == "story":
            detected_post_type = "story"
        else:
            detected_post_type = "reel"

    elif image_files:
        original_path = image_files[-1]

        if ui_post_type_val == "story":
            detected_post_type = "story"
        else:
            detected_post_type = "image"

    else:
        st.error("❌ No prepared media found. Please click Prepare Posts first.")
        st.stop()


    # 2️⃣ Post for each account
    for username in selected_accounts:  
        try:
            cl = get_logged_client(username)

            # unique copy per account
            unique_media = original_path.with_name(
                f"{original_path.stem}_{username}{original_path.suffix}"
            )
            shutil.copy(original_path, unique_media)

            wm_media = unique_media
            
            # ================= FINAL WATERMARK LOGIC =================

            suffix = wm_media.suffix.lower()

            # 🎥 VIDEO FILE (Reel / Story)
            if suffix == ".mp4":

                if enable_png_wm and watermark_png_path:
                    wm_media = Path(
                        add_png_watermark_to_video(
                            str(wm_media),
                            str(watermark_png_path),
                            x=wm_x,
                            y=wm_y
                        )
                    )

                if enable_text_wm and watermark_text:
                    wm_media = Path(
                        add_story_watermark(
                            str(wm_media),
                            watermark_text
                        )
                    )

            # 🖼 IMAGE FILE (Feed / Story)
            elif suffix in [".jpg", ".jpeg", ".png"]:

                if enable_png_wm and watermark_png_path:
                    from utils.watermark_image import add_png_watermark_to_image
                    wm_media = Path(
                        add_png_watermark_to_image(
                            str(wm_media),
                            str(watermark_png_path),
                            x=wm_x,
                            y=wm_y
                        )
                    )

                if enable_text_wm and watermark_text:
                    from utils.watermark_image import add_watermark_to_image
                    wm_media = Path(
                        add_watermark_to_image(
                            str(wm_media),
                            watermark_text
                        )
                    )


            final_caption = read_final_caption_from_media(str(original_path))

            # 3️⃣ POST
            if detected_post_type == "reel":
                cl.clip_upload(
                    path=str(wm_media),
                    caption=final_caption
            )

            elif detected_post_type == "image":
                cl.photo_upload(
                    path=str(wm_media),
                    caption=final_caption
            )

            elif detected_post_type == "story":
                cl.video_upload_to_story(
                    path=str(wm_media)
            )


            st.success(f"✅ Posted successfully for @{username}")

        except Exception as e:
            st.error(f"❌ Failed for @{username}: {e}")



elif page == "📥 Downloaded Posts":
    st.markdown("## 📥 Downloaded Instagram Posts")
    show_downloaded_posts()
    


    # Pipeline visualization
    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Automation Pipeline</div>
          <div class="section-sub">Full flow your backend already does — now visualized.</div>
          <div style="display:flex; gap:12px; margin-top:14px;">
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 1</div>
              <div class="metric-value" style="font-size:16px;">Download</div>
              <div class="metric-sub">instaloader.py</div>
            </div>
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 2</div>
              <div class="metric-value" style="font-size:16px;">Filter</div>
              <div class="metric-sub">filter.py</div>
            </div>
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 3</div>
              <div class="metric-value" style="font-size:16px;">Watermark</div>
              <div class="metric-sub">watermark.py</div>
            </div>
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 4</div>
              <div class="metric-value" style="font-size:16px;">AI Generate</div>
              <div class="metric-sub">feature4_engine.py</div>
            </div>
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 5</div>
              <div class="metric-value" style="font-size:16px;">Ready</div>
              <div class="metric-sub">ready_to_post.py</div>
            </div>
            <div class="metric-box" style="flex:1; text-align:center;">
              <div class="metric-label">STEP 6</div>
              <div class="metric-value" style="font-size:16px;">Schedule</div>
              <div class="metric-sub">auto_bulk_scheduler.py + scheduler_runner.py</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ⏱ Upcoming Jobs")
    upcoming = [j for j in jobs if j.get("status") in ("pending", "failed")]
    upcoming = sorted(upcoming, key=parse_time)

    if not upcoming:
        st.info("No pending or failed jobs. All clear ✅")
    else:
        for j in upcoming[:10]:
            status = j.get("status", "pending")
            st.markdown(
                """
                <div class="job-card">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                      <div class="job-path">
                        {j['media_path'].split('final_ready_to_post')[-1].lstrip('\\\\/')}
                      </div>
                      <div class="job-meta">
                        ID: {j['id'][:10]} · User: @{j['username']} · Created: {j.get('created_at','-')}
                      </div>
                    </div>
                    <div style="text-align:right;">
                      <div style="font-size:12px; color:#e5e7eb; font-weight:500;">
                        {j['scheduled_time']}
                      </div>
                      <div style="margin-top:4px;">
                        {status_badge(status)}
                      </div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )



# ==========================
# 1) DOWNLOAD & FILTER
# ==========================

elif page == "1) Download & Filter":
    st.markdown("## 1️⃣ Download & Filter")

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Instaloader — Download posts</div>
          <div class="section-sub">Run your <code>instaloader.py</code> script to pull fresh posts.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("⬇ Run instaloader.py", use_container_width=True):
        run_script("Instaloader", SCRIPTS["instaloader"])

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Filter media</div>
          <div class="section-sub">Clean invalid / broken downloads using <code>filter.py</code>.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🧹 Run filter.py", use_container_width=True):
        run_script("Filter", SCRIPTS["filter"])

# ==========================
# 2) WATERMARK
# ==========================

elif page == "2) Watermark":
    st.markdown("## 2️⃣ Watermark")

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Apply watermark on media</div>
          <div class="section-sub">
            Uses <code>watermark.py</code> to read from filtered downloads and write to
            <code>filtered_downloads_watermarked/</code>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("💧 Run watermark.py", use_container_width=True):
        run_script("Watermark", SCRIPTS["watermark"])

# ==========================
# 3) AI GENERATION
# ==========================

elif page == "3) AI Generation":
    st.markdown("## 3️⃣ AI Caption / Hook / CTA / Hashtags")

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Run feature4_engine.py</div>
          <div class="section-sub">
            Generates caption, hook, CTA, comments, hashtags, keywords, analysis for each post under
            <code>filtered_downloads_watermarked/</code>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🤖 Run feature4_engine.py", use_container_width=True):
        run_script("Feature4 Engine", SCRIPTS["feature_engine"])

# ==========================
# 4) READY-TO-POST
# ==========================

elif page == "4) Ready-to-Post":
    st.markdown("## 4️⃣ Build final ready_to_post folders")

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Create final_ready_to_post</div>
          <div class="section-sub">
            Uses <code>ready_to_post.py</code> to assemble each post folder with media + final_caption.txt.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("📦 Run ready_to_post.py", use_container_width=True):
        run_script("Ready to Post", SCRIPTS["ready_to_post"])

# ==========================
# 5) BULK SCHEDULER
# ==========================

elif page == "5) Bulk Scheduler":
    st.markdown("## 5️⃣ Auto Bulk Scheduler")

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">Create jobs from final_ready_to_post</div>
          <div class="section-sub">
            Runs <code>auto_bulk_scheduler.py</code> and appends jobs into <code>scheduled_jobs.json</code>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🗂 Run auto_bulk_scheduler.py", use_container_width=True):
        run_script("Auto Bulk Scheduler", SCRIPTS["auto_bulk"])

    st.markdown("### Jobs summary")
    st.write(f"Jobs file: `{JOBS_FILE}`")
    st.write(f"Total jobs: {total_jobs}, Pending: {pending_jobs}, Done: {done_jobs}, Failed: {failed_jobs}")

# ==========================
# 6) JOBS MONITOR
# ==========================

elif page == "6) Jobs Monitor":
    st.markdown("## 6️⃣ Jobs Monitor (JSON view)")

    st.info(
        "Posting actually runs from `scheduler_runner.py` via Windows Task Scheduler. "
        "This page is a live view / manual editor for `scheduled_jobs.json`."
    )

    filter_status = st.selectbox(
        "Filter by status",
        options=["all", "pending", "running", "failed", "done"],
        index=0,
    )

    filtered = jobs
    if filter_status != "all":
        filtered = [j for j in jobs if j.get("status") == filter_status]

    if not filtered:
        st.info("No jobs for this filter.")
    else:
        for j in filtered:
            status = j.get("status", "pending")
            st.markdown(
                """
                <div class="job-card">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                      <div class="job-path">
                        {j['media_path'].split('final_ready_to_post')[-1].lstrip('\\\\/')}
                      </div>
                      <div class="job-meta">
                        ID: {j['id']}<br>
                        User: @{j['username']}<br>
                        Scheduled: {j['scheduled_time']}<br>
                        Created: {j.get('created_at','-')}<br>
                        Retries: {j.get('retries',0)}
                      </div>
                    </div>
                    <div style="text-align:right;">
                      <div>{status_badge(status)}</div>
                      <div class="job-meta" style="margin-top:6px; max-width:260px;">
                        Last error: {j.get('last_error','-')[:110]}
                      </div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Manual status update")
    colA, colB, colC = st.columns(3)
    with colA:
        target_id = st.text_input("Job ID")
    with colB:
        new_status = st.selectbox(
            "New status",
            options=["pending", "failed", "done", "running"],
        )
    with colC:
        if st.button("Update job"):
            if not target_id.strip():
                st.error("Enter job ID.")
            else:
                jobs2 = load_jobs()
                ok = False
                for job in jobs2:
                    if job["id"] == target_id.strip():
                        job["status"] = new_status
                        ok = True
                        break
                if ok:
                    save_jobs(jobs2)
                    st.success("Job updated.")
                    st.rerun()
                else:
                    st.error("Job ID not found.")

# ==========================
# SETTINGS / INFO
# ==========================

else:
    st.markdown("## ⚙️ Settings & Info")

    st.markdown(
        f"""
        <div class="glass-card">
          <div class="section-title">Paths</div>
          <div class="section-sub">
            <code>Base dir:</code> {BASE_DIR}<br>
            <code>Jobs file:</code> {JOBS_FILE}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title">How this UI works</div>
          <div class="section-sub">
            <ul>
              <li>Ye dashboard tumhare existing Python scripts ko <code>subprocess</code> se run karta hai.</li>
              <li>Real posting: <code>scheduler_runner.py</code> + Windows Task Scheduler se hoti hai (jaise abhi setup hai).</li>
              <li>Agar isse Streamlit Cloud par host karoge, wahan local scripts / JSON direct access nahi milega –
              uske liye alag API bridge banana padega (future upgrade).</li>
            </ul>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔁 Reload jobs from disk"):
        st.experimental_rerun()
