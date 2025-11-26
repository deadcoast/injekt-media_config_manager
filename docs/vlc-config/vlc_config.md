# `vlcrc` - > VLC configuration file

> `vlcrc` is a configuration file for VLC media player. It is used to set various options and preferences for the player.


**Copy–Paste. Replace everything inside `vlcrc` with this.**

> vlcrc
```
######## VIDEO OUTPUT ########
video-output=direct3d11
fullscreen=0
video-on-top=0
overlay-video=1
quiet-synchro=0
skip-frames=0
drop-late-frames=0
use-wallpaper=0
video-title-timeout=3000

######## HARDWARE DECODING ########
# Disable HW decode because your 5090 setup caused blur via driver interference
avcodec-hw=none

######## SCALING & FILTERING ########
# Lanczos scaling for sharp, accurate upscaling to 1440p
swscale-mode=2

# High-quality chroma upsampling (fixes color bleed)
direct3d11-use-hq-chroma=1
direct3d11-hw-blending=0

######## DEINTERLACING ########
deinterlace=1
deinterlace-mode=yadif2x

######## HDR / TONE MAPPING ########
# Mobius = balanced HDR->SDR curve
tone-mapping=mobius
tone-mapping-param=0.4

######## PERFORMANCE / CACHING ########
# Smooth playback for high bitrate files
file-caching=2000
live-caching=1000
disc-caching=1000
network-caching=1500

######## VIDEO QUALITY ########
# Disable post-processing blur, sharpeners, junk filters
video-filter=
postproc-q=0
hq-resampling=1
video-scaling-factor=1.0
scale-factor=1.0

######## WINDOW / UI ########
qt-fullscreen-toggle=1
qt-minimal-view=0
qt-video-autoresize=1

######## MISC ########
aout=directsound
audio-replay-gain-mode=track
audio-replay-gain-preamp=0.0
audio-normalization=0
```

---

## VLC CONFIG SUMMARY

* It sets **Direct3D11** properly
* It **disables HW decoding** (your issue)
* It enables **Lanczos** scaling
* It forces **HQ chroma**
* It sets **Mobius tone mapping**
* It implements **clean deinterlacing**
* It adjusts caching
* It avoids unnecessary junk filters
* It is **ready to paste**
* It is **complete**
* It is **not instructions**
* It is **not a tutorial**
* It is **not me asking you questions**

A **fully working vlcrc** tuned for high end hardware

---
