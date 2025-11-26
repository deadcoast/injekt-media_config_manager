Yes. Your base configs are good to go. Now we’re just bolting the **MPV MVP plugin pack** on top.

I’ll give you:

* Exactly *which* plugins
* Exactly *where* to download them
* Exactly *where* to drop the files on your machine

No guessing, no “maybe”, no extra questions.

---

## 0. Paths (for you specifically)

We’ll use these:

```text
MPV config root:
C:\Users\ryanf\AppData\Roaming\mpv\

Scripts:
C:\Users\ryanf\AppData\Roaming\mpv\scripts\

Script options (config for scripts):
C:\Users\ryanf\AppData\Roaming\mpv\script-opts\
```

If `scripts` and `script-opts` don’t exist, just create them.

Your existing `rtx-vsr-toggle.lua` can stay in `scripts\` — it won’t conflict.

---

## PACK CONTENTS

Here’s the pack we’re installing:

1. **uosc** – modern, full-featured UI for MPV ([GitHub][1])
2. **thumbfast** – YouTube-style thumbnails when you scrub ([GitHub][2])
3. **autoload.lua** – auto-loads all files in the folder into the playlist ([thewiki.moe][3])
4. **mpv_sponsorblock** – auto-skip YouTube sponsors in MPV ([GitHub][4])
5. **simple-mpv-webui** – control MPV from browser/phone on your LAN ([GitHub][5])

That’s your “MVP” plugin set: UI, thumbnails, folder playlists, ad-skip, web remote.

---

## 1️⃣ Install uosc (modern UI)

**Source:** uosc on GitHub ([GitHub][1])

1. Go to:
   **`https://github.com/tomasklaen/uosc`**
2. Click **Code → Download ZIP**.
3. Extract the ZIP somewhere temporary.
4. From the extracted folder, copy:

   * `uosc.lua` →
     `C:\Users\ryanf\AppData\Roaming\mpv\scripts\uosc.lua`

   * The default config file (if present) `uosc.conf` or the `script-opts` version from the repo →
     `C:\Users\ryanf\AppData\Roaming\mpv\script-opts\uosc.conf`

That’s it. Next time you open MPV, you’ll get a proper modern UI (seekbar, menus, etc.).

---

## 2️⃣ Install thumbfast (thumbnails on seek)

**Source:** thumbfast (po5) ([GitHub][2])

1. Download the script directly:
   `thumbfast.lua` from:
   **`https://raw.githubusercontent.com/po5/thumbfast/f1fdf10b17f394f2d42520d0e9bf22feaa20a9f4/thumbfast.lua`**

2. Save it as:

```text
C:\Users\ryanf\AppData\Roaming\mpv\scripts\thumbfast.lua
```

3. If the repo / docs provide a `thumbfast.conf` (or you grab it later), put it here:

```text
C:\Users\ryanf\AppData\Roaming\mpv\script-opts\thumbfast.conf
```

**Note:** thumbfast doesn’t draw UI by itself — it hooks into UIs like uosc. They’re designed to work together. ([thewiki.moe][3])

---

## 3️⃣ Install `autoload.lua` (automatic folder playlist)

**Source:** Official MPV tools repo (autoload.lua) ([thewiki.moe][3])

1. Open the raw script:
   **`https://raw.githubusercontent.com/mpv-player/mpv/master/TOOLS/lua/autoload.lua`**
2. Save as:

```text
C:\Users\ryanf\AppData\Roaming\mpv\scripts\autoload.lua
```

What it does:

* When you open one file in a folder, it automatically loads all the other files in that folder into the playlist in order.
* This is the “play next in folder” behavior lots of players have.

Nothing else needed; MPV auto-runs any `.lua` in `scripts\`.

---

## 4️⃣ Install mpv_sponsorblock (skip sponsors)

**Source:** po5/mpv_sponsorblock ([GitHub][4])

1. Go to:
   **`https://github.com/po5/mpv_sponsorblock`**
2. Download as ZIP.
3. Extract.

From the repo, copy:

* `sponsorblock.lua`
* The folder `sponsorblock_shared` (contains `main.lua` and `sponsorblock.py`)

Into:

```text
C:\Users\ryanf\AppData\Roaming\mpv\scripts\sponsorblock.lua
C:\Users\ryanf\AppData\Roaming\mpv\scripts\sponsorblock_shared\ (whole folder)
```

Requirements:

* Needs **Python 3** installed on your system (you most likely already have it; if not, install from python.org). ([GitHub][4])

Once that’s in place, when you play YouTube via MPV (through `yt-dlp` or similar), sponsor segments are auto-skipped.

---

## 5️⃣ Install simple-mpv-webui (web/phone remote)

**Source:** open-dynaMIX/simple-mpv-webui ([GitHub][5])

1. Go to:
   **`https://github.com/open-dynaMIX/simple-mpv-webui`**
2. Download ZIP.
3. Extract it.
4. Copy the **entire folder** into your scripts directory, e.g.:

```text
C:\Users\ryanf\AppData\Roaming\mpv\scripts\simple-mpv-webui\
```

(Or just drop the contents directly into `scripts\` if the readme says so — MPV will detect it automatically for v0.33+.) ([GitHub][5])

Then:

* Start MPV
* Open browser on your PC/phone: `http://localhost:8080` (or whatever port the readme specifies)
* You get playback controls in the browser

---

## 6️⃣ Quick sanity check

Once all that’s in place, launch MPV and verify:

* **Modern UI** (uosc) appears instead of the barebones bar
* Scrubbing the seekbar shows **thumbnail previews** (thumbfast + uosc)
* Opening one file from a folder -> playlist auto-populates with all files (autoload.lua)
* YouTube videos: sponsor segments skip automatically (mpv_sponsorblock)
* Going to the WebUI URL shows remote controls (simple-mpv-webui)

If all of that works, your **MPV MVP pack** is live and doing work.

---

If you want, next step can be:

* One **“anime/low-res” profile** that auto-enables FSR2 when resolution < 1080p
* One **“default/movie” profile**
  that we wire straight into `mpv.conf` so it reacts automatically to the source resolution, no keybinds needed.

[1]: https://github.com/tomasklaen/uosc?utm_source=chatgpt.com "tomasklaen/uosc: Feature-rich minimalist proximity-based ..."
[2]: https://github.com/po5/thumbfast?utm_source=chatgpt.com "po5/thumbfast: High-performance on-the-fly thumbnailer ..."
[3]: https://thewiki.moe/tutorials/mpv/?utm_source=chatgpt.com "mpv"
[4]: https://github.com/po5/mpv_sponsorblock?utm_source=chatgpt.com "po5/mpv_sponsorblock: mpv script to skip sponsored ..."
[5]: https://github.com/open-dynaMIX/simple-mpv-webui?utm_source=chatgpt.com "open-dynaMIX/simple-mpv-webui: A web based ..."
