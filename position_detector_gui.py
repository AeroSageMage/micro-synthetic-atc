import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import threading
import time
import sys
import json
from position_detector import PositionDetector, AircraftArea
from pathlib import Path
from airport_manager import AirportManager

class PositionDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Airport Position Detector")
        
        # Initialize variables
        self.airport_manager = None
        self.position_detector = None
        self.current_airport_file = None
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create file selection frame
        self.file_frame = ttk.LabelFrame(self.main_frame, text="Airport Data", padding="5")
        self.file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.file_label = ttk.Label(self.file_frame, text="No airport file selected")
        self.file_label.grid(row=0, column=0, sticky=tk.W)
        
        self.select_button = ttk.Button(self.file_frame, text="Select Airport File", command=self.select_airport_file)
        self.select_button.grid(row=0, column=1, padx=5)
        
        # Create input frame
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Position Input", padding="5")
        self.input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.input_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W)
        self.lat_entry = ttk.Entry(self.input_frame)
        self.lat_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.input_frame, text="Longitude:").grid(row=1, column=0, sticky=tk.W)
        self.lon_entry = ttk.Entry(self.input_frame)
        self.lon_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.input_frame, text="Heading:").grid(row=2, column=0, sticky=tk.W)
        self.heading_entry = ttk.Entry(self.input_frame)
        self.heading_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        # Create detect button
        self.detect_button = ttk.Button(self.input_frame, text="Detect Position", command=self.detect_position)
        self.detect_button.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Create status frame
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="5")
        self.status_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.status_text = tk.Text(self.status_frame, height=10, width=40, wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.input_frame.columnconfigure(1, weight=1)
        self.status_frame.columnconfigure(0, weight=1)
        
        # Select initial airport file
        self.select_airport_file()
        
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
    
    def select_airport_file(self):
        """Show file selection dialog and load the selected airport file."""
        # Set initial directory to airport_data if it exists
        initial_dir = "airport_data" if Path("airport_data").exists() else None
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Airport File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if file_path:
            try:
                self.current_airport_file = file_path
                self.airport_manager = AirportManager(file_path)
                self.position_detector = PositionDetector(self.airport_manager)
                
                # Update file label
                self.file_label.config(text=f"Airport: {self.airport_manager.name} ({self.airport_manager.icao})")
                
                # Clear status
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, f"Loaded airport: {self.airport_manager.name}\n")
                self.status_text.insert(tk.END, f"ICAO: {self.airport_manager.icao}\n")
                self.status_text.insert(tk.END, f"Runways: {len(self.airport_manager.runways)}\n")
                self.status_text.insert(tk.END, f"Taxiways: {len(self.airport_manager.taxiways)}\n")
                self.status_text.insert(tk.END, f"Parking positions: {len(self.airport_manager.parking_positions)}\n")
                self.status_text.insert(tk.END, f"Holding points: {len(self.airport_manager.holding_points)}\n")
                
            except Exception as e:
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, f"Error loading airport file: {str(e)}")
    
    def detect_position(self):
        """Detect the aircraft's position based on input coordinates and heading."""
        if not self.airport_manager or not self.position_detector:
            self.status_text.insert(tk.END, "Please select an airport file first.\n")
            return
        
        try:
            # Get input values
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            heading = float(self.heading_entry.get())
            
            # Detect position
            position_info = self.position_detector.detect_position((lat, lon), heading)
            
            # Update status
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"Position: {position_info['position']}\n")
            self.status_text.insert(tk.END, f"Nearest runway: {position_info['nearest_runway']}\n")
            self.status_text.insert(tk.END, f"Distance to center: {position_info['distance_to_center']:.2f}m\n")
            self.status_text.insert(tk.END, f"Nearest taxiway: {position_info['nearest_taxiway']}\n")
            self.status_text.insert(tk.END, f"Distance to taxiway: {position_info['distance_to_taxiway']:.2f}m\n")
            
            if position_info['nearest_parking']:
                self.status_text.insert(tk.END, f"Nearest parking: {position_info['nearest_parking']}\n")
                self.status_text.insert(tk.END, f"Parking type: {position_info['parking_type']}\n")
                self.status_text.insert(tk.END, f"Parking elevation: {position_info['parking_elevation']:.2f}m\n")
                self.status_text.insert(tk.END, f"Parking heading: {position_info['parking_heading']:.2f}°\n")
                self.status_text.insert(tk.END, f"Parking size: {position_info['parking_size']:.2f}m\n")
            
            if position_info['nearest_holding_point']:
                self.status_text.insert(tk.END, f"Nearest holding point: {position_info['nearest_holding_point']}\n")
                self.status_text.insert(tk.END, f"Associated with: {position_info['holding_point_association']}\n")
            
        except ValueError as e:
            self.status_text.insert(tk.END, f"Error: {str(e)}\n")
            self.status_text.insert(tk.END, "Please enter valid numbers for latitude, longitude, and heading.\n")
        except Exception as e:
            self.status_text.insert(tk.END, f"Error detecting position: {str(e)}\n")

def main():
    root = tk.Tk()
    app = PositionDetectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 