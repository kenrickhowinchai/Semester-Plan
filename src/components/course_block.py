import tkinter as tk
from tkinter import ttk

class CourseBlock(tk.Frame):
    # Colors for different requirement groups
    GROUP_COLORS = {
        "1.": "#D4E6F1",  # Kernbereich - Informatik und Mathematik: Light blue
        "2.": "#D5F5E3",  # Kernbereich - Simulation und Optimierung: Light green
        "3.": "#E8DAEF",  # Kernbereich - Messen, Steuern, Regeln: Light purple
        "4.": "#FDEBD0",  # Profilbereich: Light orange
        "6.": "#FADBD8",  # Projekt: Light red
        "7.": "#F9E79F",  # Freiwahlbereich: Light yellow
        "8.": "#D1F2EB",  # Fachpraktikum: Light cyan
        "9.": "#FDEDEC",  # Masterarbeit: Light pink
    }
    
    def __init__(self, parent, course, drag_drop_manager=None, is_placed=False):
        super().__init__(parent, relief=tk.RAISED, borderwidth=1, padx=5, pady=5)
        self.course = course
        self.drag_drop_manager = drag_drop_manager
        self.is_placed = is_placed
        
        # Determine background color based on course group
        bg_color = self.get_background_color()
        self.configure(background=bg_color)
        
        # Create a header frame for course title and favorite button
        header_frame = tk.Frame(self, bg=bg_color)
        header_frame.pack(fill=tk.X, expand=True)
        
        # Create favorite button (star icon)
        self.fav_text = tk.StringVar()
        self.update_favorite_display()
        
        self.fav_btn = tk.Button(
            header_frame, 
            textvariable=self.fav_text,
            font=("Arial", 10),
            width=2,
            command=self.toggle_favorite,
            relief=tk.FLAT,
            bd=0,
            bg=bg_color,
            state=tk.DISABLED if is_placed else tk.NORMAL  # Disable favorite button if placed
        )
        self.fav_btn.pack(side=tk.RIGHT)
        
        # Course title
        text_color = "#A0A0A0" if is_placed else "#000000"  # Gray text if placed
        self.title_label = tk.Label(
            header_frame, 
            text=self.course.title, 
            font=("Helvetica", 10, "bold"),
            anchor="w",
            bg=bg_color,
            fg=text_color
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Course credits
        tk.Label(
            self, 
            text=f"{self.course.credits} LP", 
            font=("Helvetica", 9),
            bg=bg_color,
            fg=text_color
        ).pack(anchor="w")
        
        # Course module code if available
        if hasattr(self.course, 'module_code') and self.course.module_code:
            tk.Label(
                self, 
                text=f"Code: {self.course.module_code}", 
                font=("Helvetica", 8),
                bg=bg_color,
                fg=text_color
            ).pack(anchor="w")
            
        # Course group if available
        if hasattr(self.course, 'group') and self.course.group:
            tk.Label(
                self, 
                text=f"Group: {self.course.group}", 
                font=("Helvetica", 8),
                bg=bg_color,
                fg=text_color
            ).pack(anchor="w")
        
        # Course semester availability if available
        if hasattr(self.course, 'semester') and self.course.semester:
            tk.Label(
                self, 
                text=f"Offered: {self.course.semester}", 
                font=("Helvetica", 8),
                bg=bg_color,
                fg=text_color
            ).pack(anchor="w")
        
        # If course is placed, add an indicator label
        if is_placed:
            placement_info = f"Placed in {course.assigned_semester.title}" if course.assigned_semester else "Already placed"
            tk.Label(
                self,
                text=placement_info,
                font=("Helvetica", 8, "italic"),
                bg=bg_color,
                fg="#FF6B6B"  # Red-ish color
            ).pack(anchor="w")
        
        # Make draggable only if not placed
        if self.drag_drop_manager and not is_placed:
            self.bind("<ButtonPress-1>", self.on_drag_start)
            self.title_label.bind("<ButtonPress-1>", self.on_drag_start)
            for child in self.winfo_children():
                child.bind("<ButtonPress-1>", self.on_drag_start)
    
    def get_background_color(self):
        """Determine the background color based on the course group"""
        if self.is_placed:
            return "#F0F0F0"  # Light gray for placed courses
        
        if hasattr(self.course, 'group') and self.course.group:
            # Check if this course is a favorite
            if hasattr(self.course, 'favorite') and self.course.favorite:
                return "#FFF9C4"  # Light yellow for favorites takes precedence
            
            # Otherwise use group-based color
            for prefix, color in self.GROUP_COLORS.items():
                if self.course.group.startswith(prefix):
                    return color
        
        return "#F5F5F5"  # Default light gray
    
    def update_favorite_display(self):
        """Update the favorite button text based on status"""
        if hasattr(self.course, 'favorite') and self.course.favorite:
            self.fav_text.set("★")  # Solid star
            print(f"Course {self.course.title} is marked as favorite")
        else:
            self.fav_text.set("☆")  # Empty star
    
    def update_appearance(self):
        """Update the appearance based on favorite status"""
        bg_color = self.get_background_color()
        self.configure(background=bg_color)
        
        # Update star color
        if hasattr(self.course, 'favorite') and self.course.favorite:
            self.fav_btn.configure(background=bg_color, foreground="#FFB300")
        else:
            self.fav_btn.configure(background=bg_color, foreground="#757575")
        
        # Apply background to all child widgets
        for child in self.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(background=bg_color)
                for grandchild in child.winfo_children():
                    grandchild.configure(background=bg_color)
            else:
                child.configure(background=bg_color)
    
    def toggle_favorite(self):
        """Toggle favorite status of the course"""
        if not hasattr(self.course, 'favorite'):
            self.course.favorite = False
        self.course.favorite = not self.course.favorite
        print(f"Course '{self.course.title}' favorite status: {self.course.favorite}")
        
        # Update display
        self.update_favorite_display()
        self.update_appearance()
        
        # Save state if possible
        if self.drag_drop_manager and hasattr(self.drag_drop_manager, 'app'):
            self.drag_drop_manager.app.save_state()
    
    def on_drag_start(self, event):
        """Start dragging this course block"""
        if self.drag_drop_manager:
            # Pass the click to the star button if it was clicked
            if event.widget == self.fav_btn:
                self.toggle_favorite()
                return "break"
            
            # Otherwise start dragging
            self.drag_drop_manager.start_drag(event, self)
            return "break"