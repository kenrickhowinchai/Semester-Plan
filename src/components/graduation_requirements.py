import tkinter as tk
from tkinter import ttk


class GraduationRequirementsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Define the requirements
        self.requirements = {
            "Kernbereich": {
                "total": 48,
                "sub_requirements": {
                    "Informatik und Mathematik": 18,
                    "Simulation und Optimierung": 18,
                    "Messen, Steuern, Regeln": 12
                }
            },
            "Profilbereich": {
                "total": 18
            },
            "Projekt": {
                "total": 6
            },
            "Freiwahlbereich": {
                "total": 18
            },
            "Fachpraktikum": {
                "total": 6
            },
            "Masterarbeit": {
                "total": 24
            }
        }

        # Storage for canvas bar widgets
        self._bar_canvases = {}
        self._bar_data = {}
        self._credits_labels = {}

        # Create the UI
        self.create_widgets()

        # Update the display
        self.update_requirements()

    def create_widgets(self):
        """Create the UI elements with custom canvas progress bars."""
        # Title label
        title_label = tk.Label(
            self,
            text="Studienfortschritt",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, 10))

        # Create frame for requirements
        self.req_frame = tk.Frame(self)
        self.req_frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        bar_height = 14
        sub_bar_height = 10

        for req_name, req_data in self.requirements.items():
            # Requirement name label
            req_label = tk.Label(
                self.req_frame,
                text=req_name,
                font=("Segoe UI", 10, "bold"),
                anchor="w"
            )
            req_label.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)

            # Canvas progress bar
            bar_canvas = tk.Canvas(
                self.req_frame, height=bar_height, highlightthickness=0,
                bg="#E0E0E0", relief=tk.FLAT, bd=0
            )
            bar_canvas.grid(row=row, column=1, sticky="ew", padx=4, pady=3)

            # Credits label
            credits_label = tk.Label(
                self.req_frame,
                text=f"0/{req_data['total']} LP",
                font=("Segoe UI", 9),
                anchor="e", width=10
            )
            credits_label.grid(row=row, column=2, padx=(4, 0), pady=3)

            self._bar_canvases[req_name] = bar_canvas
            self._bar_data[req_name] = {"max": req_data["total"], "value": 0}
            self._credits_labels[req_name] = credits_label

            row += 1

            # Sub-requirements
            if "sub_requirements" in req_data:
                for sub_name, sub_total in req_data["sub_requirements"].items():
                    key = f"{req_name}_{sub_name}"

                    sub_label = tk.Label(
                        self.req_frame,
                        text=f"  \u2022 {sub_name}",
                        font=("Segoe UI", 9),
                        anchor="w", fg="#555555"
                    )
                    sub_label.grid(row=row, column=0, sticky="w", padx=(12, 8), pady=2)

                    sub_canvas = tk.Canvas(
                        self.req_frame, height=sub_bar_height, highlightthickness=0,
                        bg="#E0E0E0", relief=tk.FLAT, bd=0
                    )
                    sub_canvas.grid(row=row, column=1, sticky="ew", padx=4, pady=2)

                    sub_credits = tk.Label(
                        self.req_frame,
                        text=f"0/{sub_total} LP",
                        font=("Segoe UI", 8),
                        anchor="e", width=10, fg="#555555"
                    )
                    sub_credits.grid(row=row, column=2, padx=(4, 0), pady=2)

                    self._bar_canvases[key] = sub_canvas
                    self._bar_data[key] = {"max": sub_total, "value": 0}
                    self._credits_labels[key] = sub_credits

                    row += 1

        # Configure column weights
        self.req_frame.columnconfigure(1, weight=1)

        # Separator
        sep = tk.Frame(self, height=2, bg="#BDBDBD")
        sep.pack(fill=tk.X, pady=10)

        # Total progress
        total_frame = tk.Frame(self)
        total_frame.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            total_frame,
            text="Gesamt",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.total_canvas = tk.Canvas(
            total_frame, height=20, highlightthickness=0,
            bg="#E0E0E0", relief=tk.FLAT, bd=0
        )
        self.total_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        self.total_label = tk.Label(
            total_frame,
            text="0/120 LP",
            font=("Segoe UI", 10, "bold"),
            anchor="e", width=10
        )
        self.total_label.pack(side=tk.LEFT, padx=(4, 0))

        self._bar_canvases["__total__"] = self.total_canvas
        self._bar_data["__total__"] = {"max": 120, "value": 0}

        # Bind resize so bars redraw
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        """Redraw all bars when the frame resizes."""
        self._draw_all_bars()

    def _draw_bar(self, canvas, value, maximum):
        """Draw a filled progress bar on the given canvas."""
        canvas.delete("all")
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 2 or h < 2:
            return

        # Background track (rounded rect)
        radius = min(h // 2, 4)
        self._rounded_rect(canvas, 0, 0, w, h, radius, fill="#E0E0E0", outline="")

        # Fill
        if maximum > 0 and value > 0:
            fraction = min(value / maximum, 1.0)
            fill_w = max(radius * 2, int(w * fraction))

            if value >= maximum:
                fill_color = "#66BB6A"  # green when complete
            else:
                fill_color = "#42A5F5"  # blue in progress

            self._rounded_rect(canvas, 0, 0, fill_w, h, radius,
                               fill=fill_color, outline="")

            # Percentage text inside bar if wide enough
            if fill_w > 30:
                pct = int(fraction * 100)
                canvas.create_text(
                    fill_w - 6, h // 2,
                    text=f"{pct}%", anchor="e",
                    fill="white", font=("Segoe UI", max(7, h - 6), "bold"))

    def _rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on a canvas."""
        r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
            x1 + r, y1,
        ]
        canvas.create_polygon(points, smooth=True, **kwargs)

    def _draw_all_bars(self):
        """Redraw every progress bar."""
        for key, canvas in self._bar_canvases.items():
            data = self._bar_data.get(key)
            if data:
                self._draw_bar(canvas, data["value"], data["max"])

    def update_requirements(self):
        """Update the progress bars and labels based on current courses."""
        # Reset all counters
        credits_per_requirement = {
            "Kernbereich_Informatik und Mathematik": 0,
            "Kernbereich_Simulation und Optimierung": 0,
            "Kernbereich_Messen, Steuern, Regeln": 0,
            "Profilbereich": 0,
            "Projekt": 0,
            "Freiwahlbereich": 0,
            "Fachpraktikum": 0,
            "Masterarbeit": 0
        }

        # Count credits in each semester
        for semester_frame in self.app.semester_frames:
            for course in semester_frame.courses:
                if not hasattr(course, 'group') or not course.group:
                    continue

                group = course.group.strip()
                credits = course.credits

                if group.startswith("1."):
                    credits_per_requirement["Kernbereich_Informatik und Mathematik"] += credits
                elif group.startswith("2."):
                    credits_per_requirement["Kernbereich_Simulation und Optimierung"] += credits
                elif group.startswith("3."):
                    credits_per_requirement["Kernbereich_Messen, Steuern, Regeln"] += credits
                elif group.startswith("4."):
                    credits_per_requirement["Profilbereich"] += credits
                elif group.startswith("6."):
                    credits_per_requirement["Projekt"] += credits
                elif group.startswith("7."):
                    credits_per_requirement["Freiwahlbereich"] += credits
                elif group.startswith("8."):
                    credits_per_requirement["Fachpraktikum"] += credits
                elif group.startswith("9."):
                    credits_per_requirement["Masterarbeit"] += credits

        # Kernbereich total
        kernbereich_total = (
            credits_per_requirement["Kernbereich_Informatik und Mathematik"] +
            credits_per_requirement["Kernbereich_Simulation und Optimierung"] +
            credits_per_requirement["Kernbereich_Messen, Steuern, Regeln"]
        )

        # Update sub-requirement bars
        for sub_name in ["Informatik und Mathematik", "Simulation und Optimierung",
                         "Messen, Steuern, Regeln"]:
            key = f"Kernbereich_{sub_name}"
            earned = credits_per_requirement[key]
            maximum = self.requirements["Kernbereich"]["sub_requirements"][sub_name]

            self._bar_data[key] = {"max": maximum, "value": earned}
            self._credits_labels[key].config(
                text=f"{earned}/{maximum} LP",
                fg="#2E7D32" if earned >= maximum else "#555555")

        # Update main requirement bars
        requirement_totals = {
            "Kernbereich": kernbereich_total,
            "Profilbereich": credits_per_requirement["Profilbereich"],
            "Projekt": credits_per_requirement["Projekt"],
            "Freiwahlbereich": credits_per_requirement["Freiwahlbereich"],
            "Fachpraktikum": credits_per_requirement["Fachpraktikum"],
            "Masterarbeit": credits_per_requirement["Masterarbeit"]
        }

        for req_name, req_data in self.requirements.items():
            earned = requirement_totals[req_name]
            maximum = req_data["total"]

            self._bar_data[req_name] = {"max": maximum, "value": earned}
            self._credits_labels[req_name].config(
                text=f"{earned}/{maximum} LP",
                fg="#2E7D32" if earned >= maximum else "#212121")

        # Total
        total_credits = sum(requirement_totals.values())
        self._bar_data["__total__"] = {"max": 120, "value": total_credits}
        self.total_label.config(
            text=f"{total_credits}/120 LP",
            fg="#2E7D32" if total_credits >= 120 else "#212121",
            font=("Segoe UI", 10, "bold"))

        # Redraw all bars
        self._draw_all_bars()

    def apply_scaling(self, scale_factor):
        """Apply scaling to this graduation requirements frame."""
        def update_widget_font(widget):
            try:
                current_font = widget.cget("font")
                if current_font:
                    if isinstance(current_font, (tuple, list)):
                        family, size = current_font[0], current_font[1]
                        new_size = max(8, int(size * scale_factor))
                        new_font = (family, new_size)
                        if len(current_font) > 2:
                            new_font = new_font + current_font[2:]
                        widget.configure(font=new_font)
                    elif isinstance(current_font, str):
                        parts = current_font.split()
                        if len(parts) >= 2:
                            try:
                                size = int(parts[1])
                                new_size = max(8, int(size * scale_factor))
                                parts[1] = str(new_size)
                                new_font = " ".join(parts)
                                widget.configure(font=new_font)
                            except (ValueError, IndexError):
                                pass
            except tk.TclError:
                pass

            try:
                for child in widget.winfo_children():
                    update_widget_font(child)
            except tk.TclError:
                pass

        update_widget_font(self)

    def set_scale_factor(self, scale_factor):
        """Update the graduation requirements frame based on scale factor."""
        self.scale_factor = scale_factor

        if not hasattr(self, '_base_dimensions'):
            self._base_dimensions = {
                'title_font_size': 14,
                'label_font_size': 10,
                'padx': 5,
                'pady': 5
            }

        def update_fonts_recursive(widget):
            try:
                current_font = widget.cget("font")
                if current_font:
                    if isinstance(current_font, (tuple, list)) and len(current_font) >= 2:
                        family, size = current_font[0], current_font[1]
                        if size >= 14:
                            new_size = max(10, int(size * scale_factor))
                        else:
                            new_size = max(8, int(size * scale_factor))
                        new_font = (family, new_size)
                        if len(current_font) > 2:
                            new_font = new_font + current_font[2:]
                        widget.configure(font=new_font)
            except tk.TclError:
                pass

            try:
                for child in widget.winfo_children():
                    update_fonts_recursive(child)
            except tk.TclError:
                pass

        update_fonts_recursive(self)
        self.after_idle(self._draw_all_bars)