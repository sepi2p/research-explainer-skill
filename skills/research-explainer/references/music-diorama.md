# Music brief: paper-diorama explainers

## 1. The sound in one paragraph
A small acoustic workshop band playing in a lamp-lit room: plucked bass, harp, soft mallets and a little glass sparkle, the sound of a wooden toy that works. Curious, patient, quietly confident: a chamber score for a stop-motion short, not a trailer. Nothing electronic, epic or sad. It sits under the narrator and speaks only in the narrator's pauses.

## 2. Fixed decisions
- **Tempo:** 66–80 bpm with a quarter-note feel for every section with speech. Never 95–105 bpm, where eighth notes land on the syllable rate (about 3.3/s). Only one grid runs per chapter; it runs freely and is never locked to the words. **Exception:** a silence-only hold may take the period of its own periodic SFX, at any bpm (e.g. a card every 2.73 s gives a 4/4 bar at 87.8 bpm). The chapter's grid returns at the first spoken word after the hold.
- **Metre:** 4/4. Use 3/4 only for a waltz-like reprise at the end screen.
- **Key:** one home key, a major key with a pentatonic lean. Tune it to the rung-chime SFX (measure its partials). Allowed relations are the IV key, the relative minor and dorian for the teaser. Harmony is diatonic, with add9, sus2 and sus4. Doubt is a sus4 that does not resolve. Never diminished, never minor-ominous. Change chords every 2–4 bars.
- **Pitched SFX:** list every pitched SFX with its MIDI pitch (fundamental, plus the strong partials of bells) and the key of the section it sounds in. If it is not diatonic there, retune it to that key in a copy of the mixer. If it must stay sour, drop the music to bass only for 1 s around it (−0.5 s to +0.5 s). Unpitched SFX (noise ticks, flips, slams) need no entry. Short chirps under 150 ms (pops, wood knocks) count as unpitched.
- **Palette (CC0 only: VSCO 2 CE, VCSL):**

| Role | Instruments |
|---|---|
| pulse | `marimba` (soft, low velocity), `shaker` (≤0.1 vel, on quarters only, never eighths or sixteenths), `contrabass_pizz` on beats 1 and 3 |
| bass | `contrabass_pizz`, low `harp`, `cellos` only at MIDI 36–45 with a 0.8 s attack |
| harmony | `harp` (strum 0.03); `vibraphone` and `vibraphone_bowed` (see §3.1 for register); `upright` voiced at MIDI ≥ 76 under speech |
| colour | `glockenspiel`, `hand_chimes`, `mbira` (kalimba stand-in), `triangle`, `violins_pizz`/`violas_pizz` |
| melody (gaps only) | `clarinet`, `flute`, `recorder`, `ocarina`, upper `marimba` |

- **Avoid:**
  - `drum_kit` and `piano`: CC BY (attribution required) and not installed.
  - `kalimba`, `accordion`, `guitar_nylon`, `ukulele` (FreePats) and `alto_sax` (Karoryfer): CC0, but the packs are not installed. Fetch them first.
  - Snare, timpani rolls, crash, gong and `gran_cassa`: too cinematic.
  - Sustained brass, `organ_soft` and mid-register `violins`: they fill the voice band.
  - `vibraphone_hard` and `xylophone`: too bright in the 1–4 kHz band.
  - `alto_sax`, `tenor_sax`, harmonica, and `oboe` under speech: they sound like a voice.
  - `tubular_bells`: it collides with the chime.

## 3. Room for the voice
**Measure each episode's narrator before composing.** Measure f0 p5, median and p95 on speech frames, the long-term average spectrum (LTAS) of speech frames, its centroid and the number of pauses per minute. Then work out:
- **No-sustain zone:** MIDI(f0 p5) to MIDI(2 × f0 p95), rounded outward. That covers the fundamental and the first harmonic, where most of the voice's energy sits.
- **Voice body band:** the band where the LTAS is strongest. Report it in Hz; it feeds rule 1 below.

