# Titles, lower thirds and callouts with HyperFrames

HyperFrames (open source, from HeyGen) turns HTML, CSS and seekable animations (GSAP) into video. It suits titles, lower thirds, chapter cards, step counters, code highlights and simple animated diagrams. Requirements: Node.js 22+ and FFmpeg.

## Two ways to use it
- **Local CLI (default here).** Files stay on the user's computer and can be edited and versioned.
  ```
  cd 03_assets
  npx hyperframes init lower-third
  # edit the composition HTML: text, brand colours, timing
  npx hyperframes preview      # browser preview, live reload
  npx hyperframes render --output lower_third.mp4
  ```
  If the HyperFrames agent skills are installed (`npx skills add heygen-com/hyperframes`), load the `/hyperframes` skill and follow it for authoring rules; it knows the composition format better than this note. Run `npx hyperframes --help` and `npx hyperframes render --help` to see the current options - the CLI changes often.
- **Hosted connector (HyperFrames by HeyGen).** Creates a HeyGen project from a description and renders in the cloud. Use when the user wants a shareable HeyGen project, or has no Node.js. Download the render into `03_assets/`.

## Transparency
Overlays need a transparent background, or they hide the video. Check `npx hyperframes render --help` for a transparent / alpha output (WebM VP9 or MOV ProRes 4444). If there is none:
- render the graphic on pure green (#00FF00) and key it out in FFmpeg before assembly:
  `ffmpeg -i lt_green.mp4 -vf "chromakey=0x00FF00:0.15:0.05,format=yuva420p" -c:v libvpx-vp9 -pix_fmt yuva420p lower_third.webm`
- or use the graphic as a full-frame cutaway (title or chapter card), which needs no transparency.
Still graphics (PNG with transparency) also work as overlays and are the simplest option.

## Picking a look from the catalog
The catalog at https://hyperframes.heygen.com/catalog shows ready-made compositions and effects. SKILL.md step 7 has the user pick from it. For each one they pick, open its catalog page and start from the code or install line it gives. Then swap in the user's text, brand colours and timing. Note their favourites in `edit_rules.md` (with their agreement) so later videos keep the same look.

## Design defaults
- Use the user's brand design system if one exists (colours, fonts, logo). Ask once, then record it in `edit_rules.md`.
- Lower third: name and role, left-aligned, bottom-left safe area (about 5% in from edges), on screen 4-5 s, animate in and out in about 0.3 s.
- Chapter card: 2-3 s full-frame, or a 4 s lower-third title at the start of each section.
- Code callout: a box or highlight over the exact lines, timed to when they are mentioned; keep text at least 32 px tall at 1080p.
- Keep graphics clear of the caption area (bottom 15% when captions are burned in).

## Check before assembly
Grab one frame of each graphic (`ffmpeg -ss 1 -i asset -frames:v 1 check.png`) and look at it: text spelled right, brand colours right, transparent where it should be.
