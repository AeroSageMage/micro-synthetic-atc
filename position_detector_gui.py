import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import time
import sys
import json
from position_detector import PositionDetector, AircraftArea

class PositionDetectorGUI:
    def __init__(self, root, layout_file="airport_data/graz_airport.json"):
        self.root = root
        self.root.title("Position Detector GUI")
        self.root.geometry("600x500")
        
        # Create PositionDetector instance
        self.detector = PositionDetector(layout_file)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="5")
        self.status_frame.pack(fill=tk.X, pady=5)
        
        # Airport status
        self.airport_label = ttk.Label(self.status_frame, text=f"Airport: {self.detector.airport.name} ({self.detector.airport.icao})")
        self.airport_label.pack(side=tk.LEFT, padx=5)
        
        # Area status
        self.area_label = ttk.Label(self.status_frame, text="Area: Not detected")
        self.area_label.pack(side=tk.LEFT, padx=5)
        
        # Create latest position info frame
        self.latest_info_frame = ttk.LabelFrame(self.main_frame, text="Latest Position Info", padding="5")
        self.latest_info_frame.pack(fill=tk.X, pady=5)
        
        # Latest info text
        self.latest_info_text = ttk.Label(self.latest_info_frame, text="No position info yet", wraplength=550)
        self.latest_info_text.pack(fill=tk.X, padx=5)
        
        # Messages frame
        self.messages_frame = ttk.LabelFrame(self.main_frame, text="Debug Log", padding="5")
        self.messages_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Messages text area
        self.messages_text = scrolledtext.ScrolledText(self.messages_frame, wrap=tk.WORD)
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        self.messages_text.config(state=tk.DISABLED)
        
        # Control frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        # Start/Stop button
        self.start_button = ttk.Button(self.control_frame, text="Start Detection", command=self.toggle_detection)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Clear messages button
        self.clear_button = ttk.Button(self.control_frame, text="Clear Log", command=self.clear_messages)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Save Position button
        self.save_button = ttk.Button(self.control_frame, text="Save Position", command=self.save_position)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Debug mode toggle
        self.debug_mode = tk.BooleanVar(value=True)
        self.debug_checkbox = ttk.Checkbutton(self.control_frame, text="Debug Mode", variable=self.debug_mode)
        self.debug_checkbox.pack(side=tk.LEFT, padx=5)
        
        # State
        self.running = False
        self.detector_thread = None
        self.latest_info = None
        
        # Redirect stdout
        self.original_stdout = sys.stdout
        sys.stdout = self
        
    def write(self, text):
        if text.startswith("DEBUG:"):
            if self.debug_mode.get():
                self.messages_text.config(state=tk.NORMAL)
                self.messages_text.insert(tk.END, text)
                self.messages_text.see(tk.END)
                self.messages_text.config(state=tk.DISABLED)
        else:
            self.messages_text.config(state=tk.NORMAL)
            self.messages_text.insert(tk.END, text)
            self.messages_text.see(tk.END)
            self.messages_text.config(state=tk.DISABLED)
        
    def flush(self):
        pass
        
    def toggle_detection(self):
        if not self.running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        self.running = True
        self.start_button.config(text="Stop Detection")
        self.detector.udp_receiver.start_receiving()
        self.detector_thread = threading.Thread(target=self.run_detector)
        self.detector_thread.daemon = True
        self.detector_thread.start()
    
    def stop_detection(self):
        self.running = False
        self.start_button.config(text="Start Detection")
        self.detector.udp_receiver.stop()
        self.area_label.config(text="Area: Not detected")
        self.latest_info_text.config(text="No position info yet")
    
    def run_detector(self):
        try:
            while self.running:
                info = self.detector.detect_position()
                self.latest_info = info
                # Update area label
                self.area_label.config(text=f"Area: {info.area.name.replace('_', ' ').title()}")
                # Update latest info text
                details = []
                if info.specific_location:
                    details.append(f"Location: {info.specific_location}")
                if info.taxiway:
                    details.append(f"Taxiway: {info.taxiway}")
                if info.runway:
                    details.append(f"Runway: {info.runway}")
                if info.distance_to_center is not None:
                    details.append(f"Distance to center: {info.distance_to_center:.6f}")
                if info.heading is not None:
                    details.append(f"Heading: {info.heading:.1f}°")
                if info.speed is not None:
                    details.append(f"Speed: {info.speed:.1f} m/s")
                self.latest_info_text.config(text=" | ".join(details) if details else "No position info yet")
                time.sleep(1)
        except Exception as e:
            self.add_message(f"Error: {str(e)}")
            self.stop_detection()
    
    def add_message(self, message):
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, f"{message}\n")
        self.messages_text.see(tk.END)
        self.messages_text.config(state=tk.DISABLED)
    
    def clear_messages(self):
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
    
    def save_position(self):
        if not self.latest_info:
            self.add_message("No position info available to save")
            return
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"positiondetector_{timestamp}.json"
        data = {
            "timestamp": timestamp,
            "area": self.latest_info.area.name,
            "specific_location": self.latest_info.specific_location,
            "taxiway": self.latest_info.taxiway,
            "runway": self.latest_info.runway,
            "distance_to_center": self.latest_info.distance_to_center,
            "heading": self.latest_info.heading,
            "speed": self.latest_info.speed,
            "airport": {
                "name": self.detector.airport.name,
                "icao": self.detector.airport.icao
            }
        }
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            self.add_message(f"Position info saved to {filename}")
        except Exception as e:
            self.add_message(f"Error saving position info: {str(e)}")
    
    def __del__(self):
        sys.stdout = self.original_stdout

if __name__ == "__main__":
    root = tk.Tk()
    app = PositionDetectorGUI(root)
    root.mainloop() 