# ¡No Presidente! — Asset Production TODO

All assets are optional — the game runs without them (placeholder colors + silence).
But adding them transforms the experience from "text game" to "pixel art adventure."

---

## FOLDER LOCATIONS

```
no-presidente/
└── frontend/
    └── assets/
        ├── sprites/     ← all .png sprite images go here
        ├── audio/       ← all .mp3 audio files go here
        └── fonts/       ← any custom font files go here (currently loaded via Google Fonts CDN)
```

---

## SPRITES (Pixel Art)

### Global Style Guide
- **Style:** 8-bit / 16-bit pixel art — think SNES-era RPG portraits
- **Format:** PNG with transparency (32-bit RGBA)
- **Color palette:** 16–32 colors max per image for authentic feel
- **Pixel size:** Each "pixel" should be at least 3–4 screen pixels wide — chunky, readable
- **Rendering:** The game uses `image-rendering: pixelated` — do NOT export with anti-aliasing or blending
- **Tool suggestions:** Aseprite, Libresprite, Piskel (free, browser-based), GraphicsGale

---

### Scene/Background Sprites
Displayed in the Visual Panel (top of screen) while story text plays.
The panel is `200px tall`. The sprite area is `220px wide × 200px tall`.
The right side fades into the terminal background via a CSS gradient — **keep important content left-aligned**.

| Filename | Canvas Size | Export Size | Scene Description | Mood |
|---|---|---|---|---|
| `street_morning.png` | 64×56 px | 192×168 px | Empty street at dawn — lamppost, apartment building, two distant figures | mysterious |
| `rosa_garage.png` | 64×56 px | 192×168 px | Dark parking garage — Rosa leaning on car hood, headlights behind her | hopeful |
| `vargas_car.png` | 64×56 px | 192×168 px | Sedan on street, nervous man in driver seat, city background | tense |
| `vargas_trust.png` | 64×56 px | 192×168 px | Same car — Vargas relieved, hand extended with a badge | hopeful |
| `alley_escape.png` | 64×56 px | 192×168 px | Night alley — silhouette running, soldiers behind | dangerous |
| `jorge_footage.png` | 64×56 px | 192×168 px | Laptop screen showing night-vision helicopter footage | mysterious |
| `rosa_laptop.png` | 64×56 px | 192×168 px | Rosa at laptop, satellite map on screen | hopeful |
| `consulate_line.png` | 64×56 px | 192×168 px | Government building exterior, formal queue, Venezuelan flag | tense |
| `smuggler_boat.png` | 64×56 px | 192×168 px | Small fishing boat at night, woman at helm, dark water | dangerous |
| `detention_room.png` | 64×56 px | 192×168 px | Bare white room, single chair, flickering overhead light | tense |
| `palace_exterior.png` | 64×56 px | 192×168 px | White palace walls, floodlights, guards silhouetted at gate | mysterious |
| `carmen_courtyard.png` | 64×56 px | 192×168 px | Palace courtyard — woman in lab coat glancing over shoulder | hopeful |

**Canvas vs Export Size explained:**
Draw at **64×56 px** (native pixel canvas), then export/scale to **192×168 px** at 3× zoom with no interpolation. This gives you chunky 3px pixels on screen. Alternatively draw at 48×42 px and export at 4×.

---

### Character Sprites (Portraits)
Shown in the Visual Panel during character-focused nodes.
These are taller and narrower — portrait orientation, character centered in frame.

