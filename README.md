# COSMOS — cinematic 60-second short

The renderer now builds six distinct illustrated compositions rather than reusing a few generic gradients: a luminous nebula, a detailed ringed planet, an asteroid field with a spacecraft, a cratered lunar horizon, an Earthrise, and a spiral galaxy.

- 60 seconds · 1920×1080 · 24 fps · 16:9
- Camera push-ins, crossfades, scene captions and an original synthesized ambient score
- Output: `dist/cosmos-60s.mp4` (H.264 + AAC)

## Render locally
Python 3.11+, FFmpeg, Pillow and NumPy are required.

    python -m pip install -r requirements.txt
    python render.py

## GitHub Actions
A push to `main` or a manual run of **Actions → Render COSMOS film** renders the video. The `cosmos-60s-video` artifact is retained for 14 days.

The scenes are original procedural illustrations, not live-action footage or scientific imagery.
