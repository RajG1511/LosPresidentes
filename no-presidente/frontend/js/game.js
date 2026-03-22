/**
 * game.js — Main game controller: API calls, state management, orchestration
 */

const Game = (() => {
  const TOTAL_MAIN_ENDINGS = 5;
  const LS_ENDINGS_KEY = "nopresidente_endings";

  let _moodsData = null;
  let _currentNode = null;
  let _currentPlayer = null;
  let _hudInitialized = false;

  // ── Boot ────────────────────────────────────────────────────────────────

  async function boot() {
    // 1. Load moods config
    try {
      const res = await fetch("/data/config/moods.json");
      _moodsData = await res.json();
      Visuals.init(_moodsData);
    } catch (e) {
      console.warn("Could not load moods.json", e);
      _moodsData = { moods: {} };
      Visuals.init(_moodsData);
    }

    // 2. Init audio
    AudioManager.init();

    // 3. Wire UI controls
    _wireControls();

    // 4. Restore settings from localStorage
    _applyStoredSettings();

    // 5. Start game session
    await startGame();
  }

  // ── Wire Controls ────────────────────────────────────────────────────────

  function _wireControls() {
    // Mute
    document.getElementById("btn-mute")?.addEventListener("click", () => {
      const muted = AudioManager.toggleMute();
      const btn = document.getElementById("btn-mute");
      if (btn) btn.style.opacity = muted ? "0.4" : "1";
    });

    // Restart
    document.getElementById("btn-restart")?.addEventListener("click", async () => {
      if (confirm("Restart the game? Your current run will be lost.")) {
        _hudInitialized = false;
        await startGame();
      }
    });

    // Settings open/close
    document.getElementById("btn-settings")?.addEventListener("click", () => {
      document.getElementById("settings-modal").style.display = "flex";
    });

    document.getElementById("btn-close-settings")?.addEventListener("click", () => {
      document.getElementById("settings-modal").style.display = "none";
    });

    // Close settings on backdrop click
    document.getElementById("settings-modal")?.addEventListener("click", (e) => {
      if (e.target === document.getElementById("settings-modal")) {
        document.getElementById("settings-modal").style.display = "none";
      }
    });

    // Text speed buttons
    document.querySelectorAll(".speed-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".speed-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        Terminal.setSpeed(parseInt(btn.dataset.speed, 10));
      });
    });

    // Volume slider
    document.getElementById("volume-slider")?.addEventListener("input", (e) => {
      AudioManager.setVolume(parseInt(e.target.value, 10) / 100);
    });

    // Scanlines toggle
    document.getElementById("toggle-scanlines")?.addEventListener("change", (e) => {
      document.getElementById("crt-scanlines").style.display = e.target.checked ? "" : "none";
      localStorage.setItem("nopresidente_scanlines", e.target.checked ? "1" : "0");
    });

    // Vignette toggle
    document.getElementById("toggle-vignette")?.addEventListener("change", (e) => {
      document.getElementById("crt-vignette").style.display = e.target.checked ? "" : "none";
      localStorage.setItem("nopresidente_vignette", e.target.checked ? "1" : "0");
    });

    // Play Again
    document.getElementById("btn-play-again")?.addEventListener("click", async () => {
      document.getElementById("ending-screen").style.display = "none";
      _hudInitialized = false;
      await startGame();
    });
  }

  function _applyStoredSettings() {
    // Text speed
    const storedSpeed = localStorage.getItem("nopresidente_textspeed");
    if (storedSpeed !== null) {
      const ms = parseInt(storedSpeed, 10);
      Terminal.setSpeed(ms);
      // Highlight the matching button
      document.querySelectorAll(".speed-btn").forEach(btn => {
        btn.classList.toggle("active", parseInt(btn.dataset.speed, 10) === ms);
      });
    }

    // Scanlines
    const scanlines = localStorage.getItem("nopresidente_scanlines");
    if (scanlines === "0") {
      document.getElementById("crt-scanlines").style.display = "none";
      const tog = document.getElementById("toggle-scanlines");
      if (tog) tog.checked = false;
    }

    // Vignette
    const vignette = localStorage.getItem("nopresidente_vignette");
    if (vignette === "0") {
      document.getElementById("crt-vignette").style.display = "none";
      const tog = document.getElementById("toggle-vignette");
      if (tog) tog.checked = false;
    }
  }

  // ── Start Game ──────────────────────────────────────────────────────────

  async function startGame() {
    Terminal.clearTerminal();
    try {
      const res = await fetch("/api/start", { method: "POST" });
      if (!res.ok) throw new Error(`Start failed: ${res.status}`);
      const data = await res.json();
      _currentNode = data.node;
      _currentPlayer = data.player;
      _hudInitialized = false;
      await renderNode(data.node, data.player, [], null);
    } catch (e) {
      console.error("Failed to start game:", e);
      Terminal.clearTerminal();
      await Terminal.typeText(
        Terminal.outputEl,
        "ERROR: Could not connect to game server.\nMake sure Flask is running: python app.py"
      );
    }
  }

  // ── Render Node ─────────────────────────────────────────────────────────

  async function renderNode(node, player, changes, rngResult) {
    Terminal.clearTerminal();

    // Apply mood
    if (node.mood) {
      Visuals.setMood(node.mood);
      AudioManager.playMoodTrack(node.mood);
    }

    // Sprite
    Visuals.setSprite(node.sprite || null);

    // Node type tag
    Terminal.setNodeTag(node.type, node.mood);

    // Init or update HUD
    if (player) {
      if (!_hudInitialized) {
        HUD.initHUD(player.attributes);
        _hudInitialized = true;
      } else {
        HUD.updateHUD(player.attributes, changes);
      }
    }

    // Show RNG result first
    if (rngResult) {
      Terminal.showRngResult(rngResult);
      await new Promise(r => setTimeout(r, 500));
    }

    // Show attribute changes
    if (changes && changes.length > 0) {
      await Terminal.showAttributeChanges(changes);
      await new Promise(r => setTimeout(r, 250));
    }

    // Morale death flash
    if (player && player.attributes.morale === 0) {
      HUD.flashMoraleDeath();
      await new Promise(r => setTimeout(r, 400));
    }

    // Type node text
    await Terminal.typeText(Terminal.outputEl, node.text);

    // Ending?
    if (node.type === "ending") {
      await new Promise(r => setTimeout(r, 800));
      await showEndingScreen(node, player);
      return;
    }

    // Show choices
    if (node.choices && node.choices.length > 0) {
      Terminal.displayChoices(node.choices, handleChoice);
    } else {
      Terminal.appendText(Terminal.outputEl, "\n\n> [No options available]");
    }
  }

  // ── Handle Choice ────────────────────────────────────────────────────────

  async function handleChoice(choiceIndex) {
    Terminal.disableChoices();
    AudioManager.playSFX("choice_select");

    try {
      const res = await fetch("/api/choose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ choice_index: choiceIndex }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("Choose error:", err);
        return;
      }

      const data = await res.json();
      const { node, player, changes, rng_result } = data;

      _currentNode = node;
      _currentPlayer = player;

      // SFX for attribute changes
      if (changes) {
        const hasMoraleDown = changes.some(c => c.attribute === "morale" && c.delta < 0);
        const hasDown = changes.some(c => c.delta < 0);
        const hasUp = changes.some(c => c.delta > 0);
        if (hasMoraleDown && player?.attributes?.morale <= 2) AudioManager.playSFX("morale_warning");
        else if (hasDown) AudioManager.playSFX("attribute_down");
        else if (hasUp) AudioManager.playSFX("attribute_up");
      }

      await new Promise(r => setTimeout(r, 400));
      await renderNode(node, player, changes, rng_result);

    } catch (e) {
      console.error("Network error on choose:", e);
    }
  }

  // ── Ending Screen ────────────────────────────────────────────────────────

  async function showEndingScreen(node, player) {
    AudioManager.playSFX("ending_fanfare");

    // Save to localStorage
    const discovered = _getDiscoveredEndingsLocal();
    if (node.ending_id && !discovered.includes(node.ending_id)) {
      discovered.push(node.ending_id);
      localStorage.setItem(LS_ENDINGS_KEY, JSON.stringify(discovered));
    }

    // Fetch all endings metadata
    let allEndingsData = { all_endings: {}, discovered: [] };
    try {
      const res = await fetch("/api/endings");
      if (res.ok) allEndingsData = await res.json();
    } catch { /* silently fail */ }

    const allDiscovered = Array.from(new Set([...discovered, ...(allEndingsData.discovered || [])]));
    const mainCount = allDiscovered.filter(e => e !== "morale_death").length;
    const allEndings = allEndingsData.all_endings || {};

    // Type ending text in the ending screen
    const endingTextEl = document.getElementById("ending-text");
    if (endingTextEl) {
      endingTextEl.textContent = "";
      // Use instant speed in ending screen so it feels punchy
      const speedOverride = Terminal.getSpeed() === 0 ? 0 : Math.min(Terminal.getSpeed(), 20);
      await Terminal.typeText(endingTextEl, node.text, speedOverride);
    }

    // Build tracker
    const trackerEl = document.getElementById("endings-tracker");
    if (trackerEl) {
      const mainEndingIds = ["ending_1", "ending_2", "ending_3", "ending_4", "ending_5"];
      let html = `<div class="tracker-title">ENDINGS: ${mainCount} / ${TOTAL_MAIN_ENDINGS}</div>`;
      mainEndingIds.forEach(eid => {
        if (allDiscovered.includes(eid)) {
          const title = allEndings[eid]?.title || eid;
          html += `<div class="discovered-item">> ${title}</div>`;
        } else {
          const hint = allEndings[eid]?.hint || "???";
          html += `<div class="hint-item">? ${hint}</div>`;
        }
      });
      trackerEl.innerHTML = html;
    }

    document.getElementById("ending-screen").style.display = "flex";
  }

  function _getDiscoveredEndingsLocal() {
    try {
      return JSON.parse(localStorage.getItem(LS_ENDINGS_KEY) || "[]");
    } catch {
      return [];
    }
  }

  return { boot };
})();

document.addEventListener("DOMContentLoaded", () => Game.boot());
