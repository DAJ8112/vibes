// A–B Loop — content script.
// Injected into YouTube and YouTube Music. Builds a draggable floating widget,
// captures start/end timestamps from the live playhead, and keeps playback
// inside [start, end] while looping is on. Session-only: no persistence.

(() => {
  "use strict";

  // Guard against double injection (SPA re-injection / dev reloads).
  if (window.__abLoopInjected) return;
  window.__abLoopInjected = true;

  const EPSILON = 0.3; // seconds of slack before yanking back to start

  const state = {
    start: null, // seconds, or null
    end: null, // seconds, or null
    looping: false,
    video: null, // current media element
  };

  let widget = null;
  let els = {}; // cached references to widget sub-elements

  // ---- media element ---------------------------------------------------------

  // YouTube's main player video carries .html5-main-video / .video-stream.
  // YT Music has a single <video>. Hover-preview thumbnails can add extra
  // <video> nodes, so prefer the known player classes.
  function getVideo() {
    return (
      document.querySelector("video.html5-main-video") ||
      document.querySelector("video.video-stream") ||
      document.querySelector("video")
    );
  }

  // YouTube ads reuse the same <video>; the player gets an .ad-showing class.
  // Don't fight the ad — only enforce our loop on the real content.
  function isAdPlaying() {
    return !!document.querySelector(
      ".ad-showing, .ytp-ad-player-overlay, .ad-interrupting"
    );
  }

  function bindVideo() {
    const v = getVideo();
    if (v && v !== state.video) {
      if (state.video) state.video.removeEventListener("timeupdate", enforceLoop);
      state.video = v;
      // timeupdate keeps the loop working in background tabs (where rAF is
      // throttled/paused); the rAF loop adds tight precision in the foreground.
      v.addEventListener("timeupdate", enforceLoop);
    }
    return state.video;
  }

  // ---- loop enforcement ------------------------------------------------------

  function enforceLoop() {
    if (!state.looping || state.start == null || state.end == null) return;
    const v = state.video;
    if (!v || isAdPlaying()) return;
    if (v.currentTime >= state.end || v.currentTime < state.start - EPSILON) {
      v.currentTime = state.start;
    }
  }

  function rafTick() {
    enforceLoop();
    requestAnimationFrame(rafTick);
  }

  // ---- formatting ------------------------------------------------------------

  function fmt(t) {
    if (t == null || isNaN(t)) return "––:––";
    t = Math.max(0, Math.floor(t));
    const h = Math.floor(t / 3600);
    const m = Math.floor((t % 3600) / 60);
    const s = t % 60;
    const mm = h > 0 ? String(m).padStart(2, "0") : String(m);
    const ss = String(s).padStart(2, "0");
    return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
  }

  // Parse user-typed time. Accepts "mm:ss", "h:mm:ss", or bare seconds
  // ("32", "15.5"). Returns null for empty (= clear), NaN for unparseable.
  function parseTime(str) {
    const s = String(str).trim();
    if (s === "") return null;
    const parts = s.split(":");
    if (parts.length > 3) return NaN;
    const nums = parts.map((p) => (p.trim() === "" ? NaN : Number(p)));
    if (nums.some((n) => isNaN(n) || n < 0)) return NaN;
    // For colon-separated input, lower fields must be < 60.
    if (parts.length > 1 && nums.slice(1).some((n) => n >= 60)) return NaN;
    let secs = 0;
    for (const n of nums) secs = secs * 60 + n;
    return secs;
  }

  // ---- widget ----------------------------------------------------------------

  function buildWidget() {
    widget = document.createElement("div");
    widget.id = "abloop-widget";
    widget.className = "abloop-hidden";
    widget.innerHTML = `
      <div class="abloop-header">
        <span class="abloop-title">A–B Loop</span>
        <button class="abloop-close" title="Hide">×</button>
      </div>
      <div class="abloop-body">
        <div class="abloop-row">
          <span class="abloop-label">Start</span>
          <span class="abloop-time" data-role="start-time" title="Click to type a time">––:––</span>
          <input class="abloop-time-input" data-role="start-input" type="text" inputmode="numeric" autocomplete="off" spellcheck="false" hidden />
          <button class="abloop-btn" data-role="set-start">Set</button>
        </div>
        <div class="abloop-row">
          <span class="abloop-label">End</span>
          <span class="abloop-time" data-role="end-time" title="Click to type a time">––:––</span>
          <input class="abloop-time-input" data-role="end-input" type="text" inputmode="numeric" autocomplete="off" spellcheck="false" hidden />
          <button class="abloop-btn" data-role="set-end">Set</button>
        </div>
        <div class="abloop-row abloop-controls">
          <button class="abloop-toggle" data-role="toggle">Loop: OFF</button>
          <button class="abloop-btn abloop-clear" data-role="clear">Clear</button>
        </div>
        <div class="abloop-status" data-role="status">Set Start &amp; End while playing.</div>
      </div>
    `;
    document.body.appendChild(widget);

    const q = (role) => widget.querySelector(`[data-role="${role}"]`);
    els = {
      startTime: q("start-time"),
      endTime: q("end-time"),
      startInput: q("start-input"),
      endInput: q("end-input"),
      setStart: q("set-start"),
      setEnd: q("set-end"),
      toggle: q("toggle"),
      clear: q("clear"),
      status: q("status"),
      close: widget.querySelector(".abloop-close"),
      header: widget.querySelector(".abloop-header"),
    };

    els.setStart.addEventListener("click", onSetStart);
    els.setEnd.addEventListener("click", onSetEnd);
    els.toggle.addEventListener("click", onToggle);
    els.clear.addEventListener("click", onClear);
    els.close.addEventListener("click", hideWidget);
    wireEditable("start");
    wireEditable("end");
    makeDraggable(widget, els.header);

    requestAnimationFrame(rafTick);
  }

  function setStatus(msg, kind) {
    if (!els.status) return;
    els.status.textContent = msg;
    els.status.className = "abloop-status" + (kind ? ` abloop-${kind}` : "");
  }

  function refreshUI() {
    els.startTime.textContent = fmt(state.start);
    els.endTime.textContent = fmt(state.end);
    els.toggle.textContent = state.looping ? "Loop: ON" : "Loop: OFF";
    els.toggle.classList.toggle("abloop-on", state.looping);
    if (state.looping && state.start != null && state.end != null) {
      setStatus(`Looping ${fmt(state.start)} → ${fmt(state.end)}`, "active");
    }
  }

  // ---- actions ---------------------------------------------------------------

  function onSetStart() {
    const v = bindVideo();
    if (!v) return setStatus("No video found on this page.", "warn");
    state.start = v.currentTime;
    if (state.end != null && state.end <= state.start) {
      state.end = null; // end is no longer valid relative to new start
    }
    setStatus(`Start set to ${fmt(state.start)}.`);
    refreshUI();
  }

  function onSetEnd() {
    const v = bindVideo();
    if (!v) return setStatus("No video found on this page.", "warn");
    const t = v.currentTime;
    if (state.start != null && t <= state.start) {
      return setStatus("End must come after Start.", "warn");
    }
    state.end = t;
    setStatus(`End set to ${fmt(state.end)}.`);
    refreshUI();
  }

  // Click-to-type editing for a time field ("start" | "end").
  function wireEditable(which) {
    const span = which === "start" ? els.startTime : els.endTime;
    const input = which === "start" ? els.startInput : els.endInput;
    let editing = false;

    function begin() {
      if (editing) return;
      editing = true;
      const cur = which === "start" ? state.start : state.end;
      input.value = cur != null ? fmt(cur) : "";
      span.hidden = true;
      input.hidden = false;
      input.focus();
      input.select();
    }

    function finish(commit) {
      if (!editing) return;
      editing = false;
      const warn = commit ? applyEdit(which, input.value) : null;
      input.hidden = true;
      span.hidden = false;
      refreshUI();
      if (warn) setStatus(warn, "warn");
    }

    span.addEventListener("click", begin);
    input.addEventListener("blur", () => finish(true));
    input.addEventListener("keydown", (e) => {
      // Keep typing from triggering YouTube's single-key shortcuts.
      e.stopPropagation();
      if (e.key === "Enter") {
        e.preventDefault();
        finish(true);
      } else if (e.key === "Escape") {
        e.preventDefault();
        finish(false);
      }
    });
  }

  // Apply a typed value to start/end. Returns a warning string to surface, or
  // null on success/clear (status is set here for those cases).
  function applyEdit(which, raw) {
    const secs = parseTime(raw);
    if (Number.isNaN(secs)) return "Couldn't read that time.";

    if (secs === null) {
      if (which === "start") state.start = null;
      else state.end = null;
      if (state.start == null || state.end == null) state.looping = false;
      setStatus(`${which === "start" ? "Start" : "End"} cleared.`);
      return null;
    }

    let t = Math.max(0, secs);
    const dur =
      state.video && isFinite(state.video.duration) ? state.video.duration : null;
    if (dur != null) t = Math.min(t, dur);

    if (which === "start") {
      if (state.end != null && t >= state.end) return "Start must come before End.";
      state.start = t;
      setStatus(`Start set to ${fmt(t)}.`);
    } else {
      if (state.start != null && t <= state.start) return "End must come after Start.";
      state.end = t;
      setStatus(`End set to ${fmt(t)}.`);
    }
    if (state.looping) enforceLoop();
    return null;
  }

  function onToggle() {
    if (!state.looping) {
      if (state.start == null || state.end == null) {
        return setStatus("Set both Start and End first.", "warn");
      }
      if (state.end <= state.start) {
        return setStatus("End must come after Start.", "warn");
      }
      state.looping = true;
      bindVideo();
      enforceLoop();
    } else {
      state.looping = false;
      setStatus("Loop off.");
    }
    refreshUI();
  }

  function onClear() {
    state.start = null;
    state.end = null;
    state.looping = false;
    setStatus("Cleared.");
    refreshUI();
  }

  // Reset loop on track change (session-only). The <video> persists across
  // SPA navigations, so we clear state and re-sync the UI.
  function onTrackChange() {
    state.start = null;
    state.end = null;
    state.looping = false;
    bindVideo();
    if (widget) {
      setStatus("New track — loop cleared.");
      refreshUI();
    }
  }

  // ---- visibility ------------------------------------------------------------

  function showWidget() {
    if (!widget) buildWidget();
    bindVideo();
    widget.classList.remove("abloop-hidden");
    refreshUI();
  }

  function hideWidget() {
    if (widget) widget.classList.add("abloop-hidden");
  }

  function toggleWidget() {
    if (!widget || widget.classList.contains("abloop-hidden")) showWidget();
    else hideWidget();
  }

  // ---- drag ------------------------------------------------------------------

  function makeDraggable(panel, handle) {
    let dragging = false;
    let offX = 0;
    let offY = 0;

    handle.addEventListener("mousedown", (e) => {
      if (e.target.closest(".abloop-close")) return;
      dragging = true;
      const rect = panel.getBoundingClientRect();
      offX = e.clientX - rect.left;
      offY = e.clientY - rect.top;
      // Switch from right-anchored to left/top so dragging works smoothly.
      panel.style.right = "auto";
      panel.style.left = `${rect.left}px`;
      panel.style.top = `${rect.top}px`;
      e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const x = Math.max(0, Math.min(window.innerWidth - panel.offsetWidth, e.clientX - offX));
      const y = Math.max(0, Math.min(window.innerHeight - panel.offsetHeight, e.clientY - offY));
      panel.style.left = `${x}px`;
      panel.style.top = `${y}px`;
    });

    document.addEventListener("mouseup", () => {
      dragging = false;
    });
  }

  // ---- wiring ----------------------------------------------------------------

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === "TOGGLE_WIDGET") toggleWidget();
  });

  // YouTube + YT Music fire this on SPA navigation between videos/tracks.
  window.addEventListener("yt-navigate-finish", onTrackChange);
  // Fallback: a fresh media source loading also signals a track change.
  document.addEventListener(
    "loadeddata",
    (e) => {
      if (e.target instanceof HTMLMediaElement) onTrackChange();
    },
    true
  );

  bindVideo();
})();