*Example (the default paid voice, gpt-audio "marin"):* f0 median 195 Hz, p5–p95 152–302 Hz, centroid 700 Hz, about 20 pauses per minute. MIDI(152 Hz) = 50.6 and MIDI(604 Hz) = 74.1, so the no-sustain zone is **MIDI 50–75**. The body band is 200–1000 Hz, and 1–4 kHz holds 1.2 % of the energy. A male narrator moves all of these numbers down: re-measure the voice, never copy them.

1. **The body band (example voice: 200–1000 Hz).** Under speech, keep music in this band at least 18 dB below the voice. Hold no sustained note inside the no-sustain zone. Instruments with a long ring count as sustained:
   - `upright` voicings sit at MIDI ≥ 76 under speech.
   - `vibraphone` and `vibraphone_bowed` under speech: only at MIDI ≥ 76, or damped to a duration of 0.6 s or less. Otherwise use them only in gaps.
2. **1–4 kHz is intelligibility.** This band carries the consonants. Put a fixed −5 dB bell at 2.5 kHz (Q 0.8) on the music bus. Mallet and glock notes land here too: under speech they stay transient, and they count toward the density rule (rule 5).
3. **Below 150 Hz is nearly free.** Bass at MIDI 36–48 gets only a further 0–2 dB of duck under speech (§6).
4. **Above 5 kHz is free, except the sibilance region at 6–9 kHz.** Shelf the music down 2 dB there while the voice is active.
5. **Density:** under speech, allow at most 2 onsets/s summed over all instruments above 120 Hz. Allow a low sustain plus a sparse high pluck, and no new ideas.
   - Pauses under 1.5 s: nothing; the duck release is the breath.
   - Gaps of 1.5 s or more: a motif answer or a chord change.
   - Holds over 5 s: 3–5 layers and a mid-register melody.
6. **Dynamics:** swells only in gaps. Measure the music's LRA on the unducked score, leaving out the dropouts and the aside. It must be ≤ 6 LU.

## 4. Recipes
**SFX fall into two classes.**
- **Locked:** the chapter chime, the slips of a silence-only hold, and the wall rows. Music lands on them sample-exact (±10 ms) and takes its pitches from the SFX (§2 list). Unpitched locked SFX, such as noise ticks, take their pitches from the section's key.
- **Avoid:** stamp, pop, cascade, crack, whoosh and every other SFX. No music onset within ±80 ms of them. Music moves on phrases and downbeats instead.

**Energy scale (0–10)** counts layers and their level offset from the reference bed (§6):

| Energy | Layers and level |
|---|---|
| 0 | off |
| 1 | 1 layer at −6 dB |
| 2 | 1 layer at −3 dB |
| 3 | 1 layer at 0 dB |
| 4 | 2 layers at −2 dB |
| 5 | 2 layers at 0 dB |
| 6 | 3 layers at 0 dB |
| 7 | 3 layers at +1 dB |
| 8 | 4–5 layers at 0 dB |
| 9 | 5 layers at +1 dB with melody |
| 10 | tutti, recap and outro only |

