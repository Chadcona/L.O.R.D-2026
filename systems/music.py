# Procedural chiptune music engine
# Generates retro RPG background music at runtime using pygame sound synthesis
# Town theme: funky, party-vibe 8-bit groove inspired by 90s hip-hop rhythms

import pygame
import math
import struct
import array


SAMPLE_RATE = 22050
CHANNELS = 1


def _generate_wave(freq, duration, wave_type="square", volume=0.3, duty=0.5):
    """Generate a raw waveform as a list of samples."""
    n_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        phase = (t * freq) % 1.0

        if wave_type == "square":
            val = volume if phase < duty else -volume
        elif wave_type == "triangle":
            if phase < 0.5:
                val = volume * (4 * phase - 1)
            else:
                val = volume * (3 - 4 * phase)
        elif wave_type == "sawtooth":
            val = volume * (2 * phase - 1)
        elif wave_type == "noise":
            # Pseudo-noise using a simple hash
            val = volume * (((i * 1103515245 + 12345) >> 16 & 0x7FFF) / 16384.0 - 1)
        elif wave_type == "sine":
            val = volume * math.sin(2 * math.pi * phase)
        else:
            val = 0

        # Apply a simple envelope (attack/release to avoid clicks)
        env = 1.0
        attack = min(n_samples, int(SAMPLE_RATE * 0.005))
        release = min(n_samples, int(SAMPLE_RATE * 0.01))
        if i < attack:
            env = i / attack
        elif i > n_samples - release:
            env = (n_samples - i) / release
        val *= env

        samples.append(int(max(-32767, min(32767, val * 32767))))

    return samples


def _samples_to_sound(samples):
    """Convert a list of 16-bit samples to a pygame Sound object."""
    # The mixer may run in stereo even if we request mono, so duplicate
    # each sample into left+right channels to ensure correct playback speed.
    freq, fmt, channels = pygame.mixer.get_init()
    if channels == 2:
        stereo = array.array('h')
        for s in samples:
            stereo.append(s)
            stereo.append(s)
        raw = stereo
    else:
        raw = array.array('h', samples)
    sound = pygame.mixer.Sound(buffer=raw)
    return sound


def _mix_samples(*sample_lists):
    """Mix multiple sample lists together."""
    max_len = max(len(s) for s in sample_lists)
    mixed = [0] * max_len
    for slist in sample_lists:
        for i, val in enumerate(slist):
            mixed[i] += val
    # Clamp
    for i in range(len(mixed)):
        mixed[i] = max(-32767, min(32767, mixed[i]))
    return mixed


# Note frequencies (4th octave base)
NOTE_FREQS = {
    'C3': 130.81, 'Db3': 138.59, 'D3': 146.83, 'Eb3': 155.56,
    'E3': 164.81, 'F3': 174.61, 'Gb3': 185.00, 'G3': 196.00,
    'Ab3': 207.65, 'A3': 220.00, 'Bb3': 233.08, 'B3': 246.94,
    'C4': 261.63, 'Db4': 277.18, 'D4': 293.66, 'Eb4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'Gb4': 369.99, 'G4': 392.00,
    'Ab4': 415.30, 'A4': 440.00, 'Bb4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'Db5': 554.37, 'D5': 587.33, 'Eb5': 622.25,
    'E5': 659.26, 'F5': 698.46, 'Gb5': 739.99, 'G5': 783.99,
    'Ab5': 830.61, 'A5': 880.00, 'Bb5': 932.33, 'B5': 987.77,
    'R': 0,  # Rest
}
# Aliases for sharps
NOTE_FREQS['C#3'] = NOTE_FREQS['Db3']
NOTE_FREQS['F#3'] = NOTE_FREQS['Gb3']
NOTE_FREQS['G#3'] = NOTE_FREQS['Ab3']
NOTE_FREQS['C#4'] = NOTE_FREQS['Db4']
NOTE_FREQS['F#4'] = NOTE_FREQS['Gb4']
NOTE_FREQS['G#4'] = NOTE_FREQS['Ab4']
NOTE_FREQS['C#5'] = NOTE_FREQS['Db5']
NOTE_FREQS['F#5'] = NOTE_FREQS['Gb5']
NOTE_FREQS['G#5'] = NOTE_FREQS['Ab5']


