# A–B Loop — Section Repeat for YouTube & YT Music

Mark a **start** and **end** point on any YouTube / YouTube Music track and loop
that section automatically. No accounts, no network calls, nothing leaves your
browser.

## Install (load unpacked)

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top-right).
3. Click **Load unpacked** and select this `ab-loop/` folder.
4. Pin the extension from the puzzle-piece menu if you want it always visible.

## Use

1. Open a video on `youtube.com` or a track on `music.youtube.com`.
2. Click the **A–B Loop** toolbar icon → a small floating widget appears.
3. While playing, click **Set** next to *Start* at the moment you want the loop
   to begin, then **Set** next to *End* where it should jump back.
4. Click **Loop: OFF** to flip it **ON**. Playback now repeats that section.
5. **Clear** resets the points; the **×** hides the widget (click the toolbar
   icon again to bring it back).

Drag the widget by its title bar to move it.

## Notes & limits

- **Session-only:** the loop clears on page reload or when the track changes.
- **YouTube ads:** looping pauses during ads and resumes on the real content.
- **Precision:** loops are tight in the foreground; in a background tab they
  still work but the jump-back may be slightly less precise (browsers throttle
  background timers).
- **Spotify is not supported** in this version — its DRM-protected web player
  can't be controlled this way (it would need Spotify's Web Playback SDK +
  Premium + OAuth). Planned as a future phase.

## Files

| File | Purpose |
| --- | --- |
| `manifest.json` | Manifest V3 config |
| `content.js` | Widget UI + loop logic (injected into pages) |
| `widget.css` | Floating widget styles |
| `background.js` | Toolbar-icon click → toggle widget |
| `icons/` | Toolbar / store icons |
