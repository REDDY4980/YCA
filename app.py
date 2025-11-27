import os
import streamlit as st

from Senti import extract_video_id, analyze_sentiment, bar_chart, plot_sentiment
from YoutubeCommentScrapper import (
    save_video_comments_to_csv,
    get_channel_info,
    youtube,
    get_channel_id,
    get_video_stats,
)


# ===========================================================
# Helper — Delete old CSVs except current video
# ===========================================================
def delete_old_csvs(current_video_id):
    for file in os.listdir():
        if file.endswith(".csv") and file != f"{current_video_id}.csv":
            os.remove(file)


# ===========================================================
# Page Config
# ===========================================================
st.set_page_config(
    page_title="YCA | YouTube Comment Analyzer",
    page_icon="🧠",
    layout="wide",
)


# ===========================================================
# Global Styling
# ===========================================================
custom_css = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #000000 100%);
    color: #f9fafb;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding-top: 20px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(3, 7, 18, 0.85);
    border-right: 1px solid rgba(148, 163, 184, 0.4);
}

/* Cards */
.metric-card {
    padding: 1.1rem 1.3rem;
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.25);
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(6px);
}
.metric-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #9ca3af;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
}

/* Center title */
.app-title {
    text-align: center;
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    margin-top: 0.5rem;
}
.app-subtitle {
    text-align: center;
    font-size: 1rem;
    color: #9ca3af;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ===========================================================
# Sidebar
# ===========================================================
with st.sidebar:
    st.markdown("## YCA Dashboard")
    st.caption("YouTube Comment Analyzer")
    st.markdown("---")
    st.markdown("Paste a YouTube URL and click **Analyse**.")


# ===========================================================
# Center Logo + Title
# ===========================================================
center = st.columns([1, 2, 1])[1]
with center:
    st.markdown('<div class="app-title">YCA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">YouTube Comment Sentiment & Irrelevance Analyzer</div>',
        unsafe_allow_html=True,
    )

st.markdown("")
st.markdown("")


# ===========================================================
# Centered URL Input + Analyse Button
# ===========================================================
input_area = st.columns([1, 2, 1])[1]

with input_area:
    youtube_link = st.text_input(
        "Enter YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=xxxx",
    )
    analyse_btn = st.button("Analyse", use_container_width=True)


# ===========================================================
# CORE FUNCTIONALITY — PROCESS PIPELINE
# ===========================================================
if youtube_link and analyse_btn:
    video_id = extract_video_id(youtube_link)

    if not video_id:
        st.error("❌ Invalid YouTube link. Enter a valid URL.")
        st.stop()

    with st.spinner("Fetching data and analyzing... Please wait."):
        # ---------------------------------------------------
        # 1. Get channel ID
        # ---------------------------------------------------
        try:
            channel_id = get_channel_id(video_id)
        except Exception as e:
            st.error(f"❌ Error getting channel ID:\n\n{e}")
            st.stop()

        # ---------------------------------------------------
        # 2. Download Comments → CSV
        # ---------------------------------------------------
        try:
            csv_file = save_video_comments_to_csv(video_id)
            delete_old_csvs(video_id)
        except Exception as e:
            st.error(f"❌ Error fetching YouTube comments:\n\n{e}")
            st.stop()

        # ---------------------------------------------------
        # 3. Channel Info
        # ---------------------------------------------------
        try:
            ch_info = get_channel_info(youtube, channel_id)
        except:
            ch_info = None

        # ---------------------------------------------------
        # 4. Video Stats
        # ---------------------------------------------------
        stats = get_video_stats(video_id)

        # ---------------------------------------------------
        # 5. Sentiment Analysis
        # ---------------------------------------------------
        try:
            results = analyze_sentiment(csv_file)
        except Exception as e:
            st.error(f"❌ Sentiment Analysis Failed:\n\n{e}")
            st.stop()


    # =====================================================
    # TABS
    # =====================================================
    tab_overview, tab_sentiment, tab_channel = st.tabs(
        ["📊 Overview", "📈 Sentiment Insights", "📺 Channel Details"]
    )


    # =====================================================
    # TAB 1 — OVERVIEW
    # =====================================================
    with tab_overview:
        st.markdown("### 🎯 Video & Comment Summary")

        row = st.columns([2, 3])

        # ----- Video area -----
        with row[0]:
            st.video(youtube_link)

            if ch_info:
                st.image(ch_info["channel_logo_url"], width=180)
                st.markdown(f"### {ch_info['channel_title']}")
                st.caption(f"Created on: {str(ch_info['channel_created_date'])[:10]}")

        # ----- Stats area -----
        with row[1]:
            st.markdown("")

            col_stats = st.columns(2)

            # YouTube count
            with col_stats[0]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">YouTube Comment Count</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-value">{stats.get("commentCount", "N/A")}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # Analyzed count
            with col_stats[1]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Comments Analyzed</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="metric-value">{results["total_analyzed"]}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("This is actual comments fetched & analyzed.")
                st.markdown("</div>", unsafe_allow_html=True)



    # =====================================================
    # TAB 2 — SENTIMENT INSIGHTS
    # =====================================================
    with tab_sentiment:
        st.markdown("### 📈 Sentiment Classification (Positive / Negative / Irrelevant)")

        srow = st.columns(4)

        with srow[0]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{results["total_analyzed"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with srow[1]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Positive</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{results["num_positive"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with srow[2]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Negative</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{results["num_negative"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with srow[3]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Irrelevant</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{results["num_irrelevant"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        bar_chart(csv_file)
        plot_sentiment(csv_file)


    # =====================================================
    # TAB 3 — CHANNEL DETAILS
    # =====================================================
    with tab_channel:
        if ch_info:
            st.markdown(f"### 📺 {ch_info['channel_title']}")
            st.write(ch_info.get("channel_description", "No description available."))

            st.markdown("---")

            c1, c2, c3 = st.columns(3)
            c1.metric("Subscribers", ch_info["subscriber_count"])
            c2.metric("Total Videos", ch_info["video_count"])
            c3.metric("Created On", str(ch_info["channel_created_date"])[:10])

        else:
            st.warning("Channel information not available.")
