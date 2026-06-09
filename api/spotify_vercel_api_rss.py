from http.server import BaseHTTPRequestHandler
from spotifyappledb import supabase
import html
from email.utils import formatdate


class handler(BaseHTTPRequestHandler):

    # ✅ FIX 1: ADD HEAD SUPPORT (IMPORTANT)
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "application/xml")
        self.end_headers()

    def do_GET(self):

        try:

            current_date = formatdate(usegmt=True)

            data = (
                supabase.table("news")
                .select("*")
                .eq("is_audio_generated", True)
                .order("id", desc=True)
                .limit(50)
                .execute()
            )

            rows = data.data

            rss_items = ""

            for row in rows:

                title = row.get("title", "No Title")

                try:
                    title = title.encode("latin1").decode("utf-8")
                except:
                    pass

                title = html.escape(title)

                audio_url = row.get("audio_url")

                if not audio_url:
                    continue

                audio_url = audio_url.split("?")[0]

                rss_items += f"""
<item>
<title>{title}</title>
<description>{title}</description>
<enclosure url="{audio_url}" type="audio/mpeg" />
<guid isPermaLink="false">{audio_url}</guid>
<pubDate>{current_date}</pubDate>
<itunes:duration>03:00</itunes:duration>
<itunes:explicit>false</itunes:explicit>
</item>
"""

            rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
xmlns:atom="http://www.w3.org/2005/Atom">

<channel>

<title>AI Podcast</title>

<link>https://spotify-apple-podcast-rss.vercel.app/</link>

<atom:link href="https://spotify-apple-podcast-rss.vercel.app/" rel="self" type="application/rss+xml"/>

<description>AI generated news podcast</description>

<language>en-us</language>
<itunes:type>episodic</itunes:type>
<itunes:author>AI Podcast System</itunes:author>
<itunes:category text="Technology"/>
<itunes:explicit>false</itunes:explicit>

<itunes:owner>
<itunes:name>AI Podcast</itunes:name>
<itunes:email>personamize.ai@gmail.com</itunes:email>
</itunes:owner>

<itunes:image href="https://oklpimfespctlovlijzn.supabase.co/storage/v1/object/public/spotify-apple-podcast-bg-image/cover.jpg"/>

<lastBuildDate>{current_date}</lastBuildDate>

{rss_items}

</channel>
</rss>
"""

            self.send_response(200)
            self.send_header("Content-type", "application/xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(rss_feed.encode("utf-8"))

        except Exception as e:

            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())
