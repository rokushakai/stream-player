import yt_dlp
from dataclasses import dataclass
from typing import Optional


@dataclass
class StreamInfo:
    url: str
    title: str
    duration: Optional[float]


class StreamResolver:
    """Extracts metadata from YouTube and other sites using yt-dlp."""

    def resolve(self, url: str) -> StreamInfo:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return StreamInfo(
                url=url,
                title=info.get('title', 'Unknown'),
                duration=info.get('duration'),
            )
