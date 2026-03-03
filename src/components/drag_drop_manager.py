import tkinter as tk
from tkinter import messagebox


class DragDropManager:
    def __init__(self, app):
        self.app = app
        self.dragging = False
        self.dragged_item = None
        self.temp_window = None
        self.start_x = 0
        self.start_y = 0
        self.target_container = None
        self.potential_targets = []
        self.original_colors = {}

    def register_drop_target(self, target):
        """Register a frame as a potential drop target."""
        self.potential_targets.append(target)
        self.original_colors[target] = target.cget("background")

    def start_drag(self, event, item):
        """Start dragging an item."""
        if not hasattr(item, 'course'):
            return

        self.dragging = True
        self.dragged_item = item
        self.dragged_widget = event.widget
        self.start_x = event.x_root
        self.start_y = event.y_root

        self.temp_window = tk.Toplevel(event.widget)
        self.temp_window.overrideredirect(True)

        course = item.course
        title_label = tk.Label(
            self.temp_window, text=course.title,
            font=("Segoe UI", 10), bg="#E0E0E0",
            bd=1, relief=tk.RAISED, padx=6, pady=3)
        title_label.pack()

        self.temp_window.geometry(f"+{event.x_root - 10}+{event.y_root - 10}")

        self.app.root.bind("<B1-Motion>", self.drag)
        self.app.root.bind("<ButtonRelease-1>", lambda e: self.end_drag())

    def drag(self, event):
        """Update drag position and highlight potential drop targets."""
        if not self.dragging or not self.temp_window:
            return

        x, y = event.x_root, event.y_root
        self.temp_window.geometry(f"+{x - 10}+{y - 10}")

        # Reset highlights
        for target in self.potential_targets:
            if target in self.original_colors:
                target.configure(background=self.original_colors[target])

        self.target_container = None

        for target in self.potential_targets:
            try:
                x1 = target.winfo_rootx()
                y1 = target.winfo_rooty()
                x2 = x1 + target.winfo_width()
                y2 = y1 + target.winfo_height()

                margin = 10
                if x >= x1 - margin and x <= x2 + margin and y >= y1 and y <= y2:
                    self.target_container = target

                    if self.dragged_item and hasattr(self.dragged_item, 'course'):
                        course = self.dragged_item.course
                        if hasattr(course, 'semester') and hasattr(target, 'title'):
                            compatible = is_compatible_semester(
                                course.semester, target.title)
                            if compatible:
                                target.configure(background="#D5F5E3")
                            else:
                                target.configure(background="#FADBD8")
                        else:
                            target.configure(background="#CCE5FF")
                    else:
                        target.configure(background="#CCE5FF")
                    break
            except tk.TclError:
                continue

        return "break"

    def end_drag(self):
        """End dragging and process the drop."""
        for target in self.potential_targets:
            if target in self.original_colors:
                target.configure(background=self.original_colors[target])

        if not self.dragging:
            if self.temp_window:
                self.temp_window.destroy()
                self.temp_window = None
            return

        if self.dragged_item:
            course = self.dragged_item.course

            if hasattr(course, 'assigned_semester') and course.assigned_semester:
                try:
                    course.assigned_semester.remove_course(course)
                except Exception:
                    pass

            if self.target_container:
                is_compatible = True
                if hasattr(course, 'semester') and hasattr(self.target_container, 'title'):
                    is_compatible = is_compatible_semester(
                        course.semester, self.target_container.title)

                if is_compatible:
                    self.target_container.add_course(course)
                else:
                    messagebox.showwarning(
                        "Inkompatibles Semester",
                        f"Dieser Kurs ({course.title}) wird nur im "
                        f"{course.semester} angeboten.")

        if self.temp_window:
            self.temp_window.destroy()
            self.temp_window = None

        self.dragging = False
        self.dragged_item = None
        self.target_container = None


def is_compatible_semester(course_semester, target_semester_title):
    """Check if a course can be placed in a given semester."""
    if not course_semester:
        return True

    target_type = "SoSe" if "SoSe" in target_semester_title else "WiSe"

    if "SoSe/WiSe" in course_semester or "WiSe/SoSe" in course_semester:
        return True
    if course_semester == "SoSe" and target_type == "SoSe":
        return True
    if course_semester == "WiSe" and target_type == "WiSe":
        return True
    return False