| Section | Texture / dynamics | Entry, exit, SFX |
|---|---|---|
| Hook | M1 in full: marimba, harp, pizz bass (energy 6) | Enters with the first line; drop the pulse during pop runs |
| Story | Plucked bass + violas_pizz, low | Enters on the chapter downbeat |
| Aside | Silence | Out within 0.5 s of the opening flip; back 0.8 s after the closing one |
| Data explanation | One layer, root + fifth | Thin over 2 bars, never cut; keep the mid range clear for reading |
| Auto-cascade / list run | Pulse out; sustain only | Pulse returns on the first downbeat after the cascade's last SFX |
| Naming reveal | Nothing on the stamp; harp roll on its tail (+0.3 s) | Chord change on the next downbeat |
| Error / wrong-answer hit | Music thins to one layer 0.5 s before the hit; nothing on the hit (avoid class) | Back on the next downbeat after the SFX tail |
| Dry line | Thin to nothing over the 2 bars before the line; below −40 dBFS from its first word to 0.5 s after its last | Re-enter on the next downbeat, one layer |
| Payoff | M1 phrase + glock, one step brighter, resolve to I | Lift on a free instant (no SFX within ±80 ms) |
| Problem / cliffhanger | M3 sus4 held; near silence on the key line | Never resolve before the next chapter |
| Chapter change | Cadence ends on the chime (locked) | New orchestration from the next downbeat; 1 s equal-power crossfade. M2 starts at chime + 1.0 s if its first note is A6 or above. Otherwise it starts when the chime has decayed (end of the chime sample) |
| In-chapter scene change without a chime | No crossfade | Chord change on the next downbeat |
| Recap / term wall | Fullest: low cellos, harp, marimba, glock; M2 one note per row (locked) | +1 dB per row, peak at the lesson, cadence home |
| Teaser | Dorian, mbira + bowed vibe, rising | Ends on IV add9, open |
| Call to action | Two light pizz bars | Bridges into the next key |
| Outro / end screen | M1 reprise, then M2 in full | Music only after the last word; cadence 1.5 s before the end |
| Silence-only hold | Melody allowed (clarinet/flute M1), −4 dB re voice | Grid at the SFX period; downbeats on the slips (locked) |

## 5. Form over 20+ minutes
- **Motifs:**
  - **M1, the workshop theme.** 4 bars, pentatonic, about 6 notes. It is the episode's identity.
  - **M2, the ladder (progress leitmotif).** A rising pentatonic from the chime's pitch. At chapter *k* it plays *k* notes, so the audience hears the ladder grow. It is complete only at the recap and the outro. In the teaser it stops one note short. If speech starts before M2 can finish, M2 runs under the words and follows the density rule (≤ 2 onsets/s, nothing else above 120 Hz while it plays).
  - **M3, doubt.** A sus4 to sus2 pair.
  - **M4, the "method" colour.** Bowed-vibe fifths and high harp for the cool or technical space.
- **Re-orchestrate every chapter** (lead colour, register or key). M1 never repeats in the same orchestration within 5 minutes. No 8-bar block repeats exactly more than twice per chapter. Vary voicings with a seed and velocities by ±5 %.
- **Against fatigue:**
  - A thin bed changes chord every 2–4 bars and rotates its one instrument every 30–45 s.
  - Any chapter over 120 s re-orchestrates every 60–90 s.
- **Energy arc:**
  - Establish, then a first lift, then the main peak at the method's name.
  - A long, lean middle carried by small payoffs.
  - The warmest peak at the recap, then an open end.
  - Thin stretches are rests for the ear, not gaps to fill.
- **The arc lives in the score.** The mixer applies one global gain (§6), so every level difference in this section and in §4 must be written into the score.

