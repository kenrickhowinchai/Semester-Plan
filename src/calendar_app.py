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
        
        # Initialize scaling system
        self.scale_factor = 1.0
        self.base_fonts = {}  # Store original font sizes
        self.setup_scaling()
        
        # Create resources directory if it doesn't exist
        self.resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
        self.save_dir = os.path.join(self.resources_dir, 'saves')
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Initialize slot system
        self.current_slot = "Default"
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Get available save slots - do this BEFORE creating widgets
        self.available_slots = self.get_available_slots()
        
        # Initialize drag-drop manager
        self.drag_drop_manager = DragDropManager(self)
        
        # Initialize courses
        self.courses = []
        self.semester_frames = []  # Keep track of all semester frames
        self.load_courses()
        
        # Create UI with save slots
        self.create_widgets()
        
        # Apply initial scaling to ensure everything is properly sized
        self.apply_scaling()
        
        # Load saved state if it exists
        self.load_state()
        
        # Bind save state to window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_scaling(self):
        """Setup the scaling system with keyboard bindings"""
        # Bind keyboard shortcuts for zooming
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())  # + key without shift
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())
        
        # Bind mouse wheel with Ctrl for zooming
        self.root.bind("<Control-MouseWheel>", self.on_zoom_mousewheel)
        
        # Bind mouse wheel without Ctrl for manual scaling (alternative method)
        self.root.bind("<MouseWheel>", self.on_manual_mousewheel)
        
        # Focus the root window to ensure it can receive key events
        self.root.focus_set()
    
    def on_manual_mousewheel(self, event):
        """Handle plain mouse wheel for manual scaling (when not scrolling)"""
        # Only scale if the mouse is over the main area, not over scrollable content
        widget_under_mouse = event.widget
        widget_class = widget_under_mouse.winfo_class()
        
        # Don't intercept scrolling for scrollable widgets
        if widget_class in ['Canvas', 'Text', 'Listbox'] or 'scroll' in str(widget_under_mouse).lower():
            return  # Let normal scrolling happen
        
        # Check if Shift is held for manual scaling
        if event.state & 0x1:  # Shift key is held
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            return "break"  # Prevent normal scrolling
    
    def on_zoom_mousewheel(self, event):
        """Handle Ctrl+MouseWheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        return "break"
    
    def zoom_in(self):
        """Increase the scale factor"""
        if self.scale_factor < 2.0:  # Limit maximum zoom
            self.scale_factor += 0.1
            self.apply_scaling()
    
    def zoom_out(self):
        """Decrease the scale factor"""
        if self.scale_factor > 0.5:  # Limit minimum zoom
            self.scale_factor -= 0.1
            self.apply_scaling()
    
    def reset_zoom(self):
        """Reset zoom to default"""
        self.scale_factor = 1.0
        self.apply_scaling()
    
    def apply_scaling(self):
        """Apply the current scale factor to all UI elements"""
        # Don't scale the window size - let it stay the same so more content fits
        # when scaling down. Only scale window up when zooming in beyond 100%
        if self.scale_factor > 1.0:
            base_width, base_height = 1600, 900
            new_width = int(base_width * self.scale_factor)
            new_height = int(base_height * self.scale_factor)
            self.root.geometry(f"{new_width}x{new_height}")
        # When scaling down, keep the window size to show more content
        
        # Update grid column configuration for semester frames with scaling
        self._update_grid_configuration()
        
        # Apply direct scaling to all widgets
        self._scale_all_widgets_directly(self.root)
        
        # Apply scaling to all semester frames (ensure they scale with course blocks)
        for semester_frame in self.semester_frames:
            if hasattr(semester_frame, 'set_scale_factor'):
                semester_frame.set_scale_factor(self.scale_factor)
        
        # Apply scaling to course list
        if hasattr(self, 'course_list') and hasattr(self.course_list, 'apply_scaling'):
            self.course_list.apply_scaling(self.scale_factor)
        
        # Apply scaling to graduation requirements
        if hasattr(self, 'graduation_requirements') and hasattr(self.graduation_requirements, 'apply_scaling'):
            self.graduation_requirements.apply_scaling(self.scale_factor)
        
        # Update zoom percentage in menu
        if hasattr(self, 'view_menu'):
            zoom_percentage = int(self.scale_factor * 100)
            try:
                # Find and update the zoom percentage menu item
                for i in range(self.view_menu.index("end") + 1):
                    try:
                        label = self.view_menu.entrycget(i, "label")
                        if label.startswith("Current Zoom:"):
                            self.view_menu.entryconfig(i, label=f"Current Zoom: {zoom_percentage}%")
                            break
                    except tk.TclError:
                        continue
            except tk.TclError:
                pass
        
        # Force a redraw
        self.root.update_idletasks()
    
    def _update_grid_configuration(self):
        """Update grid column configuration for semester frames based on scale factor"""
        if hasattr(self, 'semesters_frame'):
            # Calculate scaled minimum size - make it scale aggressively for width
            base_minsize = 250
            
            if self.scale_factor < 1.0:
                # Aggressive scaling for zoom out - same as semester frame width scaling
                width_scale = self.scale_factor ** 3.0
                new_minsize = max(30, int(base_minsize * width_scale))
            else:
                # Normal scaling for zoom in
                width_scale = self.scale_factor ** 1.5
                new_minsize = int(base_minsize * width_scale)
            
            # Debug output (can be removed later)
            # print(f"Grid scaling: factor={self.scale_factor:.2f}, new_minsize={new_minsize}")
            
            # Update all column configurations
            for j in range(6):  # 6 columns for 6 semesters
                self.semesters_frame.grid_columnconfigure(j, weight=1, minsize=new_minsize)
    
    def _scale_all_widgets_directly(self, widget):
        """Apply scaling to all widgets with a direct, simple approach"""
        try:
            # Configure widget-specific scaling based on type
            widget_class = widget.winfo_class()
            
            # Handle fonts for all widgets that support them
            self._scale_widget_font(widget)
            
            # Handle dimensions for specific widget types
            if widget_class in ['Button', 'Label', 'Entry']:
                self._scale_widget_dimensions(widget, base_width=15, base_height=1)
            elif widget_class == 'Canvas':
                self._scale_widget_dimensions(widget, base_width=160, base_height=500)  # Match semester frame base width
            elif widget_class == 'Text':
                self._scale_widget_dimensions(widget, base_width=40, base_height=10)
            elif widget_class in ['TButton', 'TLabel', 'TEntry', 'TCombobox']:
                # TTK widgets - handle differently
                self._scale_ttk_widget(widget)
            
        except tk.TclError:
            pass
        
        # Recursively apply to children
        try:
            for child in widget.winfo_children():
                self._scale_all_widgets_directly(child)
        except tk.TclError:
            pass
    
    def _scale_widget_font(self, widget):
        """Scale font for a single widget"""
        try:
            current_font = widget.cget("font")
            if not current_font or current_font == "":
                # Set a default font with scaling
                base_size = 9
                new_size = max(6, int(base_size * self.scale_factor))
                widget.configure(font=("TkDefaultFont", new_size))
            else:
                # Parse and scale existing font
                if isinstance(current_font, str):
                    # Handle various font string formats
                    if current_font.startswith(("TkDefault", "TkText", "TkFixed")):
                        # System fonts
                        base_size = 9
                        new_size = max(6, int(base_size * self.scale_factor))
                        widget.configure(font=(current_font, new_size))
                    else:
                        # Custom font strings like "Helvetica 12 bold"
                        parts = current_font.split()
                        if len(parts) >= 2:
                            try:
                                family = parts[0]
                                size = int(parts[1])
                                new_size = max(6, int(size * self.scale_factor))
                                style = " ".join(parts[2:]) if len(parts) > 2 else ""
                                new_font = f"{family} {new_size} {style}".strip()
                                widget.configure(font=new_font)
                            except (ValueError, IndexError):
                                # Fallback for unparseable font strings
                                base_size = 9
                                new_size = max(6, int(base_size * self.scale_factor))
                                widget.configure(font=("TkDefaultFont", new_size))
                elif isinstance(current_font, (tuple, list)) and len(current_font) >= 2:
                    family, size = current_font[0], current_font[1]
                    new_size = max(6, int(size * self.scale_factor))
                    new_font = (family, new_size)
                    if len(current_font) > 2:
                        new_font = new_font + current_font[2:]
                    widget.configure(font=new_font)
                else:
                    # Fallback for unknown font types
                    base_size = 9
                    new_size = max(6, int(base_size * self.scale_factor))
                    widget.configure(font=("TkDefaultFont", new_size))
        except (tk.TclError, AttributeError, ValueError):
            # Fallback if font configuration fails
            try:
                base_size = 9
                new_size = max(6, int(base_size * self.scale_factor))
                widget.configure(font=("TkDefaultFont", new_size))
            except tk.TclError:
                pass
    
    def _scale_widget_dimensions(self, widget, base_width=10, base_height=1):
        """Scale dimensions for a single widget"""
        try:
            # Scale width
            try:
                current_width = widget.cget("width")
                if current_width and current_width > 0:
                    new_width = max(1, int(current_width * self.scale_factor))
                else:
                    new_width = max(1, int(base_width * self.scale_factor))
                widget.configure(width=new_width)
            except (tk.TclError, ValueError, TypeError):
                pass
            
            # Scale height
            try:
                current_height = widget.cget("height")
                if current_height and current_height > 0:
                    new_height = max(1, int(current_height * self.scale_factor))
                else:
                    new_height = max(1, int(base_height * self.scale_factor))
                widget.configure(height=new_height)
            except (tk.TclError, ValueError, TypeError):
                pass
                
        except tk.TclError:
            pass
    
    def _scale_ttk_widget(self, widget):
        """Special handling for TTK widgets"""
        try:
            # TTK widgets need style-based scaling
            style = ttk.Style()
            widget_class = widget.winfo_class()
            
            # Configure font for TTK widgets
            base_size = 9
            new_size = max(6, int(base_size * self.scale_factor))
            
            if widget_class == 'TButton':
                style.configure('TButton', font=('TkDefaultFont', new_size))
            elif widget_class == 'TLabel':
                style.configure('TLabel', font=('TkDefaultFont', new_size))
            elif widget_class == 'TEntry':
                style.configure('TEntry', font=('TkDefaultFont', new_size))
            elif widget_class == 'TCombobox':
                style.configure('TCombobox', font=('TkDefaultFont', new_size))
                
        except (tk.TclError, AttributeError):
            pass
    
    def update_font_scaling(self):
        """Simplified font scaling - this method is now handled by apply_scaling"""
        pass  # This functionality is now in _scale_all_widgets_directly
    
    def _store_original_dimensions(self, widget):
        """Deprecated - original dimension storage is no longer used"""
        pass  # This functionality has been replaced by direct scaling
    
    def _update_widget_scaling(self, widget):
        """Deprecated - complex widget scaling is no longer used"""
        pass  # This functionality has been replaced by direct scaling
    
    def create_widgets(self):
        """Create the UI elements"""
        # Create a menu bar
        menu_bar = tk.Menu(self.root)
        # Add menus to the menu bar
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_state)
        file_menu.add_command(label="Exit", command=self.on_close)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Add View menu for zoom controls
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label=f"Current Zoom: {int(self.scale_factor * 100)}%", state="disabled")
        menu_bar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menu_bar)
        self.view_menu = view_menu  # Keep reference to update zoom percentage
        
        # Add status/save bar at the TOP instead of the bottom
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.TOP, pady=(5, 10))  # TOP instead of BOTTOM
        
        # Create a left section for save slots
        left_section = ttk.Frame(status_frame)
        left_section.pack(side=tk.LEFT, fill=tk.X)
        
        # Add save slot selector to status bar
        ttk.Label(left_section, text="Save Slot:").pack(side=tk.LEFT, padx=5)
        self.slot_var = tk.StringVar(value=self.current_slot)
        self.slot_combo = ttk.Combobox(
            left_section, 
            textvariable=self.slot_var,
            values=self.available_slots,
            width=15
        )
        self.slot_combo.pack(side=tk.LEFT, padx=5)
        self.slot_combo.bind("<<ComboboxSelected>>", self.on_slot_selected)
        
        # Add slot management buttons
        slot_buttons_frame = ttk.Frame(left_section)
        slot_buttons_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Create buttons with appropriate icons or text
        ttk.Button(slot_buttons_frame, text="New", width=6, 
                   command=self.create_new_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Rename", width=6, 
                   command=self.rename_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Copy", width=6, 
                   command=self.duplicate_slot).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(slot_buttons_frame, text="Delete", width=6, 
                   command=self.delete_slot).pack(side=tk.LEFT, padx=2)
        
        # Add save button on the right
        ttk.Button(status_frame, text="Save", command=self.save_state).pack(side=tk.RIGHT, padx=5)
        
        # Create main container as a PanedWindow for resizable sections
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left panel for course list
        left_panel = ttk.Frame(main_container)
        
        # Create course list
        self.course_list = CourseList(left_panel, self.courses, self.drag_drop_manager)
        self.course_list.pack(fill=tk.BOTH, expand=True)
        
        # Create right panel for semesters and requirements as a vertical PanedWindow
        # This allows the user to resize the graduation requirements section
        right_panel = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        
        # Add semester panel to right panel
        semester_panel = ttk.Frame(right_panel)
        
        # Create horizontal scrollable frame for semesters
        semester_scroll_frame = ttk.Frame(semester_panel)
        semester_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for horizontal scrolling of semesters
        self.semester_canvas = tk.Canvas(semester_scroll_frame)
        h_scrollbar = ttk.Scrollbar(semester_scroll_frame, orient="horizontal", command=self.semester_canvas.xview)
        
        # Configure the canvas
        self.semester_canvas.configure(xscrollcommand=h_scrollbar.set)
        self.semester_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create frame to hold semester frames
        self.semesters_frame = ttk.Frame(self.semester_canvas)
        self.canvas_window = self.semester_canvas.create_window(
            (0, 0), 
            window=self.semesters_frame,
            anchor="nw",
            tags="semester_frames"
        )
        
        # Update scroll region when the size changes
        self.semesters_frame.bind("<Configure>", 
                             lambda e: self.semester_canvas.configure(scrollregion=self.semester_canvas.bbox("all")))
        self.semester_canvas.bind("<Configure>", 
                              lambda e: self.semester_canvas.itemconfig(self.canvas_window, height=e.height))
        
        # Bind mousewheel to horizontal scroll
        self.semester_canvas.bind("<MouseWheel>", self._on_horizontal_mousewheel)
        self.semesters_frame.bind("<MouseWheel>", self._on_horizontal_mousewheel)
        
        # Create semester frames
        self.create_semesters()
        
        # Add requirements panel as a resizable section
        self.requirements_panel = ttk.LabelFrame(right_panel, text="Graduation Requirements")
        
        # Create graduation requirements display
        self.graduation_requirements = GraduationRequirementsFrame(self.requirements_panel, self)
        self.graduation_requirements.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add both panels to the vertical PanedWindow
        right_panel.add(semester_panel, weight=3)  # 75% initial height for semesters
        right_panel.add(self.requirements_panel, weight=1)  # 25% initial height for requirements
        
        # Add both main panels to the horizontal PanedWindow
        main_container.add(left_panel, weight=1)
        main_container.add(right_panel, weight=3)
        
        # Set initial sash positions after a short delay to ensure widgets are fully created
        self.root.update_idletasks()
        self.root.after(100, lambda: main_container.sashpos(0, 280))  # Position horizontal sash
    
    def _on_horizontal_mousewheel(self, event):
        """Handle mousewheel events for horizontal scrolling"""
        delta = 0
        if hasattr(event, 'num') and event.num == 5 or event.delta < 0:  # Scroll down/right
            delta = 1
        elif hasattr(event, 'num') and event.num == 4 or event.delta > 0:  # Scroll up/left
            delta = -1
            
        self.semester_canvas.xview_scroll(delta, "units")
        return "break"  # Prevent propagation to parent widget
    
    def get_available_slots(self):
        """Get a list of available save slots"""
        slots = ["Default"]  # Always include Default
        
        try:
            # Get all JSON files in the saves directory
            if os.path.exists(self.save_dir):
                for filename in os.listdir(self.save_dir):
                    if filename.endswith(".json"):
                        slot_name = filename[:-5]  # Remove .json extension
                        if slot_name != "Default":  # Already included
                            slots.append(slot_name)
        except Exception as e:
            print(f"Error getting save slots: {e}")
            
        return sorted(slots)
    
    def update_slot_selector(self):
        """Update the save slot dropdown with current available slots"""
        # Use slot_combo instead of slot_selector for consistency
        if hasattr(self, 'slot_combo'):
            self.slot_combo['values'] = self.available_slots
            if self.current_slot not in self.available_slots:
                self.available_slots.append(self.current_slot)
                self.slot_combo['values'] = self.available_slots
    
    def on_slot_selected(self, event):
        """Handle selection of a different save slot"""
        selected_slot = self.slot_var.get()
        
        if selected_slot != self.current_slot:
            # Ask for confirmation if there are unsaved changes
            if messagebox.askyesno("Switch Save Slot", 
                                "Are you sure you want to switch to another save slot?\n"
                                "Any unsaved changes will be lost."):
                # Show loading cursor immediately
                self.root.config(cursor="watch")
                
                # Use after_idle to perform the switch after the dialog closes
                self.root.after_idle(lambda: self._perform_slot_switch(selected_slot))
            else:
                # Revert combobox to previous value
                self.slot_var.set(self.current_slot)

    def _perform_slot_switch(self, selected_slot):
        """Actually perform the slot switch (called by after_idle)"""
        try:
            # Save current state to new slot
            self.current_slot = selected_slot
            self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
            
            # PERFORMANCE OPTIMIZATION: Temporarily set a filter that matches no courses
            original_search = None
            if hasattr(self.course_list, 'search_var') and hasattr(self.course_list, 'search_entry'):
                original_search = self.course_list.search_var.get()
                self.course_list.search_var.set("__LOADING_FILTER_TEMP_8675309__")  # Will match no courses
                self.course_list.search_entry.update()  # Force update the search
            
            # Clear current semester layouts
            self.clear_semesters()
            
            # Load the new state (will be faster with filter active)
            self.load_state()
            
            # Restore original search after loading
            if hasattr(self.course_list, 'search_var') and original_search is not None:
                # Small delay to ensure UI is responsive first
                self.root.after(100, lambda: self.course_list.search_var.set(original_search))

        except Exception as e:
            print(f"Error switching slots: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to switch slots: {e}")
            # Reset cursor
            self.root.config(cursor="")
    
    def create_new_slot(self):
        """Create a new save slot"""
        slot_name = simpledialog.askstring("New Save Slot", 
                                         "Enter a name for the new save slot:",
                                         parent=self.root)
        
        if not slot_name:  # User canceled
            return
            
        # Clean the name (remove special characters, spaces)
        slot_name = "".join(c for c in slot_name if c.isalnum() or c in [' ', '_', '-'])
        
        # Check if name already exists
        if slot_name in self.available_slots:
            messagebox.showerror("Error", f"Save slot '{slot_name}' already exists!")
            return
            
        # Create a new slot file
        self.current_slot = slot_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Clear current semesters
        self.clear_semesters()
        
        # Save current state to new slot
        self.save_state()
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Created new save slot: {slot_name}")
    
    def rename_slot(self):
        """Rename the current save slot"""
        if self.current_slot == "Default":
            messagebox.showerror("Error", "Cannot rename the Default save slot!")
            return
            
        new_name = simpledialog.askstring("Rename Save Slot", 
                                        "Enter a new name for this save slot:",
                                        parent=self.root,
                                        initialvalue=self.current_slot)
        
        if not new_name:  # User canceled
            return
            
        # Clean the name
        new_name = "".join(c for c in new_name if c.isalnum() or c in [' ', '_', '-'])
        
        # Check if name already exists and isn't the current name
        if new_name in self.available_slots and new_name != self.current_slot:
            messagebox.showerror("Error", f"Save slot '{new_name}' already exists!")
            return
            
        old_file = self.state_file
        self.current_slot = new_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # If the old file exists, rename it
        if os.path.exists(old_file):
            try:
                os.rename(old_file, self.state_file)
            except Exception as e:
                print(f"Error renaming save file: {e}")
                # If rename fails, save to the new location
                self.save_state()
        else:
            # Save to the new location
            self.save_state()
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Renamed save slot to: {new_name}")
    
    def delete_slot(self):
        """Delete the current save slot"""
        if self.current_slot == "Default":
            messagebox.showerror("Error", "Cannot delete the Default save slot!")
            return
            
        if messagebox.askyesno("Delete Save Slot", 
                             f"Are you sure you want to delete the save slot '{self.current_slot}'?\n"
                             "This action cannot be undone."):
            
            # Delete the file
            try:
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
            except Exception as e:
                print(f"Error deleting save file: {e}")
            
            # Switch to Default slot
            self.current_slot = "Default"
            self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
            
            # Clear current semesters
            self.clear_semesters()
            
            # Load the default state
            self.load_state()
            
            # Update UI
            self.update_slot_selector()
            self.slot_var.set(self.current_slot)
            
            messagebox.showinfo("Success", "Save slot deleted successfully")
    
    def duplicate_slot(self):
        """Duplicate the current save slot"""
        # Get base name for copy
        base_name = f"{self.current_slot}_copy"
        
        # Find a unique name
        counter = 1
        new_name = base_name
        while new_name in self.available_slots:
            new_name = f"{base_name}_{counter}"
            counter += 1
        
        # Save current state
        self.save_state()
        
        # Create copy with new name
        old_file = self.state_file
        
        if os.path.exists(old_file):
            new_file = os.path.join(self.save_dir, f"{new_name}.json")
            try:
                shutil.copy2(old_file, new_file)
            except Exception as e:
                print(f"Error duplicating save file: {e}")
                return
        
        # Switch to the new slot
        self.current_slot = new_name
        self.state_file = os.path.join(self.save_dir, f"{self.current_slot}.json")
        
        # Update UI
        self.update_slot_selector()
        self.slot_var.set(self.current_slot)
        
        messagebox.showinfo("Success", f"Duplicated save slot: {new_name}")
    
    def clear_semesters(self):
        """Clear all courses from semesters"""
        for semester_frame in self.semester_frames:
            # Create a copy of the list to avoid modification during iteration
            courses_copy = semester_frame.courses.copy()
            for course in courses_copy:
                semester_frame.remove_course(course)
    
    def on_close(self):
        """Handler for window close event"""
        self.save_state()
        self.root.destroy()
    
    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                "semester_assignments": {},
                "expanded_groups": self.course_list.expanded_groups,
                "favorites": [],  # Add an array to store favorite courses
                "window": {
                    "width": self.root.winfo_width(),
                    "height": self.root.winfo_height(),
                }
            }
            
            # Save course assignments to semesters
            for i, semester_frame in enumerate(self.semester_frames):
                # Each semester gets an array of course codes
                course_codes = []
                for course in semester_frame.courses:
                    if hasattr(course, 'module_code') and course.module_code:
                        course_codes.append(course.module_code)
                        
                state["semester_assignments"][str(i)] = course_codes
            
            # Save favorite courses
            for course in self.courses:
                if hasattr(course, 'favorite') and course.favorite and hasattr(course, 'module_code'):
                    state["favorites"].append(course.module_code)
            
            # Write to file
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            print(f"State saved to {self.state_file}")
            
            # Update window title to show current slot
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
                
        except Exception as e:
            print(f"Error saving state: {e}")
            messagebox.showerror("Error", f"Failed to save state: {e}")
    
    def load_state(self):
        """Load saved state if it exists"""
        if not os.path.exists(self.state_file):
            print(f"No saved state found for slot '{self.current_slot}'.")
            self.save_state()
            return
            
        start_time = time.time()  # Track loading time
        
        try:
            # Hide window and show loading cursor early
            self.root.withdraw()
            self.root.config(cursor="watch")
            
            # Load state from file
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Set window size if specified
            if "window" in state:
                width = state["window"].get("width", 1600)
                height = state["window"].get("height", 900)
                self.root.geometry(f"{width}x{height}")
                
            # PERFORMANCE: Disable terminal output temporarily
            original_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            
            # Create a lookup dictionary for faster course retrieval by code
            course_by_code = {course.module_code: course for course in self.courses if hasattr(course, 'module_code')}
                
            # Load favorite courses
            if "favorites" in state:
                for module_code in state["favorites"]:
                    if module_code in course_by_code:
                        course_by_code[module_code].favorite = True
            
            # Set expanded groups state for course list
            if "expanded_groups" in state and hasattr(self, "course_list"):
                self.course_list.expanded_groups = state["expanded_groups"]
                
            # Store and disable critical functions during load
            original_update_grad_req = None
            if hasattr(self.drag_drop_manager, 'app'):
                original_update_grad_req = self.drag_drop_manager.app.update_graduation_requirements
                self.drag_drop_manager.app.update_graduation_requirements = lambda: None
                
            # PERFORMANCE: Create all course blocks in memory first without attaching to UI
            semester_data = {}
            course_blocks = {}
            
            # First pass: Assign courses to semester objects
            if "semester_assignments" in state:
                for semester_idx, course_codes in state["semester_assignments"].items():
                    semester_idx = int(semester_idx)
                    if semester_idx < len(self.semester_frames):
                        semester = self.semester_frames[semester_idx]
                        semester_data[semester_idx] = []
                        
                        for code in course_codes:
                            if code in course_by_code:
                                course = course_by_code[code]
                                semester.courses.append(course)
                                course.assigned_semester = semester
                                semester_data[semester_idx].append(course)
            
            # Update course list without redrawing for each course
            if hasattr(self, "course_list"):
                self.course_list.display_courses()
            
            # Make all the UI changes after everything is prepared
            for semester_idx, courses in semester_data.items():
                semester = self.semester_frames[semester_idx]
                semester.total_credits = sum(course.credits for course in semester.courses)
                
                # Create all course blocks in a batch
                for course in courses:
                    course_block = CourseBlock(semester.course_container, course, self.drag_drop_manager)
                    semester.course_blocks[course] = course_block
                
                # Update visuals after all blocks are created
                for course, block in semester.course_blocks.items():
                    block.pack(fill=tk.X, pady=3, padx=2)
                
                semester.update_total_credits()
                semester._configure_scroll_region()
            
            # Restore original functions
            if original_update_grad_req:
                self.drag_drop_manager.app.update_graduation_requirements = original_update_grad_req
            
            # Restore stdout
            sys.stdout = original_stdout
            
            # Update window title and restore visibility
            self.root.title(f"Semester Calendar Planner - {self.current_slot}")
            self.root.deiconify()
            self.root.config(cursor="")
            
            # Update graduation requirements once at the end
            self.update_graduation_requirements()
            
            print(f"State loaded in {time.time() - start_time:.2f} seconds")
                
        except Exception as e:
            self.root.deiconify()  # Make sure window is visible
            self.root.config(cursor="")
            print(f"Error loading state: {e}")
            traceback.print_exc()  # Print the full traceback for debugging
            messagebox.showerror("Error", f"Failed to load state: {e}")
    
    def create_semesters(self):
        """Create the semester frames in a 1x6 horizontal layout"""
        # Clear any existing frames
        self.semester_frames = []
        
        # Set up a row with 6 columns
        for j in range(6):  # 6 columns for 6 semesters
            self.semesters_frame.grid_columnconfigure(j, weight=1, minsize=250)  # Minimum width of 250 pixels
            
            # Generate semester name based on index
            if j % 2 == 0:  # Even indexes (0, 2, 4) are now Summer semesters
                semester_type = "SoSe"
                year = 2025 + (j // 2)
                semester_title = f"{semester_type} {year}"
            else:  # Odd indexes (1, 3, 5) are now Winter semesters
                semester_type = "WiSe"
                year = 2025 + (j // 2)
                semester_title = f"{semester_type} {year}/{year+1}"
            
            semester_frame = SemesterFrame(self.semesters_frame, semester_title, 30, self.drag_drop_manager)
            semester_frame.grid(row=0, column=j, sticky="nsew", padx=5, pady=5)  # All in row 0
            
            # Store reference to semester frame
            self.semester_frames.append(semester_frame)
    
    def load_courses(self):
        """Load courses from the JSON file"""
        try:
            # Get the absolute path to the resources directory
            courses_file = os.path.join(self.resources_dir, 'courses.json')
            
            with open(courses_file, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
                
            for course_data in courses_data:
                # Check if the course has a title - if not, it's a placeholder entry
                if 'title' in course_data:
                    # Create a Course object from the data
                    course = Course(
                        title=course_data.get('title', 'Unnamed Course'),
                        credits=course_data.get('credits', 0),
                        exam_type=course_data.get('exam_type', ''),
                        group=course_data.get('group', ''),
                        module_code=course_data.get('module_code', ''),
                        grading=course_data.get('grading', ''),
                        semester=course_data.get('semester', '')
                    )
                    self.courses.append(course)
                    
        except Exception as e:
            print(f"Error loading courses: {e}")
    
    def update_graduation_requirements(self):
        """Update the graduation requirements display"""
        if hasattr(self, 'graduation_requirements'):
            self.graduation_requirements.update_requirements()
