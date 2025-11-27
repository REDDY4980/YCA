
import csv
import os
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from config import API_KEY as CONFIG_KEY
except:
    CONFIG_KEY = None

API_KEY = st.secrets.get("API_KEY")

if not API_KEY:
    raise RuntimeError("API key missing in config.py or secrets.")

youtube = build("youtube", "v3", developerKey=API_KEY)

def get_channel_id(video_id: str) -> str:
    try:
        response = youtube.videos().list(part="snippet", id=video_id).execute()
        items = response.get("items", [])
        if not items:
            raise ValueError("Invalid video ID.")
        return items[0]["snippet"]["channelId"]
    except HttpError as e:
        raise ValueError(f"Error getting channel ID: {e}")

def save_video_comments_to_csv(video_id: str) -> str:
    comments = []
    filename = f"{video_id}.csv"

    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
        )
        results = request.execute()
    except HttpError as e:
        raise ValueError(f"Error fetching comments: {e}")

    while results:
        for item in results.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comments.append([
                top.get("authorDisplayName", "Unknown"),
                top.get("textDisplay", "")
            ])

            if "replies" in item:
                for reply in item["replies"].get("comments", []):
                    rs = reply["snippet"]
                    comments.append([
                        rs.get("authorDisplayName", "Unknown"),
                        rs.get("textDisplay", "")
                    ])

        if "nextPageToken" in results:
            next_token = results["nextPageToken"]
            try:
                results = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=100,
                    textFormat="plainText",
                    pageToken=next_token,
                ).execute()
            except HttpError:
                break
        else:
            break

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "Comment"])
        writer.writerows(comments)

    return filename

def get_video_stats(video_id: str) -> dict:
    try:
        response = youtube.videos().list(part="statistics", id=video_id).execute()
        items = response.get("items", [])
        if not items:
            return {}
        return items[0]["statistics"]
    except HttpError:
        return {}

def get_channel_info(youtube_client, channel_id: str):
    try:
        response = youtube_client.channels().list(
            part="snippet,statistics,brandingSettings",
            id=channel_id
        ).execute()
        items = response.get("items", [])
        if not items:
            return None
        data = items[0]
        return {
            "channel_title": data["snippet"].get("title"),
            "video_count": data["statistics"].get("videoCount"),
            "channel_logo_url": data["snippet"]["thumbnails"]["high"]["url"],
            "channel_created_date": data["snippet"].get("publishedAt"),
            "subscriber_count": data["statistics"].get("subscriberCount"),
            "channel_description": data["snippet"].get("description"),
        }
    except HttpError:
        return None