def _render_melody(notes, wave="square", vol=0.2, bpm=130):
    """Render a list of (note_name, duration_beats) at given BPM to samples."""
    beat_dur = 60.0 / bpm
    all_samples = []
    for note, beats in notes:
        dur = beats * beat_dur
        freq = NOTE_FREQS.get(note, 0)
        if freq > 0:
            s = _generate_wave(freq, dur, wave, vol)
        else:
            s = [0] * int(SAMPLE_RATE * dur)
        all_samples.extend(s)
    return all_samples


def _render_drums(pattern, beats, bpm=130):
    """Render a drum pattern. Pattern is list of (beat_position, drum_type)."""
    beat_dur = 60.0 / bpm
    total_dur = beats * beat_dur
    total_samples = int(SAMPLE_RATE * total_dur)
    result = [0] * total_samples

    for beat_pos, drum in pattern:
        start = int(beat_pos * beat_dur * SAMPLE_RATE)
        if drum == "kick":
            # Short low sine sweep
            dur = 0.08
            for i in range(min(int(SAMPLE_RATE * dur), total_samples - start)):
                t = i / SAMPLE_RATE
                freq = 150 * math.exp(-t * 30)
                val = int(0.4 * 32767 * math.sin(2 * math.pi * freq * t) * max(0, 1 - t / dur))
                idx = start + i
                if idx < total_samples:
                    result[idx] = max(-32767, min(32767, result[idx] + val))
        elif drum == "snare":
            dur = 0.06
            for i in range(min(int(SAMPLE_RATE * dur), total_samples - start)):
                t = i / SAMPLE_RATE
                noise = ((i * 1103515245 + 12345) >> 16 & 0x7FFF) / 16384.0 - 1
                val = int(0.25 * 32767 * noise * max(0, 1 - t / dur))
                idx = start + i
                if idx < total_samples:
                    result[idx] = max(-32767, min(32767, result[idx] + val))
        elif drum == "hat":
            dur = 0.03
            for i in range(min(int(SAMPLE_RATE * dur), total_samples - start)):
                t = i / SAMPLE_RATE
                noise = ((i * 7919 + 104729) >> 8 & 0x7FFF) / 16384.0 - 1
                val = int(0.12 * 32767 * noise * max(0, 1 - t / dur))
                idx = start + i
                if idx < total_samples:
                    result[idx] = max(-32767, min(32767, result[idx] + val))

    return result


