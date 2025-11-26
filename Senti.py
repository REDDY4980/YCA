
import csv
import re
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import Dict
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_sia = None

def _get_sia() -> SentimentIntensityAnalyzer:
    global _sia
    if _sia is not None:
        return _sia
    try:
        _sia = SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download("vader_lexicon")
        _sia = SentimentIntensityAnalyzer()
    return _sia

def extract_video_id(youtube_link: str):
    video_id_regex = r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(video_id_regex, youtube_link)
    if match:
        return match.group(1)
    return None

def is_off_topic(comment: str) -> bool:
    c = comment.lower().strip()
    if len(c.split()) <= 2:
        return True
    if re.fullmatch(r"[^\w\s]+", c):
        return True
    irrelevant_words = ["ok", "nice", "bro", "first", "hmm", "lol"]
    if c in irrelevant_words:
        return True
    return False

def analyze_sentiment(csv_file: str) -> Dict[str, int]:
    sid = _get_sia()
    comments = []
    with open(csv_file, "r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            text = row.get("Comment", "").strip()
            if text:
                comments.append(text)

    num_positive = 0
    num_negative = 0
    num_irrelevant = 0

    for comment in comments:
        if is_off_topic(comment):
            num_irrelevant += 1
            continue
        scores = sid.polarity_scores(comment)
        c = scores["compound"]
        if c >= 0.05:
            num_positive += 1
        elif c <= -0.05:
            num_negative += 1
        else:
            num_irrelevant += 1

    return {
        "num_positive": num_positive,
        "num_negative": num_negative,
        "num_irrelevant": num_irrelevant,
        "total_analyzed": num_positive + num_negative + num_irrelevant,
    }

def bar_chart(csv_file: str) -> None:
    results = analyze_sentiment(csv_file)
    df = pd.DataFrame({
        "Sentiment": ["Positive", "Negative", "Irrelevant"],
        "Count": [
            results["num_positive"],
            results["num_negative"],
            results["num_irrelevant"],
        ],
    })
    fig = px.bar(
        df,
        x="Sentiment",
        y="Count",
        color="Sentiment",
        color_discrete_sequence=["#22c55e", "#ef4444", "#9ca3af"],
        title="Sentiment Distribution",
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_sentiment(csv_file: str) -> None:
    results = analyze_sentiment(csv_file)
    labels = ["Positive", "Negative", "Irrelevant"]
    values = [
        results["num_positive"],
        results["num_negative"],
        results["num_irrelevant"],
    ]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                textinfo="label+percent",
                marker=dict(colors=["#22c55e", "#ef4444", "#9ca3af"]),
            )
        ]
    )
    fig.update_layout(
        title={"text": "Sentiment Distribution (P/N/Irrelevant)", "x": 0.5}
    )
    st.plotly_chart(fig, use_container_width=True)
