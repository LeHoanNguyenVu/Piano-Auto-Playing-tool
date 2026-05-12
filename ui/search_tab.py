"""
Search Tab — Online song search and discovery via Supabase.
"""

import threading
import customtkinter as ctk
from ui import theme as T
from library import cloud_database, song_manager


class SearchTab(ctk.CTkFrame):
    """Cloud song search interface."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=T.PLAYER_BG, corner_radius=0)
        self.app = app
        self.db = None
        self._result_widgets = []
        self._all_results = [] # Lưu toàn bộ kết quả tìm kiếm
        self._displayed_count = 0 # Số lượng bài đang hiển thị
        self._batch_size = 30 # Mỗi lần hiện thêm bao nhiêu bài
        self._search_timer = None
        self._build_ui()
        self.after(200, self._init_db)

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="🌐 " + T.L("search"), font=T.FONT_TITLE, text_color=T.TEXT_PRIMARY).pack(side="left")

        search_bar = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=T.CORNER_RADIUS)
        search_bar.pack(fill="x", padx=20, pady=(0, 15))
        
        # Search variable for tracing (Suggestions)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_type)

        self._search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search songs or artists...", 
                                          textvariable=self._search_var,
                                          height=40, font=T.FONT_BODY, fg_color="transparent", border_width=0)
        self._search_entry.pack(side="left", fill="x", expand=True, padx=15)
        
        self._search_btn = ctk.CTkButton(search_bar, text="🔍", width=50, height=32, fg_color=T.ACCENT, command=self._search)
        self._search_btn.pack(side="right", padx=10)

        self._count_label = ctk.CTkLabel(self, text="", font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        self._count_label.pack(anchor="w", padx=25, pady=(0, 5))

        self._results_frame = ctk.CTkScrollableFrame(self, fg_color=T.BG_DARKEST, corner_radius=T.CORNER_RADIUS)
        self._results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # TĂNG TỐC ĐỘ CUỘN CHUỘT
        self._results_frame.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Tăng tốc độ cuộn chuột lên cực kỳ nhanh."""
        # Chia cho 3 = Cực nhanh. 120/3 = 40 đơn vị cuộn mỗi nấc.
        self._results_frame._parent_canvas.yview_scroll(int(-1*(event.delta/3)), "units")
        
        # KIỂM TRA XEM ĐÃ CUỘN XUỐNG CUỐI CHƯA
        # y_pos: 0.0 là đầu trang, 1.0 là cuối trang
        y_pos = self._results_frame._parent_canvas.yview()[1]
        if y_pos > 0.9: # Nếu cuộn quá 90% danh sách
            self._load_more_results()

    def _load_more_results(self):
        """Tải thêm một đợt bài nhạc tiếp theo."""
        if self._displayed_count >= len(self._all_results):
            return # Đã hiện hết sạch rồi
            
        start = self._displayed_count
        end = start + self._batch_size
        next_batch = self._all_results[start:end]
        
        favs = cloud_database.load_favorites()
        for s in next_batch:
            self._create_row(s, favs)
            
        self._displayed_count = end
        self._update_count_label()

    def _update_count_label(self):
        total = len(self._all_results)
        shown = min(self._displayed_count, total)
        if total == 0:
            self._count_label.configure(text="Không tìm thấy bài hát nào.")
        else:
            self._count_label.configure(text=f"Đang hiện {shown} / {total} bài hát")

    def _init_db(self):
        def _worker(): self.db = cloud_database.CloudDatabase()
        threading.Thread(target=_worker, daemon=True).start()

    def _on_type(self, *args):
        """Suggestions logic: debounce search while typing."""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(400, self._search)

    def _search(self):
        query = self._search_var.get().strip()
        if not self.db: return
        if not query:
            # Bỏ giới hạn [:50] để lấy toàn bộ danh sách
            self._display_results(self.db.catalog) 
            return
            
        def _worker():
            results = self.db.search(query)
            self.after(0, self._display_results, results)
        threading.Thread(target=_worker, daemon=True).start()

    def _display_results(self, songs):
        self._clear_results()
        self._all_results = songs or []
        self._displayed_count = 0
        
        if not self._all_results:
            self._update_count_label()
            self._show_message(T.L("no_results"))
            return
        
        # Hiển thị đợt đầu tiên
        self._load_more_results()

    def _create_row(self, song, favs):
        song_id = str(song.get('id'))
        already_fav = song_id in favs
        row = ctk.CTkFrame(self._results_frame, fg_color=T.BG_CARD, corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)
        
        # Container chính dùng grid để căn chỉnh ảnh và text
        row.grid_columnconfigure(1, weight=1)
        
        # 1. PHẦN HÌNH ẢNH (THUMBNAIL)
        from PIL import Image
        import requests
        from io import BytesIO

        # Tạo frame chứa ảnh
        img_frame = ctk.CTkFrame(row, width=60, height=60, fg_color=T.BG_DARKEST, corner_radius=6)
        img_frame.pack(side="left", padx=10, pady=10)
        img_frame.pack_propagate(False)

        def _load_img(label, url):
            try:
                if url:
                    response = requests.get(url, timeout=5)
                    img_data = BytesIO(response.content)
                    pil_img = Image.open(img_data)
                else:
                    raise Exception("No URL")
            except:
                # Ảnh mặc định nếu lỗi hoặc không có link
                pil_img = Image.new('RGB', (60, 60), color='#1e293b')
            
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
            self.after(0, lambda: label.configure(image=ctk_img, text=""))

        img_label = ctk.CTkLabel(img_frame, text="🎵", font=("Arial", 24))
        img_label.pack(expand=True, fill="both")
        
        # Tải ảnh ở luồng riêng để không treo UI
        threading.Thread(target=_load_img, args=(img_label, song.get('cover_url')), daemon=True).start()

        # 2. PHẦN THÔNG TIN (TIÊU ĐỀ)
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)
        
        # Tiêu đề với tính năng tự động xuống dòng (wraplength=300-400 tùy độ rộng)
        ctk.CTkLabel(info_frame, 
                     text=song.get('title', 'Unknown'), 
                     font=T.FONT_BODY_BOLD, 
                     text_color=T.TEXT_PRIMARY, 
                     anchor="w",
                     justify="left",
                     wraplength=350).pack(fill="x", padx=(0, 10))
        
        # 3. PHẦN NÚT BẤM
        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.pack(side="right", padx=10)
        
        fav_text = "❤" if already_fav else "🤍"
        ctk.CTkButton(btns, text=fav_text, width=40, height=32, fg_color="#be185d" if already_fav else T.BG_ELEVATED,
                       command=lambda s=song: self._toggle_favorite(s)).pack(side="left", padx=5)
        ctk.CTkButton(btns, text=T.L("play"), width=80, height=32, fg_color=T.SUCCESS,
                       command=lambda s=song: self._play_song(s)).pack(side="left")
        
        self._result_widgets.append(row)

    def _play_song(self, song):
        self._show_message(T.L("searching"))
        def _worker():
            try:
                path = self.db.download_to_temp(song)
                if path: self.after(0, lambda: self._start_playback(path, song.get('id')))
            except Exception as e:
                self.after(0, lambda: self._show_message(f"Error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _start_playback(self, path, song_id):
        if hasattr(self.app, 'player_tab'):
            self.app.player_tab.load_file(path, song_id)
            self.app.show_frame("player")
            self.app.player_tab._play()

    def _toggle_favorite(self, song):
        sid = str(song.get('id'))
        favs = cloud_database.load_favorites()
        if sid in favs:
            cloud_database.remove_favorite(sid)
        else:
            def _worker():
                try:
                    self.db.download_to_favorites(song)
                    self.after(0, self._search)
                except: pass
            threading.Thread(target=_worker, daemon=True).start()
        self._search()

    def _show_message(self, text):
        self._clear_results()
        lbl = ctk.CTkLabel(self._results_frame, text=text, font=T.FONT_BODY, text_color=T.TEXT_MUTED)
        lbl.pack(pady=40)
        self._result_widgets.append(lbl)

    def _clear_results(self):
        for w in self._result_widgets: w.destroy()
        self._result_widgets.clear()
