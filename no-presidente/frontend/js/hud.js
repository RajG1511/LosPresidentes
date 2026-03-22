/**
 * hud.js — Attribute bars + morale display + floating change text
 */

const HUD = (() => {
  const ATTR_ORDER = ["rapport", "stealth", "intelligence", "strength", "morale"];
  const ATTR_LABELS = {
    rapport: "Rapport",
    stealth: "Stealth",
    intelligence: "Intel",
    strength: "Strength",
    morale: "Morale ♥",
  };

  let _barEls = {};   // attr → { container, bar, val }

  /**
   * initHUD(attributes) — creates the HUD bar elements
   */
  function initHUD(attributes) {
    const container = document.getElementById("hud-attributes");
    if (!container) return;
    container.innerHTML = "";
    _barEls = {};

    ATTR_ORDER.forEach(attr => {
      const val = attributes[attr] ?? 0;
      const isMoreale = attr === "morale";

      const wrapper = document.createElement("div");
      wrapper.className = "hud-attr" + (isMoreale ? " morale" : "");
      wrapper.id = `hud-attr-${attr}`;

      const label = document.createElement("div");
      label.className = "hud-attr-label";
      label.textContent = ATTR_LABELS[attr] || attr;

      const barContainer = document.createElement("div");
      barContainer.className = "hud-attr-bar-container";

      const bar = document.createElement("div");
      bar.className = "hud-attr-bar";
      bar.style.width = `${(val / 10) * 100}%`;

      barContainer.appendChild(bar);

      const valEl = document.createElement("div");
      valEl.className = "hud-attr-val";
      valEl.textContent = `${val}/10`;

      wrapper.appendChild(label);
      wrapper.appendChild(barContainer);
      wrapper.appendChild(valEl);
      container.appendChild(wrapper);

      _barEls[attr] = { wrapper, bar, val: valEl };
    });
  }

  /**
   * updateHUD(attributes, changes) — updates bars + shows floating change text
   */
  function updateHUD(attributes, changes) {
    if (!attributes) return;

    ATTR_ORDER.forEach(attr => {
      const val = attributes[attr] ?? 0;
      const els = _barEls[attr];
      if (!els) return;

      els.bar.style.width = `${(val / 10) * 100}%`;
      els.val.textContent = `${val}/10`;

      // Morale low warning
      if (attr === "morale") {
        if (val < 3) {
          els.wrapper.classList.add("low-morale");
        } else {
          els.wrapper.classList.remove("low-morale");
        }
      }
    });

    // Show floating change text
    if (changes) {
      changes.forEach(change => {
        _showFloatingChange(change.attribute, change.delta);
      });
    }
  }

  /**
   * _showFloatingChange(attr, delta) — shows "+2" or "-1" floating up and fading
   */
  function _showFloatingChange(attr, delta) {
    const els = _barEls[attr];
    if (!els) return;

    const floater = document.createElement("div");
    floater.className = "float-change " + (delta > 0 ? "positive" : "negative");
    floater.textContent = (delta > 0 ? "+" : "") + delta;

    els.wrapper.style.position = "relative";
    els.wrapper.appendChild(floater);

    // Remove after animation (1s)
    setTimeout(() => floater.remove(), 1100);
  }

  /**
   * flashMoraleDeath() — flash HUD red before game-over screen
   */
  function flashMoraleDeath() {
    const hud = document.getElementById("hud-bar");
    if (!hud) return;
    hud.classList.add("morale-flash");
    setTimeout(() => hud.classList.remove("morale-flash"), 1000);
  }

  return { initHUD, updateHUD, flashMoraleDeath };
})();