def _build_town_music():
    """Build the town theme — chill boom bap groove at 100 BPM.

    Chord progression: C# - A - F# - Ab (each chord = 2 bars = 8 beats).
    32-beat loop total. Melody over C#/Db minor pentatonic.
    """
    bpm = 100
    total_beats = 32  # 4 chords x 2 bars x 4 beats

    # === CHORD PAD (square wave, low duty for thin tone) ===
    # C# maj: C#-F(E#)-G#  |  A maj: A-C#-E  |  F# maj: F#-Bb(A#)-C#  |  Ab maj: Ab-C-Eb
    pad_notes = [
        # C# chord - 8 beats
        ('Db4', 2.0), ('F4', 2.0), ('Ab4', 2.0), ('Db4', 2.0),
        # A chord - 8 beats
        ('A3', 2.0), ('Db4', 2.0), ('E4', 2.0), ('A3', 2.0),
        # F# chord - 8 beats
        ('Gb4', 2.0), ('Bb4', 2.0), ('Db4', 2.0), ('Gb4', 2.0),
        # Ab chord - 8 beats
        ('Ab3', 2.0), ('C4', 2.0), ('Eb4', 2.0), ('Ab3', 2.0),
    ]
    pad_samples = _render_melody(pad_notes, "square", 0.08, bpm)

    # === BASSLINE (triangle wave — deep and bouncy) ===
    # Follows chord roots with rhythmic hits
    bass = [
        # C# bars (8 beats)
        ('Db3', 0.75), ('R', 0.25), ('Db3', 0.5), ('R', 0.25), ('Db3', 0.25),
        ('Ab3', 0.5), ('R', 0.5), ('Db3', 0.75), ('R', 0.25),
        ('Db3', 0.5), ('R', 0.25), ('Ab3', 0.25), ('Db3', 0.5), ('R', 0.5),
        ('Db3', 0.75), ('R', 0.25), ('Ab3', 0.5), ('R', 0.5),
        # A bars (8 beats)
        ('A3', 0.75), ('R', 0.25), ('A3', 0.5), ('R', 0.25), ('A3', 0.25),
        ('E3', 0.5), ('R', 0.5), ('A3', 0.75), ('R', 0.25),
        ('A3', 0.5), ('R', 0.25), ('E3', 0.25), ('A3', 0.5), ('R', 0.5),
        ('A3', 0.75), ('R', 0.25), ('E3', 0.5), ('R', 0.5),
        # F# bars (8 beats)
        ('Gb3', 0.75), ('R', 0.25), ('Gb3', 0.5), ('R', 0.25), ('Gb3', 0.25),
        ('Db3', 0.5), ('R', 0.5), ('Gb3', 0.75), ('R', 0.25),
        ('Gb3', 0.5), ('R', 0.25), ('Db3', 0.25), ('Gb3', 0.5), ('R', 0.5),
        ('Gb3', 0.75), ('R', 0.25), ('Db3', 0.5), ('R', 0.5),
        # Ab bars (8 beats)
        ('Ab3', 0.75), ('R', 0.25), ('Ab3', 0.5), ('R', 0.25), ('Ab3', 0.25),
        ('Eb3', 0.5), ('R', 0.5), ('Ab3', 0.75), ('R', 0.25),
        ('Ab3', 0.5), ('R', 0.25), ('Eb3', 0.25), ('Ab3', 0.5), ('R', 0.5),
        ('Ab3', 0.75), ('R', 0.25), ('Eb3', 0.5), ('R', 0.5),
    ]
    bass_samples = _render_melody(bass, "triangle", 0.22, bpm)

    # === MELODY (square wave lead — Db minor pentatonic: Db Fb(E) Gb Ab Cb(B)) ===
    melody = [
        # Over C# — opening phrase (8 beats)
        ('Db5', 0.5), ('R', 0.25), ('B4', 0.25), ('Ab4', 0.5), ('R', 0.25),
        ('Gb4', 0.75), ('Ab4', 0.5), ('Db5', 0.5), ('R', 0.5),
        ('B4', 0.5), ('Ab4', 0.25), ('Gb4', 0.5), ('R', 0.25),
        ('Ab4', 0.75), ('R', 0.25), ('Gb4', 0.5), ('R', 0.25),
        ('Db5', 0.5), ('R', 0.5),
        # Over A — descending answer (8 beats)
        ('E4', 0.5), ('R', 0.25), ('Db4', 0.25), ('E4', 0.5), ('Gb4', 0.5),
        ('R', 0.25), ('Ab4', 0.75), ('Gb4', 0.5), ('E4', 0.25),
        ('Db4', 0.5), ('R', 0.25), ('E4', 0.75), ('R', 0.25),
        ('Db4', 0.5), ('R', 0.25), ('E4', 0.5), ('R', 0.25),
        ('Db4', 0.5), ('R', 0.5),
        # Over F# — rising energy (8 beats)
        ('Gb4', 0.5), ('Ab4', 0.25), ('B4', 0.5), ('R', 0.25),
        ('Db5', 0.75), ('B4', 0.5), ('Ab4', 0.25), ('Gb4', 0.5),
        ('R', 0.25), ('Ab4', 0.5), ('B4', 0.25), ('Db5', 0.5),
        ('R', 0.25), ('B4', 0.75), ('R', 0.25), ('Ab4', 0.5),
        ('Gb4', 0.5), ('R', 0.5),
        # Over Ab — resolving phrase (8 beats)
        ('Ab4', 0.5), ('R', 0.25), ('Gb4', 0.25), ('E4', 0.5), ('Gb4', 0.5),
        ('R', 0.25), ('Ab4', 0.75), ('Db5', 0.5), ('B4', 0.25),
        ('Ab4', 0.5), ('R', 0.25), ('Gb4', 0.5), ('R', 0.25),
        ('Db4', 0.5), ('R', 0.25), ('Db4', 1.0),
        ('R', 0.5), ('Db4', 0.5),
    ]
    melody_samples = _render_melody(melody, "square", 0.14, bpm)

    # Pad all tracks to same length
    target_len = int(SAMPLE_RATE * total_beats * 60.0 / bpm)
    for samples in [pad_samples, bass_samples, melody_samples]:
        if len(samples) < target_len:
            samples.extend([0] * (target_len - len(samples)))
    pad_samples = pad_samples[:target_len]
    bass_samples = bass_samples[:target_len]
    melody_samples = melody_samples[:target_len]

    # === DRUMS (boom bap — kick on 1 and the "and" of 2, snare on 2 and 4) ===
    drum_pattern_one_bar = []
    # Hi-hats on eighth notes
    for i in range(8):
        drum_pattern_one_bar.append((i * 0.5, "hat"))
    # Boom bap kick/snare
    drum_pattern_one_bar.extend([
        (0, "kick"), (1.5, "kick"), (2.75, "kick"),
        (1, "snare"), (3, "snare"),
    ])

    full_drums = []
    bar_offset = 0
    while bar_offset < total_beats:
        for beat_pos, drum in drum_pattern_one_bar:
            full_drums.append((bar_offset + beat_pos, drum))
        bar_offset += 4

    drum_samples = _render_drums(full_drums, total_beats, bpm)
    drum_samples = drum_samples[:target_len]
    if len(drum_samples) < target_len:
        drum_samples.extend([0] * (target_len - len(drum_samples)))

    # === MIX ===
    mixed = _mix_samples(melody_samples, bass_samples, pad_samples, drum_samples)
    return _samples_to_sound(mixed)


