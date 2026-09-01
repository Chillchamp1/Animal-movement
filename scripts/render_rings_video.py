#!/usr/bin/env python3
"""Record rings.html as portrait MP4s, sized for a phone feed.

Three clips come off the same page: the polar pair, and the globe pair in each
of its two ordinary camera modes -- ground-locked, where the shade sweeps a
still Earth, and sun-locked, where the light stands still and the Earth turns
under it.

The page carries the recording layout itself. Setting `VID` moves the date and
the clock so each appears once rather than once per plate, drops the two track
panels under the map and the local-solar readings off the globes, and lets the
discs fill the frame instead of sitting in a letterbox. It changes chrome and
nothing else: a frame grabbed here is the same astronomy as a frame on screen.

Two things are deliberate. Frames are advanced by index rather than by wall
clock, so the cadence does not depend on how fast the machine rendered. And
they come straight off the canvas with toDataURL rather than through a page
screenshot, which skips the compositor -- the slowest thing in the loop -- and
lets the two globes be captured at full height each and stacked here.

Speed is read out of the page rather than set here, so a clip runs at exactly
the rate the page runs at. One clip is one year.

Requires playwright and a Chromium; ffmpeg comes from PATH or imageio-ffmpeg.

Usage
-----
    python3 scripts/render_rings_video.py                 # all three
    python3 scripts/render_rings_video.py --job polar
    python3 scripts/render_rings_video.py --crf 24        # smaller files
    python3 scripts/render_rings_video.py --seconds 3     # a quick look
"""

from __future__ import annotations

import argparse
import base64
import glob
import io
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

# Which plate each job records, and which camera mode it puts the globes in.
JOBS = {
    "polar":  ("polar", None,     "daylight-polar.mp4"),
    "ground": ("globe", "ground", "daylight-ground.mp4"),
    "sun":    ("globe", "sun",    "daylight-sun.mp4"),
}

# The page is a whole document with panels, prose and controls. Recording wants
# one plate filling the frame, so everything else is hidden and the panel is
# told to be exactly half the viewport (globes) or all of it (map). The rest of
# the layout is untouched, which is why this lives here and not in the page.
HIDE_ALL = """
  body{padding:0!important;background:#0b1017!important}
  .wrap>*{display:none!important}
  .wrap>.stage{display:block!important;margin:0!important}
  .panel{border:0!important;border-radius:0!important;padding:0!important;
    box-shadow:none!important;aspect-ratio:auto!important}
"""
POLAR_CSS = HIDE_ALL + """
  .stage>div:nth-child(2){display:none!important}
  .panel.tall{width:%(w)dpx!important;height:%(h)dpx!important}
"""
GLOBE_CSS = HIDE_ALL + """
  .stage>div:first-child{display:none!important}
  .stage>div:nth-child(2)>.camrow,.stage>div:nth-child(2)>.cols{display:none!important}
  .globes{display:grid!important;grid-template-columns:1fr!important;gap:0!important}
  .panel.globe{width:%(w)dpx!important;height:%(half)dpx!important}
"""


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("no ffmpeg found\n  pip install imageio-ffmpeg")


def find_chrome(given: str | None) -> str:
    if given:
        return given
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise SystemExit("no Chromium found; pass --chrome")


def grab(page, canvas_id: str, quality: float):
    from PIL import Image
    url = page.evaluate(f"()=>$('{canvas_id}').toDataURL('image/jpeg',{quality})")
    return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))