| Filename | Canvas Size | Export Size | Character | Description |
|---|---|---|---|---|
| `pete_missing.png` | 48×64 px | 144×192 px | Pete — ABSENT | Empty glass tank with crack, note on the floor |
| `pete_portrait.png` | 48×64 px | 144×192 px | Pete the Platypus | Pixel platypus — grumpy expression, small bill, little arms |
| `rosa_portrait.png` | 48×64 px | 144×192 px | Rosa (CIA fixer) | 40s woman, sharp eyes, leather jacket, arms crossed |
| `vargas_portrait.png` | 48×64 px | 144×192 px | Vargas (attaché) | Sweating, loose tie, scared but earnest look |
| `carmen_portrait.png` | 48×64 px | 144×192 px | Dr. Carmen Vega | Lab coat, kind face, visibly exhausted |
| `delgado_portrait.png` | 48×64 px | 144×192 px | El Presidente Delgado | Ornate uniform, absurd fake medals, holding Pete like a trophy |
| `paloma_portrait.png` | 48×64 px | 144×192 px | Paloma (smuggler) | Wiry, weathered, fishing gear, cigarette behind ear |
| `player_portrait.png` | 48×64 px | 144×192 px | The Player | Determined face — team can design this freely |

**Draw at 48×64 px native, export at 3× = 144×192 px.** Portrait sprites should have a transparent background so the mood color shows through behind them.

---

### Ending Splash Screens
Shown inside the ending overlay box (max-width 640px).
These are wider, cinematic compositions — landscape orientation.

| Filename | Canvas Size | Export Size | Ending | Scene |
|---|---|---|---|---|
| `ending_diplomat.png` | 160×80 px | 480×240 px | Ending 1: The Diplomat | Player walking out of palace front door with Pete, tuxedo, champagne glass |
| `ending_ghost.png` | 160×80 px | 480×240 px | Ending 2: The Ghost | Silhouette in tunnel, Pete under arm, moonlight through storm grate |
| `ending_caught.png` | 160×80 px | 480×240 px | Ending 3: So Close | Surrounded by soldiers in hallway, Delgado in bathrobe center frame |
| `ending_standoff.png` | 160×80 px | 480×240 px | Ending 4: The Standoff | Player and Delgado facing off in palace garden at dawn, Pete between them |
| `ending_broken.png` | 160×80 px | 480×240 px | Ending: Broken Spirit | Lone figure sitting on a curb, city skyline behind, hands empty |

**Draw at 160×80 px native, export at 3× = 480×240 px.** These should be your most polished pieces — they're the last thing a player sees.

---

## AUDIO (Music + SFX)

### BGM Tracks (Looping)

All BGM tracks should **loop seamlessly** — the loop point should be invisible.
The game crossfades between tracks over 2 seconds when the mood changes.
Keep the mix subtle and low — they play continuously under the story text.

| Filename | Mood | Target Duration | Target File Size | Format | Description / Vibe |
|---|---|---|---|---|---|
| `tense.mp3` | TENSE | 90–120 sec | ≤ 800 KB | MP3 128kbps | Slow, ominous. Low synth drones + distant percussion. NES infiltration feel. |
| `hopeful.mp3` | HOPEFUL | 90–120 sec | ≤ 800 KB | MP3 128kbps | Warm chiptune. Ascending melody, gentle rhythm. Finding an ally. |
| `dangerous.mp3` | DANGEROUS | 60–90 sec | ≤ 600 KB | MP3 128kbps | Fast, urgent. Heavy bassline + rapid arpeggios. Chase scene energy. |
| `mysterious.mp3` | MYSTERIOUS | 90–120 sec | ≤ 800 KB | MP3 128kbps | Ambient, sparse. Echoing notes, slow tempo. Exploration feel. |
| `triumphant.mp3` | TRIUMPHANT | 60–90 sec | ≤ 600 KB | MP3 128kbps | Fanfare-style 8-bit victory. Uplifting, celebratory. |

**Recommended tools:** Famitracker (NES-accurate), LSDJ (Game Boy), BeepBox (free, browser), FamiStudio, or any DAW with a chiptune plugin (e.g. GXSCC, Magical 8bit Plug).
**Export settings:** MP3, 128 kbps, 44.1 kHz, mono or stereo both fine. Normalize to -3 dBFS peak.

---

### Sound Effects (Short, punchy)

