# 3D diagrams with Blender (headless)

Use Blender only when depth or movement in 3D genuinely explains the idea - for example data flowing through stacked layers, or an object rotating to show its parts. For boxes-and-arrows diagrams, flat HyperFrames graphics are faster, sharper and easier to change.

## Pattern
1. Write a Python script that builds the scene with Blender's `bpy` API: simple shapes, the user's brand colours, labels as text objects, camera, light, a short animation (2-6 s).
2. Render headlessly, without opening Blender:
   ```
   blender -b -P 03_assets/diagram_scene.py -- --out 03_assets/diagram_ --frames 1-150
   ```
   Inside the script, read the arguments after `--`, set `scene.render.resolution_x/y` to the output size, `scene.render.fps` to the project fps, the engine to Eevee for speed, and output to a PNG sequence or FFmpeg video.
3. Turn a PNG sequence into a clip: `ffmpeg -framerate 30 -i 03_assets/diagram_%04d.png -c:v libx264 -pix_fmt yuv420p 03_assets/diagram.mp4` (for an overlay, keep transparency with `-c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le diagram.mov`).
4. Render a single still frame first (`--frames 75-75`) and show it to the user before rendering the whole animation. Full renders can take minutes.

## Keep it simple
- Few objects, flat or lightly shaded materials, slow camera move.
- Text must be large: at least 5% of frame height.
- Save the scene script in `03_assets/` so a change of label or colour is a one-line edit and a re-render.
