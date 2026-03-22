/**
 * visuals.js — Sprite panel + mood-based color transitions
 */

const Visuals = (() => {
  let _moodsData = null;

  function init(moodsData) {
    _moodsData = moodsData;
  }

  /**
   * setMood(mood) — updates CSS custom properties and mood badge
   */
  function setMood(mood) {
    if (!_moodsData || !_moodsData.moods) return;
    const cfg = _moodsData.moods[mood];
    if (!cfg) return;

    const root = document.documentElement;
    root.style.setProperty('--terminal-bg', cfg.terminal_bg);
    root.style.setProperty('--terminal-text', cfg.text_color);
    root.style.setProperty('--panel-border', cfg.hud_accent);
    root.style.setProperty('--hud-accent', cfg.hud_accent);
    root.style.setProperty('--choice-hover-bg', `${cfg.hud_accent}20`);

    // Visual panel background
    const visual = document.getElementById('visual-panel');
    if (visual) visual.style.setProperty('--visual-bg', cfg.terminal_bg);

    // Update the overlay gradient so it fades into the new bg color
    const overlay = document.getElementById('visual-overlay');
    if (overlay) {
      overlay.style.background = `linear-gradient(to right, transparent 140px, ${cfg.terminal_bg} 220px)`;
    }

    // Mood badge
    const badge = document.getElementById('mood-badge');
    if (badge) badge.textContent = mood.toUpperCase();
  }

  /**
   * setSprite(spriteUrl) — crossfade to new sprite or hide
   */
  function setSprite(spriteUrl) {
    const container = document.getElementById('sprite-container');
    if (!container) return;

    container.style.opacity = '0';
    setTimeout(() => {
      if (spriteUrl) {
        container.style.backgroundImage = `url('/assets/sprites/${spriteUrl}')`;
        container.style.opacity = '1';
      } else {
        container.style.backgroundImage = '';
        container.style.opacity = '0';
      }
    }, 250);
  }

  return { init, setMood, setSprite };
})();
