/**
 * audio.js — Howler.js wrapper: BGM per mood, crossfade, SFX
 * The game works perfectly with no audio files present.
 */

const AudioManager = (() => {
  const MOOD_TRACKS = ["tense", "hopeful", "dangerous", "mysterious", "triumphant"];
  const SFX_NAMES = ["choice_select", "attribute_up", "attribute_down", "morale_warning", "ending_fanfare"];

  let _muted = false;
  let _volume = 0.6;
  let _currentMood = null;
  let _currentTrack = null;
  let _tracks = {};   // mood → Howl
  let _sfx = {};      // name → Howl
  let _initialized = false;
  let _firstInteraction = false;

  /**
   * init() — preload all tracks (won't play until first interaction)
   */
  function init() {
    if (_initialized) return;
    _initialized = true;

    // Preload mood tracks
    MOOD_TRACKS.forEach(mood => {
      try {
        const h = new Howl({
          src: [`/assets/audio/${mood}.mp3`],
          loop: true,
          volume: 0,
          preload: true,
          onloaderror: () => console.warn(`Audio: could not load ${mood}.mp3 — skipping`),
        });
        _tracks[mood] = h;
      } catch (e) {
        console.warn(`Audio: Howl creation failed for ${mood}`, e);
      }
    });

    // Preload SFX
    SFX_NAMES.forEach(name => {
      try {
        const h = new Howl({
          src: [`/assets/audio/${name}.mp3`],
          volume: _volume,
          preload: true,
          onloaderror: () => console.warn(`Audio: could not load ${name}.mp3 — skipping`),
        });
        _sfx[name] = h;
      } catch (e) {
        console.warn(`Audio: Howl creation failed for SFX ${name}`, e);
      }
    });

    // First interaction unlocks audio
    const unlock = () => {
      if (!_firstInteraction) {
        _firstInteraction = true;
        // If a mood was set before first interaction, start it now
        if (_currentMood) playMoodTrack(_currentMood);
      }
    };
    document.addEventListener("click", unlock, { once: true });
    document.addEventListener("keydown", unlock, { once: true });
  }

  /**
   * playMoodTrack(mood) — crossfade from current track to new mood (2s)
   */
  function playMoodTrack(mood) {
    if (_muted) { _currentMood = mood; return; }
    if (mood === _currentMood) return;

    const prev = _currentMood;
    _currentMood = mood;

    if (!_firstInteraction) return;   // will be called on first interaction

    // Fade out current
    if (prev && _tracks[prev]) {
      const old = _tracks[prev];
      old.fade(old.volume(), 0, 2000);
      setTimeout(() => old.pause(), 2100);
    }

    // Fade in new
    if (_tracks[mood]) {
      const track = _tracks[mood];
      if (!track.playing()) track.play();
      track.fade(0, _volume, 2000);
      _currentTrack = track;
    }
  }

  /**
   * playSFX(name) — play a short SFX
   */
  function playSFX(name) {
    if (_muted) return;
    if (!_firstInteraction) return;
    if (_sfx[name]) {
      try {
        _sfx[name].volume(_volume);
        _sfx[name].play();
      } catch (e) {
        console.warn(`Audio: could not play SFX ${name}`, e);
      }
    }
  }

  /**
   * setVolume(level) — master volume [0, 1]
   */
  function setVolume(level) {
    _volume = Math.max(0, Math.min(1, level));
    Howler.volume(_volume);
  }

  /**
   * toggleMute() → bool (new muted state)
   */
  function toggleMute() {
    _muted = !_muted;
    if (_muted) {
      Howler.volume(0);
    } else {
      Howler.volume(_volume);
      if (_currentMood) playMoodTrack(_currentMood);
    }
    return _muted;
  }

  return { init, playMoodTrack, playSFX, setVolume, toggleMute };
})();