def capture(job: str, args, tmp: Path) -> int:
    from PIL import Image
    from playwright.sync_api import sync_playwright

    kind, mode, _ = JOBS[job]
    # Captured at device_scale_factor 3 off a third-size viewport: the canvas
    # comes out at the full 1080 wide without asking the layout engine for a
    # 1080-wide page.
    vw, vh = args.width // args.scale, args.height // args.scale
    css = (POLAR_CSS if kind == "polar" else GLOBE_CSS) % {
        "w": vw, "h": vh, "half": vh // 2}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=find_chrome(args.chrome),
            args=["--use-gl=angle", "--use-angle=swiftshader",
                  "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = browser.new_page(viewport={"width": vw, "height": vh},
                                color_scheme="dark",
                                device_scale_factor=args.scale)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # rings.html carries its mask and terrain inline, so file:// is enough.
        page.goto(args.page.resolve().as_uri(), wait_until="load", timeout=120_000)
        page.wait_for_timeout(2600)
        page.add_style_tag(content=css)
        page.evaluate("""([mode, dpr]) => {
          playing = false; VID = true; DPR_CAP = dpr;
          CURVES = false;                 /* the two track panels are gone */
          if (mode) {
            camMode = mode;
            /* A stacked pair would say the date twice and the hour twice, so
               each sphere is told which of its four corner captions it draws.
               The survivors land in the band between the two. */
            OPTS.find(o => o.id === 'gN').vid = {time: true};
            OPTS.find(o => o.id === 'gS').vid = {name: true, date: true};
          }
          sizeAll();
        }""", [mode, args.scale])
        page.wait_for_timeout(500)

        rate = page.evaluate("()=>({h:HOURS_PER_S, d:DAYS_PER_S, y:YDAYS})")
        seconds = rate["y"] / rate["d"] if args.seconds <= 0 else args.seconds
        frames = max(1, int(round(seconds * args.fps)))
        turns = seconds * rate["h"] / 24
        ids = ["polar"] if kind == "polar" else ["gN", "gS"]
        size = page.evaluate("ids=>ids.map(i=>[$(i).width,$(i).height])", ids)
        print(f"  {job}: {rate['d']} days/s and {rate['h']} h/s -> {frames} frames "
              f"({frames/args.fps:.1f} s, {turns:.2f} turns), canvas {size}", flush=True)

        started = time.time()
        for k in range(frames):
            t = k / args.fps                     # real seconds into the clip
            page.evaluate("""([t, day0, polar]) => {
              day = (day0 + t*DAYS_PER_S) % YDAYS;
              hour = (12 + t*HOURS_PER_S) % 24;
              const dd = Math.floor(day), s = sun(dd);
              const c = {decl:s.decl, subLng:subLngAt(hour, s.eot), dd, hour,
                         eot:s.eot, dateTxt:dayLabel(dd),
                         timeTxt:timeLabel(hour)+' UTC'};
              for (const o of OPTS)
                if (polar ? o.kind === 'polar' : o.kind === 'globe') render(o, c);
            }""", [t, args.day0, kind == "polar"])
            if len(ids) == 1:
                grab(page, ids[0], args.quality).save(tmp / f"f{k:05d}.jpg",
                                                      quality=int(args.quality*100))
            else:
                top, bottom = (grab(page, i, args.quality) for i in ids)
                stacked = Image.new("RGB", (top.width, top.height + bottom.height))
                stacked.paste(top, (0, 0))
                stacked.paste(bottom, (0, top.height))
                stacked.save(tmp / f"f{k:05d}.jpg", quality=int(args.quality*100))
            if k % 300 == 0:
                print(f"    {job} {k}/{frames}  {time.time()-started:.0f}s", flush=True)
        browser.close()

    if errors:
        raise SystemExit(f"{job}: page errors: {errors}")
    print(f"  {job}: {frames} frames in {time.time()-started:.0f}s", flush=True)
    return frames


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", type=Path, default=Path("rings.html"))
    ap.add_argument("--outdir", type=Path, default=Path("dist"))
    ap.add_argument("--job", default="all", choices=("all", *JOBS),
                    help="which clip to record; default records all three")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920,
                    help="WxH; 1080x1920 is a phone feed")
    ap.add_argument("--scale", type=int, default=3, help="device pixel ratio")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="clip length; the default of 0 means one whole year, "
                         "which at the page's own rates is 91 seconds")
    ap.add_argument("--day0", type=float, default=350.0,
                    help="day of the year the clip opens on; 350 starts a few "
                         "days before the December solstice")
    ap.add_argument("--quality", type=float, default=0.93,
                    help="JPEG quality of the intermediate frames")
    ap.add_argument("--crf", type=int, default=20,
                    help="x264 quality; 20 is visually clean, and 24 "
                         "reproduces it at 40.8 dB luma PSNR for 40 percent "
                         "less file")
    ap.add_argument("--chrome", default=None)
    args = ap.parse_args()

    if not args.page.exists():
        raise SystemExit(f"missing {args.page}")
    ffmpeg = find_ffmpeg()
    jobs = list(JOBS) if args.job == "all" else [args.job]
    args.outdir.mkdir(parents=True, exist_ok=True)

    for job in jobs:
        tmp = Path(tempfile.mkdtemp(prefix=f"rings-{job}-"))
        try:
            frames = capture(job, args, tmp)
            out = args.outdir / JOBS[job][2]
            # H.264 High, yuv420p and faststart: what phone players and Reddit
            # will actually accept. Silent by design.
            subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                            "-framerate", str(args.fps), "-i", str(tmp / "f%05d.jpg"),
                            "-c:v", "libx264", "-preset", "slow",
                            "-crf", str(args.crf), "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-level", "4.1",
                            "-movflags", "+faststart", "-r", str(args.fps),
                            str(out)], check=True)
            mb = out.stat().st_size / 1e6
            print(f"wrote {out} ({mb:.1f} MB, {frames/args.fps:.1f} s)", flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # The loop does not close: the frame count divides neither the year nor the
    # turns exactly, so the last frame lands about two frames' worth of motion
    # from the first. Closing it means moving one of the page's two rates.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
