import tkinter as tk
from tkintermapview import TkinterMapView
import json
from dataclasses import dataclass
from typing import List, Tuple
import math

@dataclass
class Runway:
    name: str
    threshold1_coords: Tuple[float, float]
    threshold2_coords: Tuple[float, float]
    width: float
    length: float
    heading: float

@dataclass
class Taxiway:
    name: str
    segments: List[dict]
    width: float

@dataclass
class Parking:
    name: str
    coords: Tuple[float, float]
    type: str
    elevation: float
    heading: float
    size: float

@dataclass
class HoldingPoint:
    name: str
    coords: Tuple[float, float]
    associated_with: str

class AirportVisualizer:
    def __init__(self, layout_file: str = "airport_data/graz_airport.json"):
        self.root = tk.Tk()
        self.root.title("Airport Area Visualizer")
        self.root.geometry("1200x800")
        
        # Load airport layout
        with open(layout_file, 'r') as f:
            self.layout = json.load(f)
            
        # Initialize map
        self.map_widget = TkinterMapView(self.root, width=1000, height=800, corner_radius=0)
        self.map_widget.pack(side="left", fill="both", expand=True)
        
        # Add cursor position label
        self.cursor_label = tk.Label(self.root, text="Lat: ---, Lon: ---", font=("Arial", 10), bg="black", fg="white", anchor="w")
        self.cursor_label.place(x=50, y=10)
        self.map_widget.bind("<Motion>", self.update_cursor_label)
        
        # Set initial position to airport center
        center_lat = (self.layout['runways'][0]['threshold1_coords'][0] + 
                     self.layout['runways'][0]['threshold2_coords'][0]) / 2
        center_lon = (self.layout['runways'][0]['threshold1_coords'][1] + 
                     self.layout['runways'][0]['threshold2_coords'][1]) / 2
        self.map_widget.set_position(center_lat, center_lon)
        self.map_widget.set_zoom(16)
        
        # Initialize control variables
        self.show_runways = tk.BooleanVar(value=True)
        self.show_taxiways = tk.BooleanVar(value=True)
        self.show_parking = tk.BooleanVar(value=True)
        self.show_holding = tk.BooleanVar(value=True)
        self.parking_threshold = tk.DoubleVar(value=0.00005)  # 5 meters
        self.taxiway_threshold = tk.DoubleVar(value=0.00005)  # 5 meters
        self.runway_width_factor = tk.DoubleVar(value=0.5)    # Half of runway width
        
        # Add control panel
        self.setup_control_panel()
        
        # Draw all areas
        self.draw_areas()
        
    def setup_control_panel(self):
        """Set up the control panel on the right side."""
        control_frame = tk.Frame(self.root, width=200)
        control_frame.pack(side="right", fill="y", padx=10)
        
        # Add title
        tk.Label(control_frame, text="Airport Areas", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Add checkboxes for each area type
        tk.Checkbutton(control_frame, text="Show Runways", variable=self.show_runways,
                      command=self.redraw_areas).pack(anchor="w", pady=5)
        tk.Checkbutton(control_frame, text="Show Taxiways", variable=self.show_taxiways,
                      command=self.redraw_areas).pack(anchor="w", pady=5)
        tk.Checkbutton(control_frame, text="Show Parking", variable=self.show_parking,
                      command=self.redraw_areas).pack(anchor="w", pady=5)
        tk.Checkbutton(control_frame, text="Show Holding Points", variable=self.show_holding,
                      command=self.redraw_areas).pack(anchor="w", pady=5)
        
        # Add threshold controls
        tk.Label(control_frame, text="Detection Thresholds", font=("Arial", 10, "bold")).pack(pady=(20,5))
        
        tk.Label(control_frame, text="Parking Threshold (m):").pack(anchor="w")
        tk.Entry(control_frame, textvariable=self.parking_threshold).pack(fill="x", pady=2)
        
        tk.Label(control_frame, text="Taxiway Threshold (m):").pack(anchor="w")
        tk.Entry(control_frame, textvariable=self.taxiway_threshold).pack(fill="x", pady=2)
        
        tk.Label(control_frame, text="Runway Width Factor:").pack(anchor="w")
        tk.Entry(control_frame, textvariable=self.runway_width_factor).pack(fill="x", pady=2)
        
        # Add update button
        tk.Button(control_frame, text="Update Thresholds", 
                 command=self.update_thresholds).pack(pady=10)
        
        # Add reload data button
        tk.Button(control_frame, text="Reload Data", 
                 command=self.reload_data).pack(pady=10)
        
    def draw_areas(self):
        """Draw all airport areas on the map."""
        if self.show_runways.get():
            self.draw_runways()
        if self.show_taxiways.get():
            self.draw_taxiways()
        if self.show_parking.get():
            self.draw_parking()
        if self.show_holding.get():
            self.draw_holding_points()
            
    def redraw_areas(self):
        """Clear and redraw all areas."""
        self.map_widget.delete_all_marker()
        self.map_widget.delete_all_path()
        self.draw_areas()
        
    def draw_runways(self):
        """Draw runways as filled rectangles, with detection areas and threshold boxes."""
        for runway in self.layout['runways']:
            # Draw the filled runway polygon
            self.draw_surface_polygon([runway['threshold1_coords'], runway['threshold2_coords']], runway['width'], fill_color="#444444", outline_color="white")

            # Draw runway center line
            self.map_widget.set_path(
                [runway['threshold1_coords'], runway['threshold2_coords']],
                color="white",
                width=3
            )
            
            # Draw runway width boundaries
            width = runway['width']
            self.draw_parallel_lines(
                runway['threshold1_coords'],
                runway['threshold2_coords'],
                width/2
            )
            
            # Add runway name
            center_lat = (runway['threshold1_coords'][0] + runway['threshold2_coords'][0]) / 2
            center_lon = (runway['threshold1_coords'][1] + runway['threshold2_coords'][1]) / 2
            self.map_widget.set_marker(
                center_lat, center_lon,
                text=runway['name'],
                text_color="blue"
            )
            
            # Draw threshold boxes
            self.draw_threshold_box(runway['threshold1_coords'], runway['threshold2_coords'], width)
            self.draw_threshold_box(runway['threshold2_coords'], runway['threshold1_coords'], width)
            
    def draw_taxiways(self):
        """Draw taxiways with their detection areas."""
        for taxiway in self.layout['taxiways']:
            centerline = [segment['start'] for segment in taxiway['segments']]
            centerline.append(taxiway['segments'][-1]['end'])
            self.draw_surface_polygon(centerline, taxiway['segments'][0]['width'], fill_color="#888888", outline_color="white")
            
            # Add taxiway name marker at each segment center
            for segment in taxiway['segments']:
                center_lat = (segment['start'][0] + segment['end'][0]) / 2
                center_lon = (segment['start'][1] + segment['end'][1]) / 2
                self.map_widget.set_marker(
                    center_lat, center_lon,
                    text=taxiway['name'],
                    text_color="black"
                )
            
    def draw_parking(self):
        """Draw parking positions with their detection areas."""
        for parking in self.layout['parking_positions']:
            # Draw parking spot
            self.map_widget.set_marker(
                parking['coords'][0], parking['coords'][1],
                text=parking['name'],
                text_color="green"
            )
            
            # Draw detection area circle
            self.draw_circle(
                parking['coords'],
                self.parking_threshold.get()
            )
            
    def draw_holding_points(self):
        """Draw holding points with their detection areas."""
        for hp in self.layout['holding_points']:
            # Draw holding point
            self.map_widget.set_marker(
                hp['coords'][0], hp['coords'][1],
                text=hp['name'],
                text_color="red"
            )
            
    def draw_parallel_lines(self, start: Tuple[float, float], end: Tuple[float, float], 
                          distance: float):
        """Draw two lines parallel to the given line at the specified distance."""
        # Calculate perpendicular vector
        dx = end[1] - start[1]
        dy = end[0] - start[0]
        length = math.sqrt(dx*dx + dy*dy)
        dx /= length
        dy /= length
        
        # Calculate offset points
        offset1 = (start[0] + dy*distance, start[1] - dx*distance)
        offset2 = (end[0] + dy*distance, end[1] - dx*distance)
        offset3 = (start[0] - dy*distance, start[1] + dx*distance)
        offset4 = (end[0] - dy*distance, end[1] + dx*distance)
        
        # Draw parallel lines
        self.map_widget.set_path(
            [offset1, offset2],
            color="gray",
            width=1
        )
        self.map_widget.set_path(
            [offset3, offset4],
            color="gray",
            width=1
        )
        
    def draw_circle(self, center: Tuple[float, float], radius: float, 
                   num_points: int = 36):
        """Draw a circle around the given center point."""
        circle_points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            lat = center[0] + radius * math.cos(angle)
            lon = center[1] + radius * math.sin(angle)
            circle_points.append((lat, lon))
            
        # Close the circle
        circle_points.append(circle_points[0])
        
        self.map_widget.set_path(
            circle_points,
            color="gray",
            width=1
        )
        
    def draw_threshold_box(self, threshold, other_threshold, width, box_length=0.00027):
        """Draw a rectangle at the threshold, oriented along the runway heading.
        box_length is in degrees (approx 30m)."""
        # Calculate heading from threshold to other_threshold
        lat1, lon1 = threshold
        lat2, lon2 = other_threshold
        dx = lon2 - lon1
        dy = lat2 - lat1
        angle = math.atan2(dx, dy)
        # Box corners
        half_width = width / 2 / 111320  # meters to degrees approx
        # box_length is already in degrees (approx 30m)
        corners = [
            (lat1 - half_width * math.cos(angle), lon1 + half_width * math.sin(angle)),
            (lat1 + half_width * math.cos(angle), lon1 - half_width * math.sin(angle)),
            (lat1 + half_width * math.cos(angle) + box_length * math.sin(angle), lon1 - half_width * math.sin(angle) + box_length * math.cos(angle)),
            (lat1 - half_width * math.cos(angle) + box_length * math.sin(angle), lon1 + half_width * math.sin(angle) + box_length * math.cos(angle)),
            (lat1 - half_width * math.cos(angle), lon1 + half_width * math.sin(angle)),
        ]
        self.map_widget.set_path(corners, color="red", width=2)
        
    def draw_surface_polygon(self, centerline_points, width, fill_color="#888888", outline_color="white"):
        """Draw a filled polygon along a centerline with the given width."""
        half_width = width / 2 / 111320  # meters to degrees approx
        left_side = []
        right_side = []
        n = len(centerline_points)
        for i in range(n):
            if i == 0:
                # Forward direction
                dx = centerline_points[i+1][1] - centerline_points[i][1]
                dy = centerline_points[i+1][0] - centerline_points[i][0]
            elif i == n-1:
                # Backward direction
                dx = centerline_points[i][1] - centerline_points[i-1][1]
                dy = centerline_points[i][0] - centerline_points[i-1][0]
            else:
                # Average of forward and backward
                dx1 = centerline_points[i][1] - centerline_points[i-1][1]
                dy1 = centerline_points[i][0] - centerline_points[i-1][0]
                dx2 = centerline_points[i+1][1] - centerline_points[i][1]
                dy2 = centerline_points[i+1][0] - centerline_points[i][0]
                dx = (dx1 + dx2) / 2
                dy = (dy1 + dy2) / 2
            angle = math.atan2(dx, dy)
            left = (centerline_points[i][0] - half_width * math.cos(angle), centerline_points[i][1] + half_width * math.sin(angle))
            right = (centerline_points[i][0] + half_width * math.cos(angle), centerline_points[i][1] - half_width * math.sin(angle))
            left_side.append(left)
            right_side.append(right)
        polygon = left_side + right_side[::-1] + [left_side[0]]
        self.map_widget.set_polygon(polygon, fill_color=fill_color, outline_color=outline_color)
        
    def update_thresholds(self):
        """Update the visualization with new threshold values."""
        self.redraw_areas()
        
    def update_cursor_label(self, event):
        try:
            lat, lon = self.map_widget.get_position()
            self.cursor_label.config(text=f"Map Center: Lat: {lat:.6f}, Lon: {lon:.6f}")
        except Exception:
            self.cursor_label.config(text="Lat: ---, Lon: ---")
        
    def reload_data(self):
        """Reload the JSON data and redraw all areas."""
        with open("./airport_data/graz_airport.json", 'r') as f:
            self.layout = json.load(f)
        self.redraw_areas()
        
    def run(self):
        """Start the visualization."""
        self.root.mainloop()

if __name__ == "__main__":
    visualizer = AirportVisualizer()
    visualizer.run() 