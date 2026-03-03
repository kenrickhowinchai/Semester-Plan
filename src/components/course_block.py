import tkinter as tk
from tkinter import ttk


class CourseBlock(tk.Frame):
    """Visual card representing a single course."""

    GROUP_COLORS = {
        "1.": "#D4E6F1",  # Kernbereich - Informatik und Mathematik
        "2.": "#D5F5E3",  # Kernbereich - Simulation und Optimierung
        "3.": "#E8DAEF",  # Kernbereich - Messen, Steuern, Regeln
        "4.": "#FDEBD0",  # Profilbereich
        "6.": "#FADBD8",  # Projekt
        "7.": "#F9E79F",  # Freiwahlbereich
        "8.": "#D1F2EB",  # Fachpraktikum
        "9.": "#FDEDEC",  # Masterarbeit
    }

    # Darker accent colors for the left border per group
    GROUP_ACCENT = {
        "1.": "#2980B9",
        "2.": "#27AE60",
        "3.": "#8E44AD",
        "4.": "#E67E22",
        "6.": "#E74C3C",
        "7.": "#F1C40F",
        "8.": "#1ABC9C",
        "9.": "#C0392B",
    }

    def __init__(self, parent, course, drag_drop_manager=None, is_placed=False,
                 in_semester=False):
        super().__init__(parent, relief=tk.FLAT, borderwidth=0, padx=0, pady=0)
        self.course = course
        self.drag_drop_manager = drag_drop_manager
        self.is_placed = is_placed
        self.in_semester = in_semester

        bg_color = self.get_background_color()
        accent = self._get_accent_color()

        self.configure(background=bg_color)

        # --- Left accent border -------------------------------------------
        self._accent_bar = tk.Frame(self, width=4, bg=accent)
        self._accent_bar.pack(side=tk.LEFT, fill=tk.Y)

        # --- Content area (right of accent bar) ---------------------------
        content = tk.Frame(self, bg=bg_color, padx=6, pady=4)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._content = content

        text_color = "#9E9E9E" if is_placed else "#212121"
        sub_color = "#BDBDBD" if is_placed else "#616161"

        # --- Header: title + star ---
        header = tk.Frame(content, bg=bg_color)
        header.pack(fill=tk.X)

        self.fav_text = tk.StringVar()
        self._update_star_text()

        self.fav_btn = tk.Button(
            header, textvariable=self.fav_text,
            font=("Segoe UI", 12), width=2,
            command=self.toggle_favorite,
            relief=tk.FLAT, bd=0, bg=bg_color,
            fg="#FFB300" if (hasattr(course, 'favorite') and course.favorite) else "#BDBDBD",
            activebackground=bg_color,
            cursor="hand2" if not is_placed else "",
            state=tk.DISABLED if is_placed else tk.NORMAL)
        self.fav_btn.pack(side=tk.RIGHT)

        self.title_label = tk.Label(
            header, text=course.title,
            font=("Segoe UI", 10, "bold"), anchor="w",
            bg=bg_color, fg=text_color, wraplength=200, justify=tk.LEFT)
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Info line: credits + module code ---
        info_parts = [f"{course.credits} LP"]
        if hasattr(course, 'module_code') and course.module_code:
            info_parts.append(course.module_code)
        if hasattr(course, 'semester') and course.semester:
            info_parts.append(course.semester)

        info_text = "  \u2022  ".join(info_parts)
        tk.Label(content, text=info_text, font=("Segoe UI", 8),
                 bg=bg_color, fg=sub_color, anchor="w").pack(fill=tk.X)

        # Placement indicator
        if is_placed and course.assigned_semester:
            tk.Label(
                content, text=f"\u2192 {course.assigned_semester.title}",
                font=("Segoe UI", 8, "italic"),
                bg=bg_color, fg="#EF5350", anchor="w").pack(fill=tk.X)

        # --- Proportional height for semester blocks ----------------------
        if in_semester:
            min_h = max(48, course.credits * 10)
            self.configure(height=min_h)
            self.pack_propagate(False)

        # Draggable if not placed
        if self.drag_drop_manager and not is_placed:
            self.configure(cursor="hand2")
            self.bind("<ButtonPress-1>", self.on_drag_start)
            self.title_label.bind("<ButtonPress-1>", self.on_drag_start)
            for child in self.winfo_children():
                child.bind("<ButtonPress-1>", self.on_drag_start)
                for gc in child.winfo_children():
                    gc.bind("<ButtonPress-1>", self.on_drag_start)

    # ------------------------------------------------------------------
    def _get_accent_color(self):
        if self.is_placed:
            return "#BDBDBD"
        if hasattr(self.course, 'group') and self.course.group:
            for prefix, color in self.GROUP_ACCENT.items():
                if self.course.group.startswith(prefix):
                    return color
        return "#90A4AE"

    def get_background_color(self):
        if self.is_placed:
            return "#EEEEEE"
        if hasattr(self.course, 'favorite') and self.course.favorite:
            return "#FFF9C4"
        if hasattr(self.course, 'group') and self.course.group:
            for prefix, color in self.GROUP_COLORS.items():
                if self.course.group.startswith(prefix):
                    return color
        return "#F5F5F5"

    def _update_star_text(self):
        if hasattr(self.course, 'favorite') and self.course.favorite:
            self.fav_text.set("\u2605")
        else:
            self.fav_text.set("\u2606")

    def update_favorite_display(self):
        self._update_star_text()

    def update_appearance(self):
        bg_color = self.get_background_color()
        accent = self._get_accent_color()
        self.configure(background=bg_color)
        try:
            self._accent_bar.configure(background=accent)
        except tk.TclError:
            pass
        star_fg = "#FFB300" if (hasattr(self.course, 'favorite') and self.course.favorite) else "#BDBDBD"
        try:
            self.fav_btn.configure(background=bg_color, foreground=star_fg,
                                   activebackground=bg_color)
        except tk.TclError:
            pass
        for child in self.winfo_children():
            try:
                if isinstance(child, tk.Frame):
                    child.configure(background=bg_color)
                    for gc in child.winfo_children():
                        try:
                            gc.configure(background=bg_color)
                        except tk.TclError:
                            pass
                else:
                    child.configure(background=bg_color)
            except tk.TclError:
                pass
        # Re-colour accent bar specifically (it should keep accent colour)
        try:
            self._accent_bar.configure(background=accent)
        except tk.TclError:
            pass

    def toggle_favorite(self):
        if not hasattr(self.course, 'favorite'):
            self.course.favorite = False
        self.course.favorite = not self.course.favorite
        self._update_star_text()
        self.update_appearance()
        if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
            self.drag_drop_manager.app.save_state()

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------
    def set_scale_factor(self, scale_factor):
        self.scale_factor = scale_factor
        if not hasattr(self, '_base_dims'):
            self._base_dims = {'padx': 6, 'pady': 4, 'title': 10, 'info': 8, 'star': 12}

        new_padx = max(2, int(self._base_dims['padx'] * scale_factor))
        new_pady = max(2, int(self._base_dims['pady'] * scale_factor))
        try:
            self._content.configure(padx=new_padx, pady=new_pady)
        except tk.TclError:
            pass

        title_sz = max(7, int(self._base_dims['title'] * scale_factor))
        star_sz = max(8, int(self._base_dims['star'] * scale_factor))

        try:
            self.title_label.configure(font=("Segoe UI", title_sz, "bold"))
        except tk.TclError:
            pass
        try:
            self.fav_btn.configure(font=("Segoe UI", star_sz))
        except tk.TclError:
            pass

        # Scale proportional height if in semester
        if self.in_semester:
            min_h = max(48, self.course.credits * 10)
            scaled_h = max(36, int(min_h * scale_factor))
            try:
                self.configure(height=scaled_h)
            except tk.TclError:
                pass

        self.update_idletasks()

    def on_drag_start(self, event):
        if self.drag_drop_manager:
            if event.widget == self.fav_btn:
                self.toggle_favorite()
                return "break"
            self.drag_drop_manager.start_drag(event, self)
            return "break"
