"""
Player Tab — Main MIDI player interface with controls, progress, and console log.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from ui import theme as T
from core.midi_parser import parse_midi, get_song_info
from core.playback_engine import PlaybackEngine
from core.key_mapping import get_note_name


class PlayerTab(ctk.CTkFrame):
    """Main player tab with file selection, playback controls, and console."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.engine = PlaybackEngine()
        self._current_file = None
        self._current_song_id = None
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

        ctk.CTkLabel(header, text="🎹 " + T.L("player"), font=T.FONT_TITLE,
                      text_color=T.TEXT_PRIMARY).pack(side="left")

        self._status_label = ctk.CTkLabel(header, text="...",
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
            file_inner, text=T.L("open_midi"), width=120, height=32,
            font=T.FONT_BODY_BOLD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            corner_radius=T.BUTTON_CORNER, command=self._open_file
        ).pack(side="right", padx=(10, 0))

        # ─── Song Info ────────────────────────────────────
        self._info_frame = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        self._info_frame.pack(fill="x", padx=20, pady=(0, 10))

        info_inner = ctk.CTkFrame(self._info_frame, fg_color="transparent")
        info_inner.pack(fill="x", padx=15, pady=10)

        self._info_labels = {}
        info_keys = [("duration", "Duration"), ("notes", "Notes"), ("tempo", "Tempo"), ("range", "Range")]
        for key_id, display_fallback in info_keys:
            frame = ctk.CTkFrame(info_inner, fg_color="transparent")
            frame.pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(frame, text=T.L(key_id), font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack()
            lbl = ctk.CTkLabel(frame, text="—", font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY)
            lbl.pack()
            self._info_labels[display_fallback] = lbl

        # ─── Piano Roll ───────────────────────────────────
        self._canvas_frame = ctk.CTkFrame(self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS)
        self._canvas_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._canvas = ctk.CTkCanvas(self._canvas_frame, bg=T.BG_DARKEST, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self._canvas.bind("<Configure>", lambda e: self._draw_piano_grid())

        # ─── Progress Bar ─────────────────────────────────
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=(0, 5))
        self._progress_bar = ctk.CTkProgressBar(progress_frame, height=6, corner_radius=3,
                                                fg_color=T.PROGRESS_BG, progress_color=T.ACCENT)
        self._progress_bar.pack(fill="x")
        self._progress_bar.set(0)

        time_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_frame.pack(fill="x", padx=20, pady=(0, 10))
        self._time_current = ctk.CTkLabel(time_frame, text="0:00", font=T.FONT_TINY, text_color=T.TEXT_MUTED)
        self._time_current.pack(side="left")
        self._time_total = ctk.CTkLabel(time_frame, text="0:00", font=T.FONT_TINY, text_color=T.TEXT_MUTED)
        self._time_total.pack(side="right")
        self._notes_progress = ctk.CTkLabel(time_frame, text="", font=T.FONT_TINY, text_color=T.TEXT_ACCENT)
        self._notes_progress.pack()

        # ─── Controls — single compact row ────────────────
        controls = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        controls.pack(fill="x", padx=20, pady=(0, 15))
        ctrl = ctk.CTkFrame(controls, fg_color="transparent")
        ctrl.pack(fill="x", padx=8, pady=8)

        # Play / Pause / Stop — compact buttons
        btn_s = dict(height=30, font=T.FONT_SMALL, corner_radius=T.BUTTON_CORNER)
        self._play_btn = ctk.CTkButton(ctrl, text="▶", fg_color=T.SUCCESS, command=self._play, width=40, **btn_s)
        self._play_btn.pack(side="left", padx=1)
        self._pause_btn = ctk.CTkButton(ctrl, text="⏸", fg_color=T.WARNING, command=self._pause, width=40, **btn_s)
        self._pause_btn.pack(side="left", padx=1)
        self._stop_btn = ctk.CTkButton(ctrl, text="⏹", fg_color=T.ERROR, command=self._stop, width=40, **btn_s)
        self._stop_btn.pack(side="left", padx=(1, 8))

        # Separator
        ctk.CTkFrame(ctrl, width=1, height=22, fg_color=T.BORDER).pack(side="left", padx=4)

        # Delay
        ctk.CTkLabel(ctrl, text="⏱", font=T.FONT_TINY, text_color=T.TEXT_MUTED).pack(side="left", padx=(4, 2))
        init_delay = str(self.app.config.get("start_delay", 3.0))
        self._delay_var = ctk.StringVar(value=init_delay)
        self._delay_entry = ctk.CTkEntry(ctrl, textvariable=self._delay_var, width=36, height=24,
                                          font=T.FONT_TINY, fg_color=T.BG_ELEVATED, border_color=T.ACCENT_DIM)
        self._delay_entry.pack(side="left", padx=(0, 6))
        self._delay_entry.bind("<Return>", self._on_delay_confirm)

        # Separator
        ctk.CTkFrame(ctrl, width=1, height=22, fg_color=T.BORDER).pack(side="left", padx=4)

        # Speed
        self._speed_label = ctk.CTkLabel(ctrl, text="100%", font=T.FONT_TINY, text_color=T.TEXT_MUTED, width=35)
        self._speed_label.pack(side="left", padx=(4, 2))
        self._speed_slider = ctk.CTkSlider(ctrl, from_=25, to=300, number_of_steps=55, width=70, height=14,
                                           fg_color=T.PROGRESS_BG, progress_color=T.ACCENT, button_color=T.ACCENT_LIGHT,
                                           command=self._on_speed_change)
        self._speed_slider.set(100)
        self._speed_slider.pack(side="left", padx=(0, 6))

        # Separator
        ctk.CTkFrame(ctrl, width=1, height=22, fg_color=T.BORDER).pack(side="left", padx=4)

        # Transpose
        self._transpose_label = ctk.CTkLabel(ctrl, text="TP:0", font=T.FONT_TINY, text_color=T.TEXT_MUTED, width=32)
        self._transpose_label.pack(side="left", padx=(4, 2))
        self._transpose_slider = ctk.CTkSlider(ctrl, from_=-24, to=24, number_of_steps=48, width=70, height=14,
                                               fg_color=T.PROGRESS_BG, progress_color=T.ACCENT, button_color=T.ACCENT_LIGHT,
                                               command=self._on_transpose_change)
        self._transpose_slider.set(0)
        self._transpose_slider.pack(side="left")


        self._active_visuals = True
        self._render_loop()

    def _open_file(self):
        path = filedialog.askopenfilename(title="Open MIDI", filetypes=[("MIDI Files", "*.mid *.midi"), ("All Files", "*.*")])
        if path: self.load_file(path)

    def load_file(self, path, song_id=None):
        if not os.path.exists(path): return
        self._current_file, self._current_song_id = path, song_id
        self._song_info = get_song_info(path)
        info = self._song_info
        self._file_label.configure(text=f"♪ {info.title or os.path.basename(path)}")
        mins, secs = divmod(int(info.duration), 60)
        self._info_labels["Duration"].configure(text=f"{mins}:{secs:02d}")
        self._info_labels["Notes"].configure(text=str(info.note_count))
        self._info_labels["Tempo"].configure(text=f"{info.tempo_bpm} BPM")
        if info.note_count > 0:
            self._info_labels["Range"].configure(text=f"{get_note_name(info.min_note)} — {get_note_name(info.max_note)}")
        self._time_total.configure(text=f"{mins}:{secs:02d}")
        self.engine.load(parse_midi(path))

    def _play(self):
        if self.engine.is_playing:
            if self.engine.is_paused: self.engine.resume()
        else:
            try: delay = float(self._delay_var.get())
            except ValueError: delay = 3.0
            self.engine.start_delay = delay
            self.engine.play()
            
            # INCREMENT PLAY COUNT IMMEDIATELY
            if self._current_song_id:
                def _inc_task():
                    from library.cloud_database import CloudDatabase
                    db = CloudDatabase()
                    db.increment_play_count(self._current_song_id)
                threading.Thread(target=_inc_task, daemon=True).start()

    def _pause(self):
        if self.engine.is_playing: self.engine.toggle_pause()
    def _stop(self): self.engine.stop()

    def _on_speed_change(self, value):
        s = int(value)
        self._speed_label.configure(text=f"{s}%")
        self.engine.speed = s / 100.0

    def _on_transpose_change(self, value):
        tp = int(value)
        self._transpose_label.configure(text=f"TP:{tp:+d}" if tp != 0 else "TP:0")
        self.engine.transpose = tp

    def _on_delay_confirm(self, event):
        try:
            val = float(self._delay_var.get())
            self.app.config["start_delay"] = val
            from ui.settings_tab import save_config
            save_config(self.app.config)
        except ValueError: pass
        self.focus()

    def _on_progress(self, current, total, idx, total_events):
        self.after(0, self._update_progress, current, total, idx, total_events)
    def _update_progress(self, current, total, idx, total_events):
        if total > 0: self._progress_bar.set(current / total)
        mins, secs = divmod(int(current), 60)
        self._time_current.configure(text=f"{mins}:{secs:02d}")
        self._notes_progress.configure(text=f"{idx}/{total_events}")

    def _on_note(self, n, k): pass
    def _on_countdown(self, s):
        msg = f"Starting in {s}s..." if s > 0 else "▶ Playing"
        self._status_label.configure(text=msg)
    def _on_finished(self): self._status_label.configure(text="Finished")
    def _on_log(self, msg): self.after(0, self._append_log, msg)

    def _draw_piano_grid(self):
        self._canvas.delete("grid")
        w, h = self._canvas.winfo_width(), self._canvas.winfo_height()
        if w < 10: return
        kw = w / 61
        
        # Subtle vertical lane lines
        for i in range(62):
            self._canvas.create_line(i*kw, 0, i*kw, h, fill="#1a1a1a", tags="grid")
        
        # Hit-line at bottom (where notes "land")
        hit_y = h - 8
        self._canvas.create_line(0, hit_y, w, hit_y, fill=T.ACCENT, width=3, tags="grid")
        # Glow effect under hit-line
        self._canvas.create_line(0, hit_y+2, w, hit_y+2, fill=T.ACCENT_DIM, width=1, tags="grid")

    def _render_loop(self):
        if not self._active_visuals: return
        try: self._update_roll()
        except: pass
        self.after(25, self._render_loop)  # ~40 FPS for smoother animation

    def _update_roll(self):
        from core.key_mapping import MIDI_TO_KEY
        
        self._canvas.delete("note")
        if not self.engine.events: return
        
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 10 or h < 10: return
        
        ct = self.engine.current_time
        look_ahead = 3.0   # Show notes 3 seconds into the future
        look_behind = 0.15  # Keep notes visible briefly after being played
        kw = w / 61         # Width per key column
        hit_y = h - 8       # Where notes "land"
        note_h = 22         # Height of each note block
        
        idx = self.engine.current_index
        
        for i in range(max(0, idx - 80), min(idx + 1200, len(self.engine.events))):
            e = self.engine.events[i]
            if e.velocity <= 0: continue  # Skip note_off events
            
            diff = e.time - ct  # Time until this note plays
            
            if diff > look_ahead: break       # Too far in future
            if diff < -look_behind: continue   # Already passed
            
            if 36 <= e.note <= 96:
                # Calculate position: notes fall from top (future) to hit_y (now)
                # diff=look_ahead → y=0 (top), diff=0 → y=hit_y (bottom)
                progress = 1.0 - (diff / look_ahead)  # 0.0=top, 1.0=hit_y
                y_bottom = progress * hit_y
                y_top = y_bottom - note_h
                
                x_left = (e.note - 36) * kw + 1
                x_right = (e.note - 36 + 1) * kw - 1
                
                # Color: purple=falling, green=hitting, dim=past
                if diff <= 0:
                    fill = T.SUCCESS       # Currently playing — green flash
                    outline = "#4ade80"
                elif diff < 0.15:
                    fill = T.ACCENT_LIGHT  # About to hit — bright
                    outline = T.ACCENT
                else:
                    fill = T.ACCENT        # Falling — normal purple
                    outline = T.ACCENT_HOVER
                
                # Draw note rectangle
                self._canvas.create_rectangle(
                    x_left, y_top, x_right, y_bottom,
                    fill=fill, outline=outline, width=1, tags="note"
                )
                
                # Draw key label inside note
                key_char = MIDI_TO_KEY.get(e.note, "")
                if key_char and kw > 6:  # Only show if column is wide enough
                    cx = (x_left + x_right) / 2
                    cy = (y_top + y_bottom) / 2
                    font_size = max(7, min(11, int(kw * 0.6)))
                    self._canvas.create_text(
                        cx, cy, text=key_char,
                        fill="#ffffff", font=("Consolas", font_size, "bold"),
                        tags="note"
                    )

    def _append_log(self, msg):
        # Log messages shown in status label since console was removed
        pass
