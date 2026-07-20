from http.server import BaseHTTPRequestHandler
from spotifyappledb import supabase
import html
from email.utils import formatdate


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
                    is_audio_generated
                """)
                .eq("is_audio_generated", True)
                .order("id", desc=True)
                .limit(50)
                .execute()
            )

            # Original filtering
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
                    f"Audio URL: {r.get('audio_url')[:80] if r.get('audio_url') else 'MISSING'}"
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

                length = "7200000"  # placeholder

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
<guid>{audio_url}</guid>
<pubDate>{current_date}</pubDate>
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
<itunes:author>Auto Intel Daily</itunes:author>
<itunes:category text="Technology"/>
<itunes:explicit>false</itunes:explicit>
<itunes:image href="https://oklpimfespctlovlijzn.supabase.co/storage/v1/object/public/spotify-apple-podcast-bg-image/cover.jpg"/>
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
            print("ERROR in RSS handler:", str(e))  # extra error logging
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())
