#!/usr/bin/env python3
"""Record the map as an MP4, sized for a phone feed.

The page animates in a browser; this drives one headless Chromium through the
timeline, captures a frame per step and hands them to ffmpeg. Playback is
stopped and each frame is seeked exactly, so the result is deterministic rather
than dependent on how fast the machine happened to render.

Portrait by default, 1080x1920: these birds span 82 degrees of latitude against
66 of longitude, so the data is taller than it is wide and a vertical frame
wastes less of it than a landscape one.

Requires the self-contained build, which carries its own data:

    python3 scripts/build_standalone.py

Usage
-----
    python3 scripts/render_video.py
    python3 scripts/render_video.py --seconds 45 --size 1080x1080
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("no ffmpeg found\n  pip install imageio-ffmpeg")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", default="dist/where-the-storks-went.html", type=Path)
    ap.add_argument("--out", default="dist/where-the-storks-went.mp4", type=Path)
    ap.add_argument("--size", default="1080x1920", help="WxH; 1080x1920 is a phone feed")
    ap.add_argument("--seconds", type=float, default=40.0, help="length of the migration run")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--hold", type=float, default=2.0, help="seconds to hold on the last frame")
    ap.add_argument("--chrome", default="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    args = ap.parse_args()

    if not args.page.exists():
        raise SystemExit(f"missing {args.page}\n  run: python3 scripts/build_standalone.py")
    width, height = (int(v) for v in args.size.lower().split("x"))
    frames = max(1, int(round(args.seconds * args.fps)))
    ffmpeg = find_ffmpeg()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("playwright is needed\n  pip install playwright")

    tmp = Path(tempfile.mkdtemp(prefix="storkframes-"))
    print(f"{frames} frames at {width}x{height}, {args.fps} fps -> {tmp}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=args.chrome,
                                        args=["--no-sandbox", "--disable-gpu",
                                              "--hide-scrollbars"])
            page = browser.new_context(viewport={"width": width, "height": height},
                                       device_scale_factor=1).new_page()
            # The standalone build carries its data inline, so a file:// load is
            # enough and no server has to be running.
            page.goto(args.page.resolve().as_uri(), wait_until="load", timeout=120_000)
            page.wait_for_function("window.__render !== undefined", timeout=120_000)
            # The backdrop arrives as a data URI and decodes asynchronously.
            page.wait_for_timeout(2500)
            page.evaluate("window.__render.bare(true)")
            page.wait_for_timeout(500)

            span = page.evaluate("window.__render.span()")
            print(f"timeline is {span} hours")
            for i in range(frames):
                page.evaluate("t => window.__render.seek(t)", span * i / (frames - 1 or 1))
                page.screenshot(path=str(tmp / f"f{i:05d}.png"))
                if (i + 1) % 60 == 0 or i == frames - 1:
                    print(f"  {i+1}/{frames} frames", flush=True)
            browser.close()

        # Holding on the last frame stops the loop from snapping back to an
        # empty map the instant the migration finishes.
        last = tmp / f"f{frames-1:05d}.png"
        for k in range(int(round(args.hold * args.fps))):
            shutil.copy(last, tmp / f"f{frames+k:05d}.png")

        args.out.parent.mkdir(parents=True, exist_ok=True)
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
               "-framerate", str(args.fps), "-i", str(tmp / "f%05d.png"),
               "-c:v", "libx264", "-preset", "slow", "-crf", "20",
               # yuv420p and even dimensions are what phone players and Reddit
               # will actually accept.
               "-pix_fmt", "yuv420p",
               "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
               "-movflags", "+faststart", str(args.out)]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    mb = args.out.stat().st_size / 1e6
    print(f"wrote {args.out} ({mb:.1f} MB, {frames/args.fps + args.hold:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