def _build_battle_music():
    """Build battle theme — intense, driving 8-bit track."""
    melody = [
        ('E4', 0.25), ('E4', 0.25), ('R', 0.25), ('E4', 0.25),
        ('R', 0.25), ('C4', 0.25), ('E4', 0.5),
        ('G4', 0.5), ('R', 0.5), ('G3', 0.5), ('R', 0.5),
        ('C4', 0.5), ('R', 0.25), ('G3', 0.5), ('R', 0.25),
        ('E3', 0.5), ('R', 0.25), ('A3', 0.5), ('B3', 0.5),
        ('Bb3', 0.25), ('A3', 0.5), ('G3', 0.5), ('E4', 0.5),
        ('G4', 0.25), ('A4', 0.5), ('F4', 0.25), ('G4', 0.25),
        ('R', 0.25), ('E4', 0.5), ('C4', 0.25), ('D4', 0.25), ('B3', 0.5),
    ]
    melody_samples = _render_melody(melody, "square", 0.15)

    bass = [
        ('C3', 0.5), ('C3', 0.25), ('C3', 0.25), ('G3', 0.5), ('G3', 0.5),
        ('C3', 0.5), ('R', 0.25), ('E3', 0.5), ('G3', 0.25), ('C3', 0.5),
        ('A3', 0.5), ('R', 0.25), ('G3', 0.5), ('E3', 0.25), ('C3', 0.5),
        ('G3', 0.5), ('C3', 0.5), ('R', 0.5),
    ]
    bass_samples = _render_melody(bass, "triangle", 0.2)
    bass_samples = bass_samples[:len(melody_samples)]
    if len(bass_samples) < len(melody_samples):
        bass_samples.extend([0] * (len(melody_samples) - len(bass_samples)))

    total_beats = sum(b for _, b in melody)
    drum_pattern = []
    bar = 0
    while bar < total_beats:
        for i in range(8):
            drum_pattern.append((bar + i * 0.25, "hat"))
        drum_pattern.extend([
            (bar, "kick"), (bar + 0.75, "kick"), (bar + 1.5, "kick"), (bar + 2.5, "kick"),
            (bar + 0.5, "snare"), (bar + 1.5, "snare"), (bar + 2.5, "snare"), (bar + 3.5, "snare"),
        ])
        bar += 4
    drum_samples = _render_drums(drum_pattern, total_beats)
    drum_samples = drum_samples[:len(melody_samples)]
    if len(drum_samples) < len(melody_samples):
        drum_samples.extend([0] * (len(melody_samples) - len(drum_samples)))

    mixed = _mix_samples(melody_samples, bass_samples, drum_samples)
    return _samples_to_sound(mixed)