## 6. Mixing and delivery
- **Final loudness** is set by `assemble.py`: −14 LUFS, true peak ≤ −1 dBTP after encoding. The score never sets absolute loudness. It sets only its level relative to the voice stem, which is −18 LUFS per clip.
- **Who ducks:** the mixer, only. The score is delivered unducked.
- **Mixer input:** the mixer reads `music_dry_unducked.wav` in stereo and applies one fixed gain. That gain puts the reference bed (energy 5) at −8 dB re voice RMS. There is no per-bed RMS normalisation and no downmix to mono. Voice and SFX sit in the centre of a stereo sum. (The template's `work/audio.py` does this when `work/music/score.wav` exists.)
- **Duck:**
  - The bed sits at −8 dB re voice RMS.
  - Under speech, the band above 150 Hz drops a further 10 dB (−18 dB in total).
  - The band below 150 Hz drops a further 0–2 dB.
  - Attack 50 ms, release 450 ms, as in the template's `work/audio.py`.
- **Resulting music re voice (short-term):**
  - −18 dB under speech.
  - −8 dB in gaps of 1.5 s or more.
  - −4 to −6 dB in holds (written in the score as +2 to +4 dB).
  - About −22 LUFS-S on the end screen.
- **Low end:** high-pass the music at 35 Hz.
- **Room:** one shared `S.room(size=.35, mix=.18, damp=.6, predelay=.02)`, a small wooden room. Accents run a little wetter (.25).
- **Stereo:** bass and pulse in the centre, harp and marimba at ±0.3, colour at ±0.5. Everything must stay mono-safe.
- **Deliver** 48 kHz 24-bit stereo, at the exact length, all unducked:
  - `music_bed.wav` and `music_accents.wav` (stems).
  - `music_dry_unducked.wav` (the sum).
  - `credits.txt` (`S.credits`).

## 7. Composing with the Lemo-Opuscar sampler
```python
sys.path.insert(0, LIB); os.chdir(LIB)
from core.audio import sampler as S; from core.audio.sfx import SR
S.seed(SEED); rng = np.random.default_rng(SEED)          # one seed per episode -> bit-identical
cm = json.load(open(CUEMAP)); tl = json.load(open(TIMELINE))
for sec in chapters(cm):                                   # one render per chapter
    t0 = chime(sec) + 60/sec.bpm; grid = bars(t0, sec.bpm)  # free-running grid from the downbeat
    ev = bed(sec, grid, rng) + motifs(sec, grid) + hits(cm['hits'], sec)
    ev = lint(ev, tl, cues)   # no-sustain zone, <=2 onsets/s summed >120 Hz in speech, SFX classes
    out = xfade(out, S.room(S.render(ev, master=False), .35, .18), at=chime(sec), dur=1.0)
write(out, 'music_dry_unducked.wav')   # unducked: the mixer ducks
```
- **Timing:** take hits from `beat.start`/`beat.end` (timeline.json) and from cues.json. A gap `next.start − end` of 1.5 s or more is a motif slot. Clip-internal pauses (⏸) count only if the voice stem is silent there. Quantise only section entries, to the first downbeat at or after the cue. Locked SFX are the exception: they are placed at the SFX time, not quantised.
- **Render** under `nice -n 10`, one chapter at a time.
- **In the diorama template** this is already written: `work/measure_voice.py` (section 3) → `work/make_cuemap.py` (the cue map; a CONFIG block per video) → `work/music.py` (the composer above, with lint and the section 8 event checks) → `work/audio.py` (mixes and ducks it). Order and options: `templates/diorama/README.md`, "Original music".

## 8. Checks before handover
1. The length equals the video to ±1 sample. There are no clicks at crossfades.
2. Voice minus music (short-term, speech frames, after the mixer): median ≥ 18 dB, p5 ≥ 14 dB. Per band at 1–4 kHz: voice band level minus music band level ≥ 12 dB.
3. The aside is below −60 dBFS. Dry lines are below −40 dBFS.
4. The music's LRA, measured on the unducked score without the dropouts and the aside, is ≤ 6 LU. The final loudness comes from `assemble.py`: −14 LUFS, true peak ≤ −1 dBTP after encoding.
5. **Event lint:**
   - No sustain inside the no-sustain zone over a spoken beat.
   - ≤ 2 onsets/s summed above 120 Hz during speech.
   - Shaker on quarters only.
   - Locked SFX hit within ±10 ms.
   - No onset within ±80 ms of an avoid-class SFX.
   - Every pitched SFX is diatonic in its section, or the music is bass-only for 1 s around it.
6. Every instrument is CC0 in `S.info`. The credits are written.
7. Chroma correlation with the section key is > 0.6 per chapter. No 8-bar block repeats more than twice. A thin bed rotates its instrument within 45 s.
8. Listen to the hook, the middle and the recap on laptop speakers and in mono.
