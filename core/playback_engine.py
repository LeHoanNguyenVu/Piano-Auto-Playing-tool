"""
Playback Engine — High-precision MIDI playback with zero-drift timing.

Uses time.perf_counter() for microsecond precision and absolute time tracking
to prevent timing drift over long playback sessions.
"""

import time
import threading
from core.key_mapping import get_key_for_note, clamp_to_range, MIDI_TO_KEY
from core.key_simulator import press_key, release_key, release_all


class PlaybackEngine:
    """
    Plays parsed MIDI note events by simulating keyboard input.

    Features:
    - Zero-drift timing using absolute time references
    - Adjustable speed (25% to 300%)
    - Transpose support (-24 to +24 semitones)
    - Start delay for switching to game window
    - True note holding using note_on and note_off events
    """

    def __init__(self):
        self._events = []
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially

        # Playback settings
        self.speed = 1.0          # 1.0 = normal speed
        self.transpose = 0        # Semitones to shift
        self.start_delay = 3.0    # Seconds before playback starts
        self.auto_clamp = True    # Auto-clamp notes to playable range

        # Callbacks
        self.on_progress = None   # (current_time, total_time, event_index, total_events)
        self.on_note = None       # (midi_note, key_char)
        self.on_finished = None   # ()
        self.on_log = None        # (message)
        self.on_countdown = None  # (seconds_remaining)

        # State
        self._is_playing = False
        self._is_paused = False
        self._current_index = 0
        self._total_duration = 0.0

    @property
    def is_playing(self):
        return self._is_playing

    @property
    def is_paused(self):
        return self._is_paused

    def load(self, events):
        """Load a list of NoteEvent objects for playback."""
        # Include both note_on (velocity > 0) and note_off (velocity == 0) events
        self._events = events
        if self._events:
            self._total_duration = self._events[-1].time
        else:
            self._total_duration = 0.0
        self._current_index = 0
        
        # Count actual notes (note_on events) for logging
        note_on_count = sum(1 for e in self._events if e.velocity > 0)
        self._log(f"Loaded {note_on_count} notes, duration: {self._total_duration:.1f}s")

    def play(self):
        """Start playback in a background thread."""
        if self._is_playing:
            return
        if not self._events:
            self._log("No notes loaded!")
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._is_playing = True
        self._is_paused = False
        self._current_index = 0

        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()

    def pause(self):
        """Pause playback."""
        if self._is_playing and not self._is_paused:
            self._is_paused = True
            self._pause_event.clear()
            release_all()  # Release all keys when paused
            self._log("Paused")

    def resume(self):
        """Resume paused playback."""
        if self._is_playing and self._is_paused:
            self._is_paused = False
            self._pause_event.set()
            self._log("Resumed")

    def toggle_pause(self):
        """Toggle between paused and playing."""
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def stop(self):
        """Stop playback completely."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        self._is_playing = False
        self._is_paused = False
        
        # Release all held keys to prevent stuck notes
        release_all()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._log("Stopped")

    def _log(self, msg):
        if self.on_log:
            self.on_log(msg)

    def _playback_loop(self):
        """Main playback loop running on a dedicated thread."""
        events = self._events
        total_events = len(events)
        speed = self.speed
        transpose = self.transpose

        # ── Countdown ──────────────────────────────────────────
        self._log(f"Starting in {self.start_delay:.0f}s — switch to Roblox now!")
        countdown = self.start_delay
        while countdown > 0:
            if self._stop_event.is_set():
                self._is_playing = False
                return
            if self.on_countdown:
                self.on_countdown(int(countdown))
            time.sleep(1.0)
            countdown -= 1.0

        if self.on_countdown:
            self.on_countdown(0)

        self._log(f"▶ Playing at {speed*100:.0f}% speed, transpose: {transpose:+d}")

        # ── Main playback ─────────────────────────────────────
        start_time = time.perf_counter()
        idx = 0
        while idx < total_events:
            if self._stop_event.is_set():
                break

            # Process current event
            event = events[idx]
            target_time = start_time + (event.time / speed)

            # Wait until target time (responsive to pause/stop)
            while True:
                if self._stop_event.is_set():
                    break
                
                # Handle pause
                if not self._pause_event.is_set():
                    pause_start = time.perf_counter()
                    release_all()
                    self._pause_event.wait()
                    # Shift start_time by the duration of the pause
                    start_time += time.perf_counter() - pause_start
                    target_time = start_time + (event.time / speed)

                now = time.perf_counter()
                wait_time = target_time - now
                
                if wait_time <= 0:
                    break
                
                # Sleep in small increments to remain responsive, or spin-wait for precision
                if wait_time > 0.005:
                    time.sleep(min(wait_time - 0.002, 0.01))
                else:
                    # Final precision spin-wait
                    while time.perf_counter() < target_time and self._pause_event.is_set() and not self._stop_event.is_set():
                        pass
                    break

            if self._stop_event.is_set():
                break

            # Execute event
            note = event.note
            if self.auto_clamp:
                note = clamp_to_range(note, transpose)
            else:
                note = note + transpose

            key = MIDI_TO_KEY.get(note)
            if key:
                if event.velocity > 0:
                    # Note On
                    press_key(key)
                    if self.on_note:
                        self.on_note(note, key)
                else:
                    # Note Off
                    release_key(key)

            idx += 1

            # Progress callback
            self._current_index = idx
            if self.on_progress:
                current_time = event.time
                self.on_progress(current_time, self._total_duration, idx, total_events)

        # ── Finished ──────────────────────────────────────────
        release_all()
        self._is_playing = False
        self._is_paused = False
        self._log("✓ Playback finished")
        if self.on_finished:
            self.on_finished()
