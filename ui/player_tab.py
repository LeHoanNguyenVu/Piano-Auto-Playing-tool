"""
Player Tab — Main MIDI player interface with controls, progress, and console log.
"""

import os
import customtkinter as ctk
from tkinter import filedialog
from ui import theme as T
from core.midi_parser import parse_midi, get_song_info, get_piano_tracks
from core.playback_engine import PlaybackEngine
from core.key_mapping import get_note_name


class PlayerTab(ctk.CTkFrame):
    """Main player tab with file selection, playback controls, and console."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.engine = PlaybackEngine()
        self._current_file = None
        self._song_info = None

        # Wire engine callbacks
        self.engine.on_progress = self._on_progress
        self.engine.on_note = self._on_note
        self.engine.on_finished = self._on_finished
        self.engine.on_log = self._on_log
        self.engine.on_countdown = self._on_countdown

        self._build_ui()

    def _build_ui(self):
        # ─── Header ───────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text="🎹 MIDI Player", font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        self._status_label = ctk.CTkLabel(header, text="No file loaded",
                                           font=T.FONT_SMALL, text_color=T.TEXT_MUTED)
        self._status_label.pack(side="right")

        # ─── File Selection ───────────────────────────────
        file_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        file_frame.pack(fill="x", padx=20, pady=(0, 10))

        file_inner = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_inner.pack(fill="x", padx=15, pady=12)

        self._file_label = ctk.CTkLabel(
            file_inner, text="No MIDI file selected",
            font=T.FONT_BODY, text_color=T.TEXT_SECONDARY, anchor="w"
        )
        self._file_label.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            file_inner, text="📂 Open MIDI", width=120, height=32,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._open_file
        ).pack(side="right", padx=(10, 0))

        # ─── Song Info ────────────────────────────────────
        self._info_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        self._info_frame.pack(fill="x", padx=20, pady=(0, 10))

        info_inner = ctk.CTkFrame(self._info_frame, fg_color="transparent")
        info_inner.pack(fill="x", padx=15, pady=10)

        self._info_labels = {}
        for col, key in enumerate(["Duration", "Notes", "Tempo", "Range"]):
            frame = ctk.CTkFrame(info_inner, fg_color="transparent")
            frame.pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(frame, text=key, font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack()
            lbl = ctk.CTkLabel(frame, text="—", font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY)
            lbl.pack()
            self._info_labels[key] = lbl

        # ─── Track Selection ─────────────────────────────
        self._track_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        # Hidden by default, shown when file has multiple tracks

        track_inner = ctk.CTkFrame(self._track_frame, fg_color="transparent")
        track_inner.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(track_inner, text="Track:", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY).pack(side="left")
        self._track_var = ctk.StringVar(value="All Tracks")
        self._track_menu = ctk.CTkOptionMenu(
            track_inner, variable=self._track_var, values=["All Tracks"],
            width=250, height=28, font=T.FONT_SMALL,
            fg_color=T.BG_ELEVATED, button_color=T.ACCENT, button_hover_color=T.ACCENT_HOVER,
            command=self._on_track_change
        )
        self._track_menu.pack(side="left", padx=(10, 0))

        # ─── Progress Bar ─────────────────────────────────
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=(0, 5))

        self._progress_bar = ctk.CTkProgressBar(
            progress_frame, height=6, corner_radius=3,
            fg_color=T.PROGRESS_BG, progress_color=T.ACCENT
        )
        self._progress_bar.pack(fill="x")
        self._progress_bar.set(0)

        time_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_frame.pack(fill="x", padx=20, pady=(0, 10))

        self._time_current = ctk.CTkLabel(time_frame, text="0:00", font=T.FONT_TINY,
                                           text_color=T.TEXT_MUTED)
        self._time_current.pack(side="left")
        self._time_total = ctk.CTkLabel(time_frame, text="0:00", font=T.FONT_TINY,
                                         text_color=T.TEXT_MUTED)
        self._time_total.pack(side="right")
        self._notes_progress = ctk.CTkLabel(time_frame, text="", font=T.FONT_TINY,
                                             text_color=T.TEXT_ACCENT)
        self._notes_progress.pack()

        # ─── Playback Controls ────────────────────────────
        controls = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        controls.pack(fill="x", padx=20, pady=(0, 10))

        ctrl_inner = ctk.CTkFrame(controls, fg_color="transparent")
        ctrl_inner.pack(pady=12)

        btn_style = dict(width=80, height=36, font=T.FONT_BODY_BOLD,
                         corner_radius=T.BUTTON_CORNER)

        self._play_btn = ctk.CTkButton(
            ctrl_inner, text="▶  Play", fg_color=T.SUCCESS,
            hover_color="#16a34a", command=self._play, **btn_style
        )
        self._play_btn.pack(side="left", padx=5)

        self._pause_btn = ctk.CTkButton(
            ctrl_inner, text="⏸  Pause", fg_color=T.WARNING,
            hover_color="#d97706", command=self._pause, **btn_style
        )
        self._pause_btn.pack(side="left", padx=5)

        self._stop_btn = ctk.CTkButton(
            ctrl_inner, text="⏹  Stop", fg_color=T.ERROR,
            hover_color="#dc2626", command=self._stop, **btn_style
        )
        self._stop_btn.pack(side="left", padx=5)

        # Speed slider
        speed_frame = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        speed_frame.pack(side="left", padx=(20, 5))

        ctk.CTkLabel(speed_frame, text="Speed", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack()
        self._speed_label = ctk.CTkLabel(speed_frame, text="100%", font=T.FONT_SMALL,
                                          text_color=T.TEXT_ACCENT)
        self._speed_label.pack()

        self._speed_slider = ctk.CTkSlider(
            ctrl_inner, from_=25, to=300, number_of_steps=55,
            width=120, height=16, fg_color=T.PROGRESS_BG,
            progress_color=T.ACCENT, button_color=T.ACCENT_LIGHT,
            command=self._on_speed_change
        )
        self._speed_slider.set(100)
        self._speed_slider.pack(side="left", padx=(0, 15))

        # Transpose
        tp_frame = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        tp_frame.pack(side="left", padx=5)

        ctk.CTkLabel(tp_frame, text="Transpose", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack()
        self._transpose_label = ctk.CTkLabel(tp_frame, text="0", font=T.FONT_SMALL,
                                              text_color=T.TEXT_ACCENT)
        self._transpose_label.pack()

        self._transpose_slider = ctk.CTkSlider(
            ctrl_inner, from_=-24, to=24, number_of_steps=48,
            width=100, height=16, fg_color=T.PROGRESS_BG,
            progress_color=T.ACCENT, button_color=T.ACCENT_LIGHT,
            command=self._on_transpose_change
        )
        self._transpose_slider.set(0)
        self._transpose_slider.pack(side="left")

        # ─── Delay Setting ────────────────────────────────
        delay_frame = ctk.CTkFrame(self, fg_color="transparent")
        delay_frame.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(delay_frame, text="Start delay:", font=T.FONT_SMALL,
                      text_color=T.TEXT_SECONDARY).pack(side="left")
        self._delay_var = ctk.StringVar(value="3")
        delay_entry = ctk.CTkEntry(
            delay_frame, textvariable=self._delay_var, width=40, height=26,
            font=T.FONT_SMALL, fg_color=T.BG_ELEVATED, border_color=T.BORDER
        )
        delay_entry.pack(side="left", padx=5)
        ctk.CTkLabel(delay_frame, text="seconds  (time to switch to Roblox)",
                      font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left")

        # ─── Console Log ──────────────────────────────────
        console_frame = ctk.CTkFrame(self, fg_color=T.CONSOLE_BG, corner_radius=T.CORNER_RADIUS)
        console_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        console_header = ctk.CTkFrame(console_frame, fg_color="transparent")
        console_header.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(console_header, text="Console", font=T.FONT_TINY,
                      text_color=T.TEXT_MUTED).pack(side="left")

        self._console = ctk.CTkTextbox(
            console_frame, height=100, font=T.FONT_MONO_SMALL,
            fg_color=T.CONSOLE_BG, text_color=T.TEXT_SECONDARY,
            border_width=0, activate_scrollbars=True, wrap="word"
        )
        self._console.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self._console.configure(state="disabled")

        self._log("Ready. Open a MIDI file or select from Library.")
        self._log("Hotkeys: F5 = Play | F6 = Pause/Resume | F7 = Stop")

    # ─── File Operations ──────────────────────────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Open MIDI File",
            filetypes=[("MIDI Files", "*.mid *.midi"), ("All Files", "*.*")]
        )
        if path:
            self.load_file(path)

    def load_file(self, path):
        """Load a MIDI file for playback."""
        if not os.path.exists(path):
            self._log(f"✗ File not found: {path}")
            return

        self._current_file = path
        self._song_info = get_song_info(path)
        info = self._song_info

        # Update UI
        display_name = info.title or os.path.basename(path)
        self._file_label.configure(text=f"♪ {display_name}")
        self._status_label.configure(text="File loaded", text_color=T.SUCCESS)

        # Update info labels
        mins, secs = divmod(int(info.duration), 60)
        self._info_labels["Duration"].configure(text=f"{mins}:{secs:02d}")
        self._info_labels["Notes"].configure(text=str(info.note_count))
        self._info_labels["Tempo"].configure(text=f"{info.tempo_bpm} BPM")

        if info.note_count > 0:
            self._info_labels["Range"].configure(
                text=f"{get_note_name(info.min_note)} — {get_note_name(info.max_note)}"
            )
        else:
            self._info_labels["Range"].configure(text="—")

        self._time_total.configure(text=f"{mins}:{secs:02d}")

        # Check for multiple tracks
        tracks = get_piano_tracks(path)
        if len(tracks) > 1:
            values = ["All Tracks"] + [f"Track {t[0]}: {t[1]} ({t[2]} notes)" for t in tracks]
            self._track_menu.configure(values=values)
            self._track_var.set("All Tracks")
            self._track_frame.pack(fill="x", padx=20, pady=(0, 10), after=self._info_frame)
        else:
            self._track_frame.pack_forget()

        # Parse and load into engine
        self._parse_and_load()
        self._log(f"✓ Loaded: {display_name} ({info.note_count} notes, {mins}:{secs:02d})")

    def _parse_and_load(self, track_index=None):
        """Parse current file and load into playback engine."""
        if not self._current_file:
            return
        events = parse_midi(self._current_file, track_index)
        self.engine.load(events)
        self._progress_bar.set(0)
        self._time_current.configure(text="0:00")
        self._notes_progress.configure(text="")

    def _on_track_change(self, selection):
        if selection == "All Tracks":
            self._parse_and_load(None)
        else:
            # Extract track index from "Track X: ..."
            try:
                idx = int(selection.split(":")[0].replace("Track", "").strip())
                self._parse_and_load(idx)
            except ValueError:
                self._parse_and_load(None)

    # ─── Playback Controls ────────────────────────────────
    def _play(self):
        if self.engine.is_playing:
            if self.engine.is_paused:
                self.engine.resume()
                self._status_label.configure(text="Playing", text_color=T.SUCCESS)
        else:
            try:
                delay = float(self._delay_var.get())
            except ValueError:
                delay = 3.0
            self.engine.start_delay = delay
            self.engine.play()
            self._status_label.configure(text="Playing", text_color=T.SUCCESS)

    def _pause(self):
        if self.engine.is_playing:
            self.engine.toggle_pause()
            if self.engine.is_paused:
                self._status_label.configure(text="Paused", text_color=T.WARNING)
            else:
                self._status_label.configure(text="Playing", text_color=T.SUCCESS)

    def _stop(self):
        self.engine.stop()
        self._status_label.configure(text="Stopped", text_color=T.TEXT_MUTED)
        self._progress_bar.set(0)
        self._time_current.configure(text="0:00")
        self._notes_progress.configure(text="")

    def _on_speed_change(self, value):
        speed = int(value)
        self._speed_label.configure(text=f"{speed}%")
        self.engine.speed = speed / 100.0

    def _on_transpose_change(self, value):
        tp = int(value)
        self._transpose_label.configure(text=f"{tp:+d}" if tp != 0 else "0")
        self.engine.transpose = tp

    # ─── Engine Callbacks (called from engine thread) ─────
    def _on_progress(self, current, total, idx, total_events):
        try:
            self.after(0, self._update_progress, current, total, idx, total_events)
        except Exception:
            pass

    def _update_progress(self, current, total, idx, total_events):
        if total > 0:
            self._progress_bar.set(current / total)
        mins, secs = divmod(int(current), 60)
        self._time_current.configure(text=f"{mins}:{secs:02d}")
        self._notes_progress.configure(text=f"{idx}/{total_events} notes")

    def _on_note(self, midi_note, key_char):
        pass  # Could add visual feedback here

    def _on_countdown(self, seconds):
        try:
            self.after(0, self._update_countdown, seconds)
        except Exception:
            pass

    def _update_countdown(self, seconds):
        if seconds > 0:
            self._status_label.configure(text=f"Starting in {seconds}s...",
                                          text_color=T.WARNING)
        else:
            self._status_label.configure(text="▶ Playing", text_color=T.SUCCESS)

    def _on_finished(self):
        try:
            self.after(0, self._handle_finished)
        except Exception:
            pass

    def _handle_finished(self):
        self._status_label.configure(text="Finished", text_color=T.TEXT_ACCENT)
        self._progress_bar.set(1.0)

    def _on_log(self, msg):
        try:
            self.after(0, self._append_log, msg)
        except Exception:
            pass

    # ─── Console ──────────────────────────────────────────
    def _log(self, msg):
        self._append_log(msg)

    def _append_log(self, msg):
        self._console.configure(state="normal")
        self._console.insert("end", f"{msg}\n")
        self._console.see("end")
        self._console.configure(state="disabled")
