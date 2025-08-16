import asyncio
import os
import re
from typing import Union

from yt_dlp import YoutubeDL
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from ArchMusic.utils.database import is_on_off
from ArchMusic.utils.formatters import time_to_seconds


def cookiefile():
    cookie_dir = "cookies"
    if not os.path.exists(cookie_dir) or not os.listdir(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    return os.path.join(cookie_dir, cookies_files[0])


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text, offset, length = "", None, None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset is None:
            return None
        return text[offset: offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = 0 if duration_min is None else int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]

        args = [
            "yt-dlp",
            "-g",
            "-f", "best[height<=?720][width<=?1280]",
            f"{link}"
        ]
        if cookiefile():
            args.insert(1, "--cookies")
            args.insert(2, cookiefile())

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        link = link.split("&")[0]
        cmd = (
            f"yt-dlp -i --compat-options no-youtube-unavailable-videos "
            f"--get-id --flat-playlist --playlist-end {limit} --skip-download '{link}' "
            f"2>/dev/null"
        )
        playlist = await shell_cmd(cmd)
        try:
            return [key for key in playlist.split("\n") if key]
        except Exception:
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            track_details = {
                "title": result["title"],
                "link": result["link"],
                "vidid": result["id"],
                "duration_min": result["duration"],
                "thumb": result["thumbnails"][0]["url"].split("?")[0],
                "cookiefile": cookiefile(),
            }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        ydl_opts = {"quiet": True}
        ydl = YoutubeDL(ydl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r.get("formats", []):
                try:
                    fmt = {
                        "format": format.get("format"),
                        "filesize": format.get("filesize") or 0,
                        "format_id": format.get("format_id"),
                        "ext": format.get("ext"),
                        "format_note": format.get("format_note"),
                        "yturl": link,
                        "cookiefile": cookiefile(),
                    }
                    if fmt["format"] and "dash" not in fmt["format"].lower():
                        formats_available.append(fmt)
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_optssx = {
                "cookiefile": cookiefile() if cookiefile() else None,
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            info = x.extract_info(link, False)
            if not info.get("formats"):
                ydl_optssx["format"] = "best"
                x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
                info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "cookiefile": cookiefile() if cookiefile() else None,
                "format": "best[height<=?720][width<=?1280]",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            info = x.extract_info(link, False)
            if not info.get("formats"):
                ydl_optssx["format"] = "best"
                x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
                info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookiefile() if cookiefile() else None,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            info = x.extract_info(link, False)
            if not info.get("formats"):
                ydl_optssx["format"] = "best"
                x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookiefile() if cookiefile() else None,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            info = x.extract_info(link, False)
            if not info.get("formats"):
                ydl_optssx["format"] = "bestaudio/best"
                x = YoutubeDL({k: v for k, v in ydl_optssx.items() if v is not None})
            x.download([link])

        try:
            if songvideo:
                await loop.run_in_executor(None, song_video_dl)
                return f"downloads/{title}.mp4"
            elif songaudio:
                await loop.run_in_executor(None, song_audio_dl)
                return f"downloads/{title}.mp3"
            elif video:
                if await is_on_off(1):
                    direct = True
                    downloaded_file = await loop.run_in_executor(None, video_dl)
                else:
                    args = [
                        "yt-dlp",
                        "-g",
                        "-f", "best[height<=?720][width<=?1280]",
                        f"{link}"
                    ]
                    if cookiefile():
                        args.insert(1, "--cookies")
                        args.insert(2, cookiefile())
                    proc = await asyncio.create_subprocess_exec(
                        *args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    if stdout:
                        downloaded_file = stdout.decode().split("\n")[0]
                        direct = None
                    else:
                        return None
            else:
                direct = True
                downloaded_file = await loop.run_in_executor(None, audio_dl)
            return downloaded_file, direct
        except Exception as e:
            print(f"Download error: {e}")
            return None
