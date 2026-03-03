import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import shutil
import time
import traceback
import sys

from components.semester_frame import SemesterFrame
from components.course_list import CourseList
from components.drag_drop_manager import DragDropManager
from models.course import Course
from components.graduation_requirements import GraduationRequirementsFrame
from components.course_block import CourseBlock


class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Semester Calendar Planner")
        self.root.geometry("1600x900")
        self.root.minsize(900, 500)

        # --- Modern theme -------------------------------------------------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 9))
        style.configure("TButton", padding=4)
        style.configure("TLabel", padding=2)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"))

        # --- Scaling -------------------------------------------------------
        self.scale_factor = 1.0
        self.base_fonts = {}
        self.setup_scaling()

        # --- Resources path -----------------------------------------------
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            self.resources_dir = os.path.join(application_path, '_internal', 'resources')
        else:
            self.resources_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'resources')

        self.save_dir = os.path.join(self.resources_dir, 'saves')
        os.makedirs(self.save_dir, exist_ok=True)

        # --- Slot system ---------------------------------------------------
        self.current_slot = "Default"
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        self.available_slots = self.get_available_slots()

        # --- Core state ----------------------------------------------------
        self.drag_drop_manager = DragDropManager(self)
        self.courses = []
        self.semester_frames = []
        self.load_courses()

        # --- UI ------------------------------------------------------------
        self.create_widgets()
        self.apply_scaling()
        self.load_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ==================================================================
    #  Scaling system
    # ==================================================================
    def setup_scaling(self):
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())
        self.root.bind("<Control-MouseWheel>", self.on_zoom_mousewheel)
        self.root.focus_set()

    def on_zoom_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"

    def zoom_in(self):
        if self.scale_factor < 2.0:
            self.scale_factor = round(self.scale_factor + 0.1, 1)
            self.apply_scaling()

    def zoom_out(self):
        if self.scale_factor > 0.5:
            self.scale_factor = round(self.scale_factor - 0.1, 1)
            self.apply_scaling()

    def reset_zoom(self):
        self.scale_factor = 1.0
        self.apply_scaling()

    def apply_scaling(self):
        if self.scale_factor > 1.0:
            bw, bh = 1600, 900
            self.root.geometry(f"{int(bw * self.scale_factor)}x{int(bh * self.scale_factor)}")

        self._update_grid_configuration()

        for sf in self.semester_frames:
            if hasattr(sf, 'set_scale_factor'):
                sf.set_scale_factor(self.scale_factor)

        if hasattr(self, 'course_list') and hasattr(self.course_list, 'apply_scaling'):
            self.course_list.apply_scaling(self.scale_factor)

        if hasattr(self, 'graduation_requirements') and hasattr(self.graduation_requirements, 'apply_scaling'):
            self.graduation_requirements.apply_scaling(self.scale_factor)

        if hasattr(self, 'view_menu'):
            pct = int(self.scale_factor * 100)
            try:
                for i in range(self.view_menu.index("end") + 1):
                    try:
                        lbl = self.view_menu.entrycget(i, "label")
                        if lbl.startswith("Zoom:"):
                            self.view_menu.entryconfig(i, label=f"Zoom: {pct}%")
                            break
                    except tk.TclError:
                        continue
            except tk.TclError:
                pass

        self.root.update_idletasks()

    def _update_grid_configuration(self):
        if not hasattr(self, 'semesters_frame'):
            return
        base = 250
        scale = max(0.5, self.scale_factor)
        minsize = max(100, int(base * scale))
        for j in range(6):
            self.semesters_frame.grid_columnconfigure(j, weight=1, minsize=minsize)

    # ==================================================================
    #  Widget creation
    # ==================================================================
    def create_widgets(self):
        # --- Menu bar -----------------------------------------------------
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Speichern", command=self.save_state, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Kurs hinzuf\u00fcgen\u2026", command=self.add_course_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.on_close)
        menu_bar.add_cascade(label="Datei", menu=file_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Vergr\u00f6\u00dfern", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Verkleinern", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Zoom zur\u00fccksetzen", command=self.reset_zoom, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label=f"Zoom: {int(self.scale_factor * 100)}%", state="disabled")
        menu_bar.add_cascade(label="Ansicht", menu=view_menu)

        self.root.config(menu=menu_bar)
        self.view_menu = view_menu
        self.root.bind("<Control-s>", lambda e: self.save_state())

        # --- Status / save bar --------------------------------------------
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.TOP, pady=(4, 8), padx=8)

        left_section = ttk.Frame(status_frame)
        left_section.pack(side=tk.LEFT, fill=tk.X)

        ttk.Label(left_section, text="Speicherplatz:").pack(side=tk.LEFT, padx=(0, 4))
        self.slot_var = tk.StringVar(value=self.current_slot)
        self.slot_combo = ttk.Combobox(
            left_section, textvariable=self.slot_var,
            values=self.available_slots, width=15)
        self.slot_combo.pack(side=tk.LEFT, padx=4)
        self.slot_combo.bind("<<ComboboxSelected>>", self.on_slot_selected)

        btns = ttk.Frame(left_section)
        btns.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0))
        for txt, cmd in [("Neu", self.create_new_slot),
                         ("Umbenennen", self.rename_slot),
                         ("Kopieren", self.duplicate_slot),
                         ("L\u00f6schen", self.delete_slot)]:
            ttk.Button(btns, text=txt, width=9, command=cmd).pack(side=tk.LEFT, padx=2)

        ttk.Button(status_frame, text="Speichern", style="Accent.TButton",
                   command=self.save_state).pack(side=tk.RIGHT, padx=4)

        # --- Main horizontal pane -----------------------------------------
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Left panel — course list
        left_panel = ttk.Frame(main_container)
        self.course_list = CourseList(left_panel, self.courses,
                                     self.drag_drop_manager,
                                     on_add_course=self.add_course_dialog)
        self.course_list.pack(fill=tk.BOTH, expand=True)

        # Right panel — semesters + requirements
        right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)

        semester_panel = ttk.Frame(right_panel)

        semester_scroll_frame = ttk.Frame(semester_panel)
        semester_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.semester_canvas = tk.Canvas(semester_scroll_frame, highlightthickness=0)
        h_scrollbar = ttk.Scrollbar(semester_scroll_frame, orient="horizontal",
                                    command=self.semester_canvas.xview)
        self.semester_canvas.configure(xscrollcommand=h_scrollbar.set)
        self.semester_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.semesters_frame = ttk.Frame(self.semester_canvas)
        self.canvas_window = self.semester_canvas.create_window(
            (0, 0), window=self.semesters_frame, anchor="nw",
            tags="semester_frames")

        self.semesters_frame.bind(
            "<Configure>",
            lambda e: self.semester_canvas.configure(
                scrollregion=self.semester_canvas.bbox("all")))
        self.semester_canvas.bind("<Configure>", self._on_semester_canvas_configure)

        self.semester_canvas.bind("<MouseWheel>", self._on_horizontal_mousewheel)
        self.semesters_frame.bind("<MouseWheel>", self._on_horizontal_mousewheel)

        self.create_semesters()

        # Requirements
        self.requirements_panel = ttk.LabelFrame(right_panel, text="Studienfortschritt")
        self.graduation_requirements = GraduationRequirementsFrame(
            self.requirements_panel, self)
        self.graduation_requirements.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        right_panel.add(semester_panel, weight=3)
        right_panel.add(self.requirements_panel, weight=1)

        main_container.add(left_panel, weight=1)
        main_container.add(right_panel, weight=3)

        self.root.update_idletasks()
        self.root.after(100, lambda: main_container.sashpos(0, 300))

    def _on_semester_canvas_configure(self, event):
        """Stretch semesters_frame to fill available width."""
        self.semester_canvas.itemconfig(self.canvas_window,
                                       height=event.height,
                                       width=max(event.width,
                                                 self.semesters_frame.winfo_reqwidth()))

    def _on_horizontal_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.semester_canvas.xview_scroll(delta, "units")
        return "break"

    # ==================================================================
    #  Semesters
    # ==================================================================
    def create_semesters(self):
        self.semester_frames = []
        for j in range(6):
            self.semesters_frame.grid_columnconfigure(j, weight=1, minsize=250)
            if j % 2 == 0:
                year = 2025 + (j // 2)
                title = f"SoSe {year}"
            else:
                year = 2025 + (j // 2)
                title = f"WiSe {year}/{year + 1}"
            sf = SemesterFrame(self.semesters_frame, title, 30,
                               self.drag_drop_manager)
            sf.grid(row=0, column=j, sticky="nsew", padx=4, pady=4)
            self.semester_frames.append(sf)

    # ==================================================================
    #  Add-course dialog
    # ==================================================================
    def add_course_dialog(self):
        """Open a dialog to create a new custom course."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Kurs hinzuf\u00fcgen")
        dlg.geometry("420x400")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()

        pad = dict(padx=8, pady=4)
        row = 0

        fields = {}
        for label, key, default, width in [
            ("Titel *", "title", "", 35),
            ("Modulcode *", "module_code", "", 15),
            ("LP (Credits) *", "credits", "6", 6),
        ]:
            ttk.Label(dlg, text=label).grid(row=row, column=0, sticky="w", **pad)
            var = tk.StringVar(value=default)
            ttk.Entry(dlg, textvariable=var, width=width).grid(
                row=row, column=1, sticky="ew", **pad)
            fields[key] = var
            row += 1

        # Group dropdown
        groups = sorted({c.group for c in self.courses if c.group})
        ttk.Label(dlg, text="Gruppe *").grid(row=row, column=0, sticky="w", **pad)
        group_var = tk.StringVar(value=groups[0] if groups else "7. Freie Wahlmodule")
        group_combo = ttk.Combobox(dlg, textvariable=group_var, values=groups, width=33)
        group_combo.grid(row=row, column=1, sticky="ew", **pad)
        fields["group"] = group_var
        row += 1

        # Semester dropdown
        ttk.Label(dlg, text="Angebot").grid(row=row, column=0, sticky="w", **pad)
        sem_var = tk.StringVar(value="WiSe/SoSe")
        ttk.Combobox(dlg, textvariable=sem_var,
                      values=["WiSe", "SoSe", "WiSe/SoSe", "k.A."],
                      state="readonly", width=15).grid(
            row=row, column=1, sticky="w", **pad)
        fields["semester"] = sem_var
        row += 1

        # Exam type
        ttk.Label(dlg, text="Pr\u00fcfungsform").grid(row=row, column=0, sticky="w", **pad)
        exam_var = tk.StringVar(value="k.A.")
        ttk.Combobox(dlg, textvariable=exam_var,
                      values=["Schriftliche Pr\u00fcfung", "M\u00fcndliche Pr\u00fcfung",
                              "Portfoliopr\u00fcfung", "Keine Pr\u00fcfung", "k.A."],
                      width=25).grid(row=row, column=1, sticky="w", **pad)
        fields["exam_type"] = exam_var
        row += 1

        # Grading
        ttk.Label(dlg, text="Benotung").grid(row=row, column=0, sticky="w", **pad)
        grade_var = tk.StringVar(value="Benotet")
        ttk.Combobox(dlg, textvariable=grade_var,
                      values=["Benotet", "Unbenotet", "k.A."],
                      state="readonly", width=12).grid(
            row=row, column=1, sticky="w", **pad)
        fields["grading"] = grade_var
        row += 1

        dlg.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(dlg)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=12)

        def on_ok():
            title = fields["title"].get().strip()
            code = fields["module_code"].get().strip()
            try:
                credits = int(fields["credits"].get().strip())
            except ValueError:
                messagebox.showerror("Fehler", "LP muss eine Zahl sein.", parent=dlg)
                return
            if not title or not code:
                messagebox.showerror("Fehler", "Titel und Modulcode sind Pflichtfelder.", parent=dlg)
                return
            # Check uniqueness
            if any(c.module_code == code for c in self.courses):
                messagebox.showerror("Fehler", f"Modulcode '{code}' existiert bereits.", parent=dlg)
                return

            course = Course(
                title=title, credits=credits,
                module_code=code,
                group=fields["group"].get(),
                semester=fields["semester"].get(),
                exam_type=fields["exam_type"].get(),
                grading=fields["grading"].get())
            self.courses.append(course)

            # Persist to courses.json
            self._save_courses_json()

            # Refresh UI
            self.course_list.filtered_courses = self.courses.copy()
            self.course_list.update_filter_combos()
            self.course_list.display_courses()
            dlg.destroy()

        ttk.Button(btn_frame, text="Hinzuf\u00fcgen", style="Accent.TButton",
                   command=on_ok).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Abbrechen",
                   command=dlg.destroy).pack(side=tk.LEFT, padx=8)

        dlg.bind("<Return>", lambda e: on_ok())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def _save_courses_json(self):
        """Write all courses back to courses.json."""
        path = os.path.join(self.resources_dir, 'courses.json')
        data = [c.to_dict() for c in self.courses]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ==================================================================
    #  Save-slot management
    # ==================================================================
    def get_available_slots(self):
        slots = ["Default"]
        try:
            if os.path.exists(self.save_dir):
                for fn in os.listdir(self.save_dir):
                    if fn.endswith(".json"):
                        name = fn[:-5]
                        if name != "Default":
                            slots.append(name)
        except Exception:
            pass
        return sorted(slots)

    def update_slot_selector(self):
        if hasattr(self, 'slot_combo'):
            self.available_slots = self.get_available_slots()
            self.slot_combo['values'] = self.available_slots

    def on_slot_selected(self, event):
        selected = self.slot_var.get()
        if selected != self.current_slot:
            if messagebox.askyesno("Speicherplatz wechseln",
                                   "Wirklich wechseln?\nUngespeicherte \u00c4nderungen gehen verloren."):
                self.root.config(cursor="watch")
                self.root.after_idle(lambda: self._perform_slot_switch(selected))
            else:
                self.slot_var.set(self.current_slot)

    def _perform_slot_switch(self, selected):
        try:
            self.current_slot = selected
            self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")

            original_search = None
            if hasattr(self.course_list, 'search_var'):
                original_search = self.course_list.search_var.get()
                self.course_list.search_var.set("__LOADING__")

            self.clear_semesters()
            self.load_state()

            if original_search is not None:
                self.root.after(100, lambda: self.course_list.search_var.set(
                    original_search if original_search != "__LOADING__" else ""))
        except Exception as e:
            messagebox.showerror("Fehler", f"Wechsel fehlgeschlagen: {e}")
            self.root.config(cursor="")

    def create_new_slot(self):
        name = simpledialog.askstring("Neuer Speicherplatz",
                                      "Name f\u00fcr den neuen Speicherplatz:", parent=self.root)
        if not name:
            return
        name = "".join(c for c in name if c.isalnum() or c in ' _-')
        if name in self.available_slots:
            messagebox.showerror("Fehler", f"'{name}' existiert bereits!")
            return
        self.current_slot = name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        self.clear_semesters()
        self.save_state()
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)

    def rename_slot(self):
        if self.current_slot == "Default":
            messagebox.showerror("Fehler", "Der Standard-Speicherplatz kann nicht umbenannt werden!")
            return
        new = simpledialog.askstring("Umbenennen", "Neuer Name:",
                                     parent=self.root, initialvalue=self.current_slot)
        if not new:
            return
        new = "".join(c for c in new if c.isalnum() or c in ' _-')
        if new in self.available_slots and new != self.current_slot:
            messagebox.showerror("Fehler", f"'{new}' existiert bereits!")
            return
        old_file = self.state_file
        self.current_slot = new
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        if os.path.exists(old_file):
            try:
                os.rename(old_file, self.state_file)
            except Exception:
                self.save_state()
        else:
            self.save_state()
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)

    def delete_slot(self):
        if self.current_slot == "Default":
            messagebox.showerror("Fehler", "Der Standard-Speicherplatz kann nicht gel\u00f6scht werden!")
            return
        if messagebox.askyesno("L\u00f6schen",
                               f"'{self.current_slot}' wirklich l\u00f6schen?\nDies kann nicht r\u00fcckg\u00e4ngig gemacht werden."):
            try:
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
            except Exception:
                pass
            self.current_slot = "Default"
            self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
            self.clear_semesters()
            self.load_state()
            self.update_slot_selector()
            self.slot_var.set(self.current_slot)

    def duplicate_slot(self):
        base = f"{self.current_slot}_Kopie"
        name, n = base, 1
        while name in self.available_slots:
            name = f"{base}_{n}"; n += 1
        self.save_state()
        if os.path.exists(self.state_file):
            try:
                shutil.copy2(self.state_file,
                             os.path.join(self.save_dir, f"{name}.json"))
            except Exception:
                return
        self.current_slot = name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)

    # ==================================================================
    #  State persistence
    # ==================================================================
    def clear_semesters(self):
        for sf in self.semester_frames:
            for c in sf.courses.copy():
                sf.remove_course(c)

    def on_close(self):
        self.save_state()
        self.root.destroy()

    def save_state(self):
        try:
            state = {
                "semester_assignments": {},
                "expanded_groups": self.course_list.expanded_groups,
                "favorites": [],
                "window": {
                    "width": self.root.winfo_width(),
                    "height": self.root.winfo_height(),
                },
            }
            for i, sf in enumerate(self.semester_frames):
                codes = [c.module_code for c in sf.courses
                         if hasattr(c, 'module_code') and c.module_code]
                state["semester_assignments"][str(i)] = codes
            for c in self.courses:
                if getattr(c, 'favorite', False) and getattr(c, 'module_code', None):
                    state["favorites"].append(c.module_code)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            self.root.title(f"Semester Calendar Planner \u2014 {self.current_slot}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

    def load_state(self):
        if not os.path.exists(self.state_file):
            self.save_state()
            return
        try:
            self.root.withdraw()
            self.root.config(cursor="watch")
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            if "window" in state:
                w = state["window"].get("width", 1600)
                h = state["window"].get("height", 900)
                self.root.geometry(f"{w}x{h}")

            original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')

            by_code = {c.module_code: c for c in self.courses
                       if getattr(c, 'module_code', None)}

            if "favorites" in state:
                for mc in state["favorites"]:
                    if mc in by_code:
                        by_code[mc].favorite = True

            if "expanded_groups" in state and hasattr(self, "course_list"):
                self.course_list.expanded_groups = state["expanded_groups"]

            orig_update = None
            if hasattr(self.drag_drop_manager, 'app'):
                orig_update = self.drag_drop_manager.app.update_graduation_requirements
                self.drag_drop_manager.app.update_graduation_requirements = lambda: None

            semester_data = {}
            if "semester_assignments" in state:
                for idx_s, codes in state["semester_assignments"].items():
                    idx = int(idx_s)
                    if idx < len(self.semester_frames):
                        sf = self.semester_frames[idx]
                        semester_data[idx] = []
                        for code in codes:
                            if code in by_code:
                                c = by_code[code]
                                sf.courses.append(c)
                                c.assigned_semester = sf
                                semester_data[idx].append(c)

            if hasattr(self, "course_list"):
                self.course_list.display_courses()

            for idx, courses in semester_data.items():
                sf = self.semester_frames[idx]
                sf.total_credits = sum(c.credits for c in sf.courses)
                for c in courses:
                    cb = CourseBlock(sf.course_container, c, self.drag_drop_manager,
                                    in_semester=True)
                    sf.course_blocks[c] = cb
                for _, blk in sf.course_blocks.items():
                    blk.pack(fill=tk.X, pady=3, padx=2)
                sf.update_total_credits()
                sf._configure_scroll_region()

            if orig_update:
                self.drag_drop_manager.app.update_graduation_requirements = orig_update

            sys.stdout = original_stdout
            self.root.title(f"Semester Calendar Planner \u2014 {self.current_slot}")
            self.root.deiconify()
            self.root.config(cursor="")
            self.update_graduation_requirements()
        except Exception as e:
            self.root.deiconify()
            self.root.config(cursor="")
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Laden fehlgeschlagen: {e}")

    # ==================================================================
    #  Course loading
    # ==================================================================
    def load_courses(self):
        try:
            path = os.path.join(self.resources_dir, 'courses.json')
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for d in data:
                if 'title' in d:
                    self.courses.append(Course(
                        title=d.get('title', 'Unnamed'),
                        credits=d.get('credits', 0),
                        exam_type=d.get('exam_type', ''),
                        group=d.get('group', ''),
                        module_code=d.get('module_code', ''),
                        grading=d.get('grading', ''),
                        semester=d.get('semester', '')))
        except Exception as e:
            messagebox.showerror("Fehler", f"Kurse konnten nicht geladen werden: {e}")

    def update_graduation_requirements(self):
        if hasattr(self, 'graduation_requirements'):
            self.graduation_requirements.update_requirements()
