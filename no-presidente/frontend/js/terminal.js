/**
 * terminal.js — Text rendering engine: typewriter effect, choice display, result display
 */

const Terminal = (() => {
  const LS_SPEED_KEY = "nopresidente_textspeed";

  // Speed in ms-per-character. 0 = instant.
  let _speed = parseInt(localStorage.getItem(LS_SPEED_KEY) ?? "28", 10);

  let _skipFlag = false;
  let _typingActive = false;

  // Register skip listeners once
  function _setupSkip() {
    const skipHandler = () => { if (_typingActive) _skipFlag = true; };
    document.addEventListener("keydown", skipHandler);
    // Only skip on terminal panel clicks, not choice button clicks
    document.getElementById("terminal-panel")?.addEventListener("click", skipHandler);
  }
  // Call after DOM ready
  document.addEventListener("DOMContentLoaded", _setupSkip);

  /**
   * setSpeed(ms) — set typewriter speed in ms per character
   */
  function setSpeed(ms) {
    _speed = Math.max(0, ms);
    localStorage.setItem(LS_SPEED_KEY, String(_speed));
  }

  function getSpeed() { return _speed; }

  /**
   * typeText(element, text, speedOverride?) → Promise
   * Types text character by character. Keypress/click skips to full text.
   */
  async function typeText(element, text, speedOverride) {
    const ms = speedOverride !== undefined ? speedOverride : _speed;

    if (ms === 0) {
      element.textContent = text;
      _scrollTerminal();
      return;
    }

    _typingActive = true;
    _skipFlag = false;
    element.textContent = "";

    for (let i = 0; i < text.length; i++) {
      if (_skipFlag) {
        element.textContent = text;
        break;
      }
      element.textContent += text[i];
      _scrollTerminal();
      await new Promise(resolve => setTimeout(resolve, ms));
    }

    _typingActive = false;
    _skipFlag = false;
    _scrollTerminal();
  }

  function _scrollTerminal() {
    const panel = document.getElementById("terminal-panel");
    if (panel) panel.scrollTop = panel.scrollHeight;
  }

  /**
   * displayChoices(choices, onSelect)
   * Renders choices as terminal-style clickable blocks.
   */
  function displayChoices(choices, onSelect) {
    const container = document.getElementById("choices-container");
    if (!container) return;
    container.innerHTML = "";

    choices.forEach((choice, i) => {
      const btn = document.createElement("button");
      btn.className = "choice-btn";
      btn.setAttribute("data-index", i);

      const prefix = document.createElement("span");
      prefix.className = "choice-prefix";
      prefix.textContent = `> [${i + 1}]`;

      const label = document.createElement("span");
      label.textContent = choice.label;

      btn.appendChild(prefix);
      btn.appendChild(label);

      if (choice.has_rng) {
        const rngTag = document.createElement("span");
        rngTag.className = "choice-rng-tag";
        rngTag.textContent = `[ROLL: ${choice.weight_attribute.toUpperCase()}]`;
        btn.appendChild(rngTag);
      }

      btn.addEventListener("click", (e) => {
        e.stopPropagation(); // don't trigger terminal skip
        onSelect(i);
      });
      container.appendChild(btn);
    });

    _registerChoiceKeys(choices, onSelect);
  }

  let _keyHandler = null;
  function _registerChoiceKeys(choices, onSelect) {
    if (_keyHandler) document.removeEventListener("keydown", _keyHandler);
    _keyHandler = (e) => {
      // Only fire if settings modal is closed
      if (document.getElementById("settings-modal")?.style.display !== "none") return;
      const num = parseInt(e.key, 10);
      if (!isNaN(num) && num >= 1 && num <= choices.length) {
        onSelect(num - 1);
      }
    };
    document.addEventListener("keydown", _keyHandler);
  }

  function clearChoiceKeys() {
    if (_keyHandler) {
      document.removeEventListener("keydown", _keyHandler);
      _keyHandler = null;
    }
  }

  /**
   * setNodeTag(type, mood) — show the node type tag above the text
   */
  function setNodeTag(type, mood) {
    const el = document.getElementById("node-tag");
    if (!el) return;
    const labels = {
      event: "// EVENT",
      pathway: "// DECISION",
      attribute: "// ATTRIBUTE CHECK",
      checkpoint: "// CHECKPOINT",
      ending: "// END TRANSMISSION",
    };
    el.textContent = `${labels[type] || "// NODE"} — ${mood.toUpperCase()}`;
  }

  /**
   * clearTerminal() — clears output, rng, changes, choices, tag
   */
  function clearTerminal() {
    const ids = ["terminal-output", "rng-display", "changes-display", "choices-container", "node-tag"];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML ? (el.innerHTML = "") : (el.textContent = "");
    });
  }

  /**
   * appendText(element, text) — adds text without typewriter
   */
  function appendText(element, text) {
    element.textContent += text;
    _scrollTerminal();
  }

  /**
   * showRngResult(rng) — displays the attribute check result
   */
  function showRngResult(rng) {
    const el = document.getElementById("rng-display");
    if (!el) return;

    const { attribute, chance, roll, player_value, threshold, success } = rng;
    const attrUpper = attribute.toUpperCase();
    const resultClass = success ? "rng-success" : "rng-fail";
    const resultText = success ? "> SUCCESS" : "> FAILED";

    el.innerHTML = `
      <div class="rng-box">
        <div class="rng-title">[ ${attrUpper} CHECK ]</div>
        <div>YOUR ${attribute.toUpperCase()}: ${player_value} | NEEDED: ${threshold} | CHANCE: ${chance}%</div>
        <div>ROLLED: ${roll}</div>
        <div class="${resultClass}">${resultText}</div>
      </div>
    `;
    _scrollTerminal();
  }

  /**
   * showAttributeChanges(changes)
   */
  async function showAttributeChanges(changes) {
    const el = document.getElementById("changes-display");
    if (!el || !changes || changes.length === 0) return;
    el.innerHTML = "";

    for (const change of changes) {
      const line = document.createElement("div");
      line.className = "change-line";
      const delta = change.delta;
      const attrName = change.attribute.charAt(0).toUpperCase() + change.attribute.slice(1);
      if (delta > 0) {
        line.classList.add("change-positive");
        line.textContent = `  +${delta} ${attrName}`;
      } else {
        line.classList.add("change-negative");
        line.textContent = `  ${delta} ${attrName}`;
      }
      el.appendChild(line);
      _scrollTerminal();
      await new Promise(r => setTimeout(r, 150));
    }
  }

  /**
   * disableChoices() — prevent double-click
   */
  function disableChoices() {
    clearChoiceKeys();
    document.querySelectorAll(".choice-btn").forEach(b => { b.disabled = true; });
  }

  return {
    typeText,
    displayChoices,
    clearTerminal,
    appendText,
    showRngResult,
    showAttributeChanges,
    disableChoices,
    setNodeTag,
    setSpeed,
    getSpeed,
    get outputEl() { return document.getElementById("terminal-output"); },
  };
})();
