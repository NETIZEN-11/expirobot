"""
GUI module for ExpirioBot.
Provides reusable GUI components for different application modes.
"""

import tkinter as tk
from tkinter import Label, Entry, Button, Frame, LabelFrame, messagebox
from PIL import Image, ImageTk
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

try:
    import cv2
except ImportError:
    cv2 = None

from .config import get_config, GUIConfig

logger = logging.getLogger(__name__)


@dataclass
class CounterDisplay:
    """Display for product counters."""
    frame: Frame
    count_var: tk.IntVar
    value_label: Label
    title_label: Label


class ExpirioBotGUI:
    """Main GUI class for ExpirioBot applications."""
    
    def __init__(self, title: str = "", config: Optional[GUIConfig] = None):
        self.config = config or get_config().gui
        self.root = tk.Tk()
        self.root.title(title or self.config.title)
        self.root.configure(bg=self.config.bg_color)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        
        # Video display
        self.video_label: Optional[Label] = None
        self.current_image: Optional[ImageTk.PhotoImage] = None
        
        # Counters
        self.expired_count = tk.IntVar(value=0)
        self.valid_count = tk.IntVar(value=0)
        self.counter_frame: Optional[Frame] = None
        
        # Control buttons
        self.button_frame: Optional[Frame] = None
        self.start_button: Optional[Button] = None
        self.stop_button: Optional[Button] = None
        
        # Status/Warning labels
        self.warning_label: Optional[Label] = None
        
        # Callbacks
        self.on_start: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.on_manual_check: Optional[Callable] = None
        
        # Update loop
        self._update_job: Optional[str] = None
    
    def setup_video_display(self) -> Label:
        """Create and return video display label."""
        self.video_label = Label(self.root, bg=self.config.bg_color)
        self.video_label.pack(pady=10)
        return self.video_label
    
    def setup_counters(self, compact: bool = False) -> Frame:
        """Create counter display frame."""
        self.counter_frame = Frame(self.root, bg=self.config.bg_color)
        self.counter_frame.pack(pady=10)
        
        if compact:
            self._create_compact_counters()
        else:
            self._create_full_counters()
        
        return self.counter_frame
    
    def _create_full_counters(self) -> None:
        """Create full-size counter displays."""
        # Expired counter
        expired_frame = Frame(self.counter_frame, bg=self.config.bg_color)
        expired_frame.grid(row=0, column=0, padx=20)
        
        expired_value = Label(
            expired_frame,
            textvariable=self.expired_count,
            font=(self.config.font_family, self.config.font_size_large, "bold"),
            fg="red",
            bg=self.config.bg_color
        )
        expired_value.pack()
        
        Label(
            expired_frame,
            text="Expired Products",
            font=(self.config.font_family, self.config.font_size_normal),
            bg=self.config.bg_color,
            fg=self.config.text_color
        ).pack()
        
        # Valid counter
        valid_frame = Frame(self.counter_frame, bg=self.config.bg_color)
        valid_frame.grid(row=0, column=1, padx=20)
        
        valid_value = Label(
            valid_frame,
            textvariable=self.valid_count,
            font=(self.config.font_family, self.config.font_size_large, "bold"),
            fg="green",
            bg=self.config.bg_color
        )
        valid_value.pack()
        
        Label(
            valid_frame,
            text="Valid Products",
            font=(self.config.font_family, self.config.font_size_normal),
            bg=self.config.bg_color,
            fg=self.config.text_color
        ).pack()
    
    def _create_compact_counters(self) -> None:
        """Create compact counter displays."""
        # Expired
        Label(
            self.counter_frame,
            text="Expired:",
            font=(self.config.font_family, self.config.font_size_normal),
            bg=self.config.bg_color,
            fg="red"
        ).grid(row=0, column=0, padx=5)
        
        Label(
            self.counter_frame,
            textvariable=self.expired_count,
            font=(self.config.font_family, self.config.font_size_normal, "bold"),
            bg=self.config.bg_color,
            fg="red"
        ).grid(row=0, column=1, padx=5)
        
        # Valid
        Label(
            self.counter_frame,
            text="Valid:",
            font=(self.config.font_family, self.config.font_size_normal),
            bg=self.config.bg_color,
            fg="green"
        ).grid(row=0, column=2, padx=5)
        
        Label(
            self.counter_frame,
            textvariable=self.valid_count,
            font=(self.config.font_family, self.config.font_size_normal, "bold"),
            bg=self.config.bg_color,
            fg="green"
        ).grid(row=0, column=3, padx=5)
    
    def setup_control_buttons(self, start_text: str = "Start", stop_text: str = "Stop") -> Frame:
        """Create control buttons."""
        self.button_frame = Frame(self.root, bg=self.config.bg_color)
        self.button_frame.pack(pady=10)
        
        self.start_button = Button(
            self.button_frame,
            text=start_text,
            command=self._handle_start,
            bg=self.config.accent_color,
            fg="white",
            font=(self.config.font_family, self.config.font_size_normal),
            padx=10
        )
        self.start_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = Button(
            self.button_frame,
            text=stop_text,
            command=self._handle_stop,
            bg=self.config.danger_color,
            fg="white",
            font=(self.config.font_family, self.config.font_size_normal),
            padx=10
        )
        self.stop_button.grid(row=0, column=1, padx=10)
        
        return self.button_frame
    
    def setup_warning(self, text: str = "") -> Label:
        """Create warning/status label."""
        self.warning_label = Label(
            self.root,
            text=text,
            font=(self.config.font_family, 10),
            bg=self.config.bg_color,
            fg=self.config.warning_color
        )
        self.warning_label.pack(pady=5)
        return self.warning_label
    
    def setup_manual_input(self, placeholder: str = "DD/MM/YYYY") -> tuple[Entry, Button]:
        """Create manual date input section."""
        input_frame = Frame(self.root, bg=self.config.bg_color)
        input_frame.pack(pady=20)
        
        Label(
            input_frame,
            text="Enter Expiry Date:",
            font=(self.config.font_family, self.config.font_size_normal),
            bg=self.config.bg_color,
            fg=self.config.text_color
        ).grid(row=0, column=0, padx=5)
        
        date_entry = Entry(
            input_frame,
            font=(self.config.font_family, self.config.font_size_normal),
            width=15
        )
        date_entry.grid(row=0, column=1, padx=5)
        date_entry.insert(0, placeholder)
        
        check_button = Button(
            input_frame,
            text="Check Date",
            command=self._handle_manual_check,
            bg=self.config.accent_color,
            fg="white",
            font=(self.config.font_family, self.config.font_size_normal),
            padx=10
        )
        check_button.grid(row=0, column=2, padx=5)
        
        # Bind Enter key
        date_entry.bind('<Return>', lambda e: self._handle_manual_check())
        
        return date_entry, check_button
    
    def setup_instructions(self, text: str) -> Label:
        """Create instructions label."""
        return Label(
            self.root,
            text=text,
            font=(self.config.font_family, 9),
            bg=self.config.bg_color,
            fg="#888888",
            justify="center"
        ).pack(pady=10)
    
    def update_frame(self, frame) -> None:
        """Update video display with new frame."""
        if self.video_label is None:
            return
        
        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            self.current_image = imgtk
        except Exception as e:
            logger.error(f"Frame update error: {e}")
    
    def increment_expired(self) -> int:
        """Increment expired counter."""
        self.expired_count.set(self.expired_count.get() + 1)
        return self.expired_count.get()
    
    def increment_valid(self) -> int:
        """Increment valid counter."""
        self.valid_count.set(self.valid_count.get() + 1)
        return self.valid_count.get()
    
    def reset_counters(self) -> None:
        """Reset both counters to zero."""
        self.expired_count.set(0)
        self.valid_count.set(0)
    
    def set_warning(self, text: str, color: str = None) -> None:
        """Update warning label."""
        if self.warning_label:
            self.warning_label.config(text=text, fg=color or self.config.warning_color)
    
    def start_update_loop(self, update_func: Callable) -> None:
        """Start the GUI update loop."""
        def update():
            update_func()
            self._update_job = self.root.after(self.config.update_interval_ms, update)
        
        update()
    
    def stop_update_loop(self) -> None:
        """Stop the GUI update loop."""
        if self._update_job:
            self.root.after_cancel(self._update_job)
            self._update_job = None
    
    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
    
    def destroy(self) -> None:
        """Destroy the GUI."""
        self.stop_update_loop()
        self.root.destroy()
    
    # Callback handlers
    def _handle_start(self) -> None:
        if self.on_start:
            self.on_start()
    
    def _handle_stop(self) -> None:
        if self.on_stop:
            self.on_stop()
    
    def _handle_manual_check(self) -> None:
        if self.on_manual_check:
            self.on_manual_check()