def _build_title_music():
    """Build title screen theme — majestic, mysterious opening."""
    melody = [
        ('G4', 1.0), ('Bb4', 0.5), ('D5', 1.0), ('C5', 0.5),
        ('Bb4', 1.0), ('G4', 0.5), ('F4', 1.0), ('R', 0.5),
        ('G4', 0.5), ('Bb4', 0.5), ('C5', 1.0), ('Bb4', 0.5),
        ('G4', 1.0), ('F4', 0.5), ('G4', 1.5), ('R', 0.5),
        ('D5', 1.0), ('C5', 0.5), ('Bb4', 0.5), ('G4', 0.5),
        ('Bb4', 1.0), ('C5', 0.5), ('D5', 1.5), ('R', 0.5),
    ]
    melody_samples = _render_melody(melody, "triangle", 0.18)

    # Slow pad-like chords underneath
    pad = [
        ('G3', 2.0), ('Bb3', 2.0), ('C4', 2.0), ('G3', 2.0),
        ('F3', 2.0), ('G3', 2.0), ('Bb3', 2.0), ('G3', 2.0),
    ]
    pad_samples = _render_melody(pad, "sine", 0.1)
    pad_samples = pad_samples[:len(melody_samples)]
    if len(pad_samples) < len(melody_samples):
        pad_samples.extend([0] * (len(melody_samples) - len(pad_samples)))

    mixed = _mix_samples(melody_samples, pad_samples)
    return _samples_to_sound(mixed)


def _build_forest_music():
    """Build forest theme — eerie, atmospheric 8-bit ambient."""
    melody = [
        ('E4', 1.0), ('G4', 0.5), ('A4', 1.0), ('G4', 0.5),
        ('E4', 1.0), ('D4', 0.5), ('C4', 1.0), ('R', 0.5),
        ('E4', 0.5), ('G4', 0.5), ('B4', 1.0), ('A4', 0.5),
        ('G4', 1.0), ('E4', 0.5), ('D4', 1.5), ('R', 0.5),
    ]
    melody_samples = _render_melody(melody, "triangle", 0.12)

    bass = [
        ('C3', 2.0), ('E3', 2.0), ('A3', 2.0), ('E3', 2.0),
    ]
    bass_samples = _render_melody(bass, "sine", 0.1)
    bass_samples = bass_samples[:len(melody_samples)]
    if len(bass_samples) < len(melody_samples):
        bass_samples.extend([0] * (len(melody_samples) - len(bass_samples)))

    mixed = _mix_samples(melody_samples, bass_samples)
    return _samples_to_sound(mixed)


class MusicManager:
    """Manages procedurally generated chiptune background music."""

    def __init__(self):
        try:
            # Quit any mixer already started by pygame.init() so we can
            # reinitialise at our exact sample rate.  Without this the
            # mixer may stay at 44100 Hz while we generate at 22050,
            # causing 2x playback speed.
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=CHANNELS, buffer=2048)
        except pygame.error:
            self._enabled = False
            return

        self._enabled = True
        self._tracks = {}
        self._current = None
        self._channel = None

    def _ensure_track(self, name):
        """Lazily generate tracks on first use."""
        if name in self._tracks:
            return
        builders = {
            "title": _build_title_music,
            "town": _build_town_music,
            "forest": _build_forest_music,
            "battle": _build_battle_music,
        }
        builder = builders.get(name)
        if builder:
            self._tracks[name] = builder()

    def play(self, track_name):
        """Play a named track, looping. No-op if already playing."""
        if not self._enabled:
            return
        if self._current == track_name:
            return

        self._ensure_track(track_name)
        sound = self._tracks.get(track_name)
        if not sound:
            return

        # Stop current
        if self._channel:
            self._channel.stop()

        self._channel = sound.play(loops=-1)
        if self._channel:
            self._channel.set_volume(0.4)
        self._current = track_name

    def stop(self):
        """Stop all music."""
        if self._channel:
            self._channel.stop()
        self._current = None
