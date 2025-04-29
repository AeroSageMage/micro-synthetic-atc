import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
import threading
import time
import sys
import json
import logging
from typing import Optional
from position_detector import PositionDetector, AircraftArea
from pathlib import Path
from airport_manager import AirportManager
from utils.geo_utils import haversine_distance
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk

# Configure logging to suppress TkinterMapView debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console handler
        logging.FileHandler('position_detector.log')  # File handler
    ]
)

# Set log levels for specific modules
logging.getLogger('tkintermapview').setLevel(logging.INFO)
logging.getLogger('PIL').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)

# Create a custom logger for our application
app_logger = logging.getLogger('PositionDetector')
app_logger.setLevel(logging.DEBUG)

class PositionDetectorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Position Detector")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.airport_manager: Optional[AirportManager] = None
        self.position_detector: Optional[PositionDetector] = None
        self.current_airport_file = None
        
        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create left panel for controls and debug
        self.left_panel = ttk.Frame(self.main_container)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create right panel for map
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create UI elements
        self.create_file_selection_frame()
        self.create_input_frame()
        self.create_status_frame()
        
        # Start with file selection
        self.select_airport_file()
        
        # Create map view after airport file is selected
        self.create_map_view()
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.left_panel, text="Status", padding="5")
        self.status_frame.pack(fill=tk.X, pady=5)
        
        # Airport status
        self.airport_label = ttk.Label(self.status_frame, text="Airport: Not selected")
        self.airport_label.pack(side=tk.LEFT, padx=5)
        
        # Area status
        self.area_label = ttk.Label(self.status_frame, text="Area: Not detected")
        self.area_label.pack(side=tk.LEFT, padx=5)
        
        # Create latest position info frame
        self.latest_info_frame = ttk.LabelFrame(self.left_panel, text="Latest Position Info", padding="5")
        self.latest_info_frame.pack(fill=tk.X, pady=5)
        
        # Latest info text
        self.latest_info_text = ttk.Label(self.latest_info_frame, text="No position info yet", wraplength=550)
        self.latest_info_text.pack(fill=tk.X, padx=5)
        
        # Messages frame with fixed height
        self.messages_frame = ttk.LabelFrame(self.left_panel, text="Debug Log", padding="5")
        self.messages_frame.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # Messages text area with fixed height
        self.messages_text = scrolledtext.ScrolledText(self.messages_frame, wrap=tk.WORD, height=10)
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        self.messages_text.config(state=tk.DISABLED)
        
        # Control frame
        self.control_frame = ttk.Frame(self.left_panel)
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
        
        # Map view state
        self.aircraft_marker = None
        self.aircraft_image = Image.open("aircraft_icon.png").resize((32, 32))
        self.rotated_image = None
        self.follow_aircraft = True
        self.initial_position_set = False
        self.map_center = None
        
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
        self.position_detector.udp_receiver.start_receiving()
        self.detector_thread = threading.Thread(target=self.run_detector)
        self.detector_thread.daemon = True
        self.detector_thread.start()
    
    def stop_detection(self):
        self.running = False
        self.start_button.config(text="Start Detection")
        self.position_detector.udp_receiver.stop()
        self.area_label.config(text="Area: Not detected")
        self.latest_info_text.config(text="No position info yet")
    
    def run_detector(self):
        try:
            last_update = time.time()
            while self.running:
                current_time = time.time()
                # Only update if 0.5 seconds have passed
                if current_time - last_update >= 0.5:
                    # Get latest data from UDP receiver
                    data = self.position_detector.udp_receiver.get_latest_data()
                    if data['gps'] and data['attitude']:
                        gps = data['gps']
                        attitude = data['attitude']
                        
                        # Update aircraft marker on map
                        self.update_aircraft_marker(gps, attitude)
                        
                        # Get coordinates and heading
                        coordinates = (gps.latitude, gps.longitude)
                        heading = attitude.true_heading
                        
                        # Detect position
                        info = self.position_detector.detect_position(coordinates, heading)
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
                    
                    last_update = current_time
                time.sleep(0.1)  # Small sleep to prevent CPU overuse
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
                "name": self.position_detector.airport.name,
                "icao": self.position_detector.airport.icao
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
    
    def create_file_selection_frame(self):
        """Create the file selection frame."""
        self.file_frame = ttk.LabelFrame(self.left_panel, text="Airport Data", padding="5")
        self.file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_label = ttk.Label(self.file_frame, text="No airport file selected")
        self.file_label.pack(side="left")
        
        self.select_button = ttk.Button(self.file_frame, text="Select Airport File", command=self.select_airport_file)
        self.select_button.pack(side="left", padx=5)
        
    def create_input_frame(self):
        """Create the input frame for coordinates and heading."""
        self.input_frame = ttk.LabelFrame(self.left_panel, text="Position Input", padding="5")
        self.input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(self.input_frame, text="Latitude:").grid(row=0, column=0, sticky="w")
        self.lat_entry = ttk.Entry(self.input_frame)
        self.lat_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(self.input_frame, text="Longitude:").grid(row=1, column=0, sticky="w")
        self.lon_entry = ttk.Entry(self.input_frame)
        self.lon_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(self.input_frame, text="Heading:").grid(row=2, column=0, sticky="w")
        self.heading_entry = ttk.Entry(self.input_frame)
        self.heading_entry.grid(row=2, column=1, padx=5)
        
        # Detect button
        self.detect_button = ttk.Button(self.input_frame, text="Detect Position", command=self.detect_position)
        self.detect_button.grid(row=3, column=0, columnspan=2, pady=5)
        
    def create_status_frame(self):
        """Create the status frame for displaying results."""
        self.status_frame = ttk.LabelFrame(self.left_panel, text="Status", padding="5")
        self.status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(self.status_frame, wrap="word", height=10)
        self.status_text.pack(fill="both", expand=True)
        
    def create_map_view(self):
        """Create the map view widget."""
        # Create map widget
        self.map_widget = TkinterMapView(self.right_panel, width=400, height=600, corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        
        # Setup aircraft marker
        self.setup_aircraft_marker()
        
        # Add map controls
        map_control_frame = ttk.Frame(self.right_panel)
        map_control_frame.pack(fill=tk.X, pady=5)
        
        self.follow_var = tk.BooleanVar(value=True)
        self.follow_checkbox = ttk.Checkbutton(
            map_control_frame, 
            text="Follow Aircraft", 
            variable=self.follow_var,
            command=self.toggle_follow_mode
        )
        self.follow_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Set initial map position
        self.map_widget.set_position(0, 0)
        self.map_widget.set_zoom(10)

    def setup_aircraft_marker(self):
        """Set up the aircraft marker image and related variables."""
        self.aircraft_image = Image.open("aircraft_icon.png").resize((32, 32))
        self.rotated_image = ImageTk.PhotoImage(self.aircraft_image)
        self.aircraft_marker = None
        self.initial_position_set = False

    def rotate_image(self, angle: float) -> ImageTk.PhotoImage:
        """Rotate the aircraft icon image by the given angle."""
        return ImageTk.PhotoImage(self.aircraft_image.rotate(-angle))

    def update_aircraft_marker(self, gps_data, attitude_data):
        """Update the aircraft marker on the map."""
        if not gps_data or not attitude_data:
            return
            
        if not self.initial_position_set:
            self.map_widget.set_position(gps_data.latitude, gps_data.longitude)
            self.map_widget.set_zoom(10)
            self.initial_position_set = True
            self.map_center = (gps_data.latitude, gps_data.longitude)
            
        self.rotated_image = self.rotate_image(attitude_data.true_heading)

        # Update or create the aircraft marker
        if self.aircraft_marker:
            self.aircraft_marker.delete()
            
        # Create new marker
        marker_text = f"Aircraft\n{attitude_data.true_heading:.1f}°"
        self.aircraft_marker = self.map_widget.set_marker(
            gps_data.latitude, 
            gps_data.longitude,
            icon=self.rotated_image,
            icon_anchor="center",
            text=marker_text,
            text_color="black",
            font=("Arial", 8),
            command=None
        )
        
        # Center map on aircraft if follow mode is enabled
        if self.follow_aircraft:
            self.map_widget.set_position(gps_data.latitude, gps_data.longitude)

    def toggle_follow_mode(self):
        """Toggle whether the map should automatically follow the aircraft."""
        self.follow_aircraft = self.follow_var.get()
        if not self.follow_aircraft:
            # Store current map center when disabling follow mode
            current_pos = self.map_widget.get_position()
            self.map_center = (current_pos[0], current_pos[1])
            print(f"Follow mode disabled. Map center fixed at: {self.map_center}")
        else:
            # When re-enabling follow mode, if we have GPS data, immediately center on aircraft
            if self.position_detector and self.position_detector.udp_receiver.latest_gps_data:
                gps = self.position_detector.udp_receiver.latest_gps_data
                self.map_widget.set_position(gps.latitude, gps.longitude)
                print("Follow mode enabled. Centering on aircraft.")

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

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = PositionDetectorGUI()
    app.run() 