| Filename | Trigger | Target Duration | Target File Size | Format | Description |
|---|---|---|---|---|---|
| `choice_select.mp3` | Player clicks any choice | 0.1–0.2 sec | ≤ 20 KB | MP3 128kbps | Short blip/click. 8-bit menu select sound. |
| `attribute_up.mp3` | Any attribute increases | 0.4–0.6 sec | ≤ 30 KB | MP3 128kbps | Rising tone, cheerful. NES-style power-up chime. |
| `attribute_down.mp3` | Any attribute decreases | 0.4–0.6 sec | ≤ 30 KB | MP3 128kbps | Descending tone, negative. "Ouch" hit sound. |
| `morale_warning.mp3` | Morale drops to ≤ 2 | 0.6–1.0 sec | ≤ 50 KB | MP3 128kbps | Alarm-like. Low buzzing chime, unsettling. |
| `ending_fanfare.mp3` | Any ending node reached | 2.0–3.0 sec | ≤ 150 KB | MP3 128kbps | Full 8-bit fanfare. Can be triumphant or somber per ending type. |

**Export settings:** MP3, 128 kbps, 44.1 kHz. Trim silence from both ends. Normalize to -3 dBFS peak.
**Tip:** Generate SFX easily with [jsfxr](https://sfxr.me) or [Bfxr](https://www.bfxr.net) — both are free, browser-based 8-bit SFX generators. Export as WAV then convert to MP3.

---

## FONTS (Optional — currently loaded from Google Fonts CDN)

The game loads **Press Start 2P** via Google Fonts CDN. Self-host these if you want offline support:

| Filename | File Size | Where to put it | Purpose |
|---|---|---|---|
| `PressStart2P-Regular.ttf` | ~72 KB | `frontend/assets/fonts/` | Main pixel font — all terminal text, HUD, buttons |
| `IBMPlexMono-Regular.ttf` | ~74 KB | `frontend/assets/fonts/` | Fallback monospace font |
| `IBMPlexMono-Bold.ttf` | ~74 KB | `frontend/assets/fonts/` | Bold variant |

To switch to self-hosted fonts, replace the `@import` at the top of `terminal.css` with `@font-face` blocks pointing to these files.

---

## PRIORITY ORDER

If you're short on time, here's the order that gives the most impact per hour:

### Tier 1 — Do these first (core experience)
1. `pete_portrait.png` — Pete needs to exist. He's the whole point.
2. `delgado_portrait.png` — The villain. Make him ridiculous.
3. `palace_exterior.png` — The pivotal arrival moment
4. `tense.mp3` + `hopeful.mp3` — The two most-played BGM tracks
5. `choice_select.mp3` — Used on every single click, immediate impact

### Tier 2 — Story immersion
6. `ending_diplomat.png`, `ending_ghost.png`, `ending_standoff.png` — The good endings
7. `rosa_portrait.png`, `carmen_portrait.png` — Key ally characters
8. `street_morning.png`, `pete_missing.png` — Opening sequence scenes
9. `dangerous.mp3`, `mysterious.mp3`

### Tier 3 — Full polish
10. Remaining scene sprites (vargas, alley, jorge, consulate, boat, detention, courtyard)
11. `triumphant.mp3`
12. Remaining SFX (`attribute_up`, `attribute_down`, `morale_warning`, `ending_fanfare`)
13. Remaining character portraits (vargas, paloma, player)
14. `ending_caught.png`, `ending_broken.png`

---

## NOTES FOR ARTISTS

- Sprite filenames are set in the `"sprite"` field of each node in `data/story/test_story.json`. The game prefixes `/assets/sprites/` automatically.
- To reference a sprite in a new story node: `"sprite": "filename.png"`
- **Missing sprites** → shows a mood-colored gradient. No crash.
- **Missing audio** → silent. No crash.
- All pixel art should use a **limited palette (16–32 colors max)** for authentic feel.
- Stick to the canvas sizes above when drawing — scaling up with 3× integer zoom keeps pixels clean.
- Do NOT use nearest-neighbor scaling in your export if your tool adds anti-aliasing — export at the exact canvas size and let CSS scale it up, or export at the 3× size yourself with no interpolation.
