from http.server import BaseHTTPRequestHandler
from spotifyappledb import supabase
import html
from email.utils import formatdate
from datetime import datetime


class handler(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "application/xml")
        self.end_headers()

    def do_GET(self):
        try:
            current_date = formatdate(usegmt=True)

            data = (
                supabase
                .table("news")
                .select("""
                    id,
                    title,
                    spotify_title,
                    spotify_description,
                    audio_url,
                    is_audio_generated,
                    created_at,
                    audio_duration,
                    audio_duration_seconds,
                    audio_file_size,
                    episode_pub_date
                """)
                .eq("is_audio_generated", True)
                .order("id", desc=True)
                .limit(50)
                .execute()
            )

            # Filter rows that actually have audio
            rows = [ 
                row for row in data.data
                if row.get("audio_url")
            ]

            # ==================== DEBUG PRINTS ====================
            print("TOTAL ROWS fetched from Supabase:", len(data.data))
            print("ROWS with audio_url:", len(rows))
            
            print("\n--- Row Details ---")
            for r in rows:
                print(
                    f"ID: {r['id']} | "
                    f"Title: {r.get('title')[:60] if r.get('title') else 'N/A'}... | "
                    f"Audio URL: {r.get('audio_url')[:80] if r.get('audio_url') else 'MISSING'} | "
                    f"File Size: {r.get('audio_file_size')} | "
                    f"Duration: {r.get('audio_duration')} | "
                    f"Episode Pub Date: {r.get('episode_pub_date')}"
                )
            print("--- End Debug ---\n")
            # ====================================================

            rss_items = ""

            for row in rows:
                audio_url = row.get("audio_url")
                if not audio_url:
                    continue

                title = html.escape(
                    row.get("spotify_title")
                    or row.get("title")
                    or "AI Podcast Episode"
                )

                description = html.escape(
                    row.get("spotify_description")
                    or "AI generated podcast episode"
                )

                # Clean URL (remove query params)
                audio_url = audio_url.split("?")[0]

                # ==================== DYNAMIC METADATA ====================

                # 1. Enclosure length (file size in bytes)
                length = str(row.get("audio_file_size") or 0)

                # 2. Publication Date (prefer episode_pub_date)
                if row.get("episode_pub_date"):
                    try:
                        dt = datetime.fromisoformat(
                            row["episode_pub_date"].replace("Z", "+00:00")
                        )
                        pub_date = formatdate(timeval=dt.timestamp(), usegmt=True)
                    except Exception:
                        pub_date = current_date
                elif row.get("created_at"):
                    try:
                        dt = datetime.fromisoformat(
                            row["created_at"].replace("Z", "+00:00")
                        )
                        pub_date = formatdate(timeval=dt.timestamp(), usegmt=True)
                    except Exception:
                        pub_date = current_date
                else:
                    pub_date = current_date

                # 3. iTunes Duration
                duration = row.get("audio_duration") or "00:00:00"

                # =======================================================

                rss_items += f"""
<item>
<title>{title}</title>
<description>{description}</description>
<link>{audio_url}</link>
<enclosure 
    url="{audio_url}" 
    length="{length}" 
    type="audio/mpeg"
/>
<guid isPermaLink="false">episode-{row['id']}</guid>
<pubDate>{pub_date}</pubDate>
<itunes:duration>{duration}</itunes:duration>
<itunes:summary>{description}</itunes:summary>
</item>
"""

            rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
<title>Auto Intel Daily</title>
<link>https://spotify-apple-podcast-rss.vercel.app/</link>
<description>AI powered automotive news podcast</description>
<language>en-us</language>
<itunes:type>episodic</itunes:type>
<itunes:author>Auto Intel</itunes:author>
<itunes:category text="Technology"/>
<itunes:explicit>false</itunes:explicit>
<itunes:owner>
    <itunes:name>Auto Intel</itunes:name>
    <itunes:email>personamize.ai@gmail.com</itunes:email>
</itunes:owner>
<itunes:image href="https://oklpimfespctlovlijzn.supabase.co/storage/v1/object/public/spotify-apple-podcast-bg-image/cover.png"/>
<lastBuildDate>{current_date}</lastBuildDate>

{rss_items}

</channel>
</rss>
"""

            self.send_response(200)
            self.send_header("Content-type", "application/rss+xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(rss_feed.encode("utf-8"))

        except Exception as e:
            print("ERROR in RSS handler:", str(e))
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))