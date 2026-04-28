/**
 * robin.js — Robin the AI Bird Companion
 * Animated red robin sprite + GPT-powered chat panel.
 * Robin gives advice on stats, story context, hints, and shares her own past.
 */

const RobinPanel = (() => {
  const LS_NAME_KEY    = 'nopresidente_robin_name';
  const LS_HISTORY_KEY = 'nopresidente_robin_history';
  const MAX_HISTORY    = 40;   // max messages kept in localStorage
  const SPRITE_COLS    = 4;
  const SPRITE_ROWS    = 4;
  const DISPLAY_SIZE   = 96;   // px — sprite rendered at this size (square)
  const FRAME_MS       = 130;  // ms per animation frame

  let _name          = 'Robin';
  let _history       = [];    // [{role:'robin'|'player', content:'...'}]
  let _context       = { node_text: '', mood: '', attributes: {} };
  let _busy          = false;
  let _spriteInterval = null;
  let _spriteFrame   = 0;
  let _scaledFrameW  = 0;
  let _scaledFrameH  = 0;

  // ── Init ──────────────────────────────────────────────────────────────────

  function init() {
    _name    = localStorage.getItem(LS_NAME_KEY) || 'Robin';
    _history = _loadHistory();

    _wireControls();
    _renderNameDisplay();
    _setupSprite();
  }

  function updateContext(node, player) {
    _context = {
      node_text:  node?.text       || '',
      mood:       node?.mood       || '',
      attributes: player?.attributes || {},
    };
  }

  // ── Sprite ────────────────────────────────────────────────────────────────

  function _setupSprite() {
    const el = document.getElementById('robin-sprite-anim');
    if (!el) return;

    const img = new Image();
    img.onload = function () {
      const natFrameW = img.naturalWidth  / SPRITE_COLS;
      const natFrameH = img.naturalHeight / SPRITE_ROWS;
      const scale     = DISPLAY_SIZE / Math.max(natFrameW, natFrameH);

      _scaledFrameW = natFrameW * scale;
      _scaledFrameH = natFrameH * scale;

      el.style.width           = DISPLAY_SIZE + 'px';
      el.style.height          = DISPLAY_SIZE + 'px';
      el.style.backgroundImage = "url('/assets/sprites/spritesheet_red%20robin.png')";
      el.style.backgroundSize  =
        `${img.naturalWidth * scale}px ${img.naturalHeight * scale}px`;
      el.style.backgroundRepeat = 'no-repeat';
      el.style.imageRendering   = 'pixelated';

      _renderSpriteFrame(el, 0);
    };
    img.src = '/assets/sprites/spritesheet_red%20robin.png';
  }

  function _renderSpriteFrame(el, frame) {
    const col = frame % SPRITE_COLS;
    const row = Math.floor(frame / SPRITE_COLS);
    el.style.backgroundPosition =
      `-${col * _scaledFrameW}px -${row * _scaledFrameH}px`;
  }

  function _startSpriteAnim() {
    if (_spriteInterval || !_scaledFrameW) return;
    const el = document.getElementById('robin-sprite-anim');
    if (!el) return;
    _spriteInterval = setInterval(() => {
      _spriteFrame = (_spriteFrame + 1) % (SPRITE_COLS * SPRITE_ROWS);
      _renderSpriteFrame(el, _spriteFrame);
    }, FRAME_MS);
  }

  function _stopSpriteAnim() {
    if (_spriteInterval) {
      clearInterval(_spriteInterval);
      _spriteInterval = null;
    }
  }

  // ── Wire Controls ─────────────────────────────────────────────────────────

  function _wireControls() {
    document.getElementById('btn-robin')
      ?.addEventListener('click', open);

    document.getElementById('robin-close-btn')
      ?.addEventListener('click', close);

    // Close on backdrop click
    document.getElementById('robin-modal')
      ?.addEventListener('click', e => {
        if (e.target === document.getElementById('robin-modal')) close();
      });

    // Send on button click or Enter key
    document.getElementById('robin-send-btn')
      ?.addEventListener('click', _sendMessage);

    document.getElementById('robin-input')
      ?.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); _sendMessage(); }
        e.stopPropagation(); // prevent game hotkeys from firing inside the panel
      });

    // Rename flow
    document.getElementById('robin-rename-btn')
      ?.addEventListener('click', _showRenameInput);

    document.getElementById('robin-name-save')
      ?.addEventListener('click', _saveName);

    document.getElementById('robin-name-input')
      ?.addEventListener('keydown', e => {
        if (e.key === 'Enter')  _saveName();
        if (e.key === 'Escape') _hideRenameInput();
        e.stopPropagation();
      });

    // Clear history button
    document.getElementById('robin-clear-btn')
      ?.addEventListener('click', _clearHistory);
  }

  // ── Open / Close ──────────────────────────────────────────────────────────

  function open() {
    const modal = document.getElementById('robin-modal');
    if (!modal) return;
    modal.style.display = 'flex';

    // Render chat history (in case name changed or first open)
    _renderHistory();
    _scrollToBottom();

    _startSpriteAnim();
    document.getElementById('robin-input')?.focus();

    // Auto-greeting on first open
    if (_history.length === 0) {
      _fetchRobinReply('__intro__');
    }
  }

  function close() {
    document.getElementById('robin-modal').style.display = 'none';
    _stopSpriteAnim();
  }

  // ── Name Editing ──────────────────────────────────────────────────────────

  function _showRenameInput() {
    document.getElementById('robin-name-row').style.display      = 'none';
    document.getElementById('robin-name-edit-row').style.display = 'flex';
    const inp = document.getElementById('robin-name-input');
    if (inp) { inp.value = _name; inp.focus(); inp.select(); }
  }

  function _hideRenameInput() {
    document.getElementById('robin-name-row').style.display      = 'flex';
    document.getElementById('robin-name-edit-row').style.display = 'none';
  }

  function _saveName() {
    const inp = document.getElementById('robin-name-input');
    const newName = (inp?.value || '').trim();
    if (newName) {
      _name = newName;
      localStorage.setItem(LS_NAME_KEY, _name);
      _renderNameDisplay();
      _renderHistory(); // refresh labels
    }
    _hideRenameInput();
  }

  function _renderNameDisplay() {
    const el = document.getElementById('robin-name-display');
    if (el) el.textContent = _name;
  }

  // ── Messaging ─────────────────────────────────────────────────────────────

  async function _sendMessage() {
    if (_busy) return;
    const input = document.getElementById('robin-input');
    const text  = (input?.value || '').trim();
    if (!text) return;
    if (input) input.value = '';

    _addToHistory('player', text);
    await _fetchRobinReply(text);
  }

  async function _fetchRobinReply(message) {
    if (_busy) return;
    _busy = true;
    _setThinking(true);

    // Build OpenAI-style history (exclude the intro trigger from display)
    const apiHistory = _history
      .filter(h => h.content !== '__intro__')
      .map(h => ({
        role:    h.role === 'robin' ? 'assistant' : 'user',
        content: h.content,
      }));

    try {
      const res = await fetch('/api/robin', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history:      apiHistory.slice(0, -1), // exclude last (just added)
          game_context: _context,
          robin_name:   _name,
        }),
      });
      const data = await res.json();
      _addToHistory('robin', data.response || '...chirp...');
    } catch {
      _addToHistory('robin', '...chirp... Signal lost. Try again.');
    } finally {
      _setThinking(false);
      _busy = false;
      document.getElementById('robin-input')?.focus();
    }
  }

  function _addToHistory(role, content) {
    _history.push({ role, content });
    if (_history.length > MAX_HISTORY) _history = _history.slice(-MAX_HISTORY);
    _saveHistory();

    const histEl = document.getElementById('robin-chat-history');
    if (!histEl) return;

    const el = _buildMessageEl(role, content);
    histEl.appendChild(el);
    _scrollToBottom();
  }

  function _buildMessageEl(role, content) {
    const el = document.createElement('div');
    el.className = `robin-msg robin-msg-${role}`;
    const label = role === 'robin' ? _name : 'You';
    el.innerHTML =
      `<span class="robin-msg-label">${_escHtml(label)}:</span>` +
      `<span class="robin-msg-text">${_escHtml(content).replace(/\n/g, '<br>')}</span>`;
    return el;
  }

  function _renderHistory() {
    const histEl = document.getElementById('robin-chat-history');
    if (!histEl) return;
    histEl.innerHTML = '';
    _history.forEach(h => histEl.appendChild(_buildMessageEl(h.role, h.content)));
    _scrollToBottom();
  }

  function _setThinking(on) {
    const el = document.getElementById('robin-thinking');
    if (el) el.style.display = on ? 'flex' : 'none';

    const sendBtn = document.getElementById('robin-send-btn');
    const input   = document.getElementById('robin-input');
    if (sendBtn) sendBtn.disabled = on;
    if (input)   input.disabled   = on;
  }

  function _scrollToBottom() {
    const el = document.getElementById('robin-chat-history');
    if (el) el.scrollTop = el.scrollHeight;
  }

  function _clearHistory() {
    if (!confirm(`Clear your entire conversation with ${_name}?`)) return;
    _history = [];
    _saveHistory();
    _renderHistory();
  }

  // ── Persistence ───────────────────────────────────────────────────────────

  function _saveHistory() {
    try {
      localStorage.setItem(LS_HISTORY_KEY, JSON.stringify(_history));
    } catch { /* storage full — silently skip */ }
  }

  function _loadHistory() {
    try {
      return JSON.parse(localStorage.getItem(LS_HISTORY_KEY) || '[]');
    } catch {
      return [];
    }
  }

  // ── Utility ───────────────────────────────────────────────────────────────

  function _escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  return { init, updateContext, open, close };
})();
