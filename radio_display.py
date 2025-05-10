import tkinter as tk
from tkinter import ttk
import math
from tools.rewinger import UDPReceiver
import threading
import time
import socket
import json

class RadioDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("Radio Display")
        
        # Initialize frequencies
        self.active_freq = 118.700
        self.standby_freq = 121.500
        
        # Initialize aircraft info with default callsign
        self.aircraft_info = {
            'callsign': 'aabbcc',  # Default callsign matching ATC state manager
            'type': '',
            'position': '',
            'altitude': '',
            'heading': ''
        }
        
        # Initialize UDP receivers
        self.sim_udp_receiver = UDPReceiver()  # For simulator data
        self.atc_udp_receiver = None  # For ATC messages
        self.running = False
        self.update_thread = None
        
        # Initialize UDP sender for pilot messages
        self.pilot_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frequency displays and swap button
        self.create_frequency_and_swap()
        
        # Create standby control buttons
        self.create_standby_control_buttons()
        
        # Create aircraft info section
        self.create_aircraft_info_section()
        
        # Create ATC message display
        self.create_atc_message_display()
        
        # Create pilot message input
        self.create_pilot_message_input()
        
        # Create control buttons
        self.create_control_buttons()
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.columnconfigure(2, weight=1)
        
    def create_frequency_and_swap(self):
        # Active frequency display
        active_frame = ttk.LabelFrame(self.main_frame, text="ACTIVE", padding="5")
        active_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.active_label = ttk.Label(active_frame, text=f"{self.active_freq:.3f}", font=('Arial', 14))
        self.active_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Swap button (centered vertically between the two displays)
        swap_frame = ttk.Frame(self.main_frame)
        swap_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.N, tk.S))
        swap_btn = ttk.Button(swap_frame, text="SWAP", command=self.swap_frequencies)
        swap_btn.grid(row=0, column=0, padx=5, pady=20)
        
        # Standby frequency display
        standby_frame = ttk.LabelFrame(self.main_frame, text="STBY", padding="5")
        standby_frame.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.standby_label = ttk.Label(standby_frame, text=f"{self.standby_freq:.3f}", font=('Arial', 14))
        self.standby_label.grid(row=0, column=0, padx=5, pady=5)
        
    def create_standby_control_buttons(self):
        # Only standby frequency can be adjusted
        standby_controls = ttk.Frame(self.main_frame)
        standby_controls.grid(row=1, column=2, pady=5)
        
        # Coarse adjustment buttons
        ttk.Button(standby_controls, text="Coarse ↑", command=lambda: self.adjust_frequency('standby', 'coarse', 1)).grid(row=0, column=0, padx=2)
        ttk.Button(standby_controls, text="Coarse ↓", command=lambda: self.adjust_frequency('standby', 'coarse', -1)).grid(row=1, column=0, padx=2)
        # Fine adjustment buttons
        ttk.Button(standby_controls, text="Fine ↑", command=lambda: self.adjust_frequency('standby', 'fine', 1)).grid(row=0, column=1, padx=2)
        ttk.Button(standby_controls, text="Fine ↓", command=lambda: self.adjust_frequency('standby', 'fine', -1)).grid(row=1, column=1, padx=2)
        
    def adjust_frequency(self, freq_type, adjustment_type, direction):
        if freq_type != 'standby':
            return  # Only standby can be changed
        freq = self.standby_freq
        step = 1.0 if adjustment_type == 'coarse' else 0.005
        new_freq = freq + (direction * step)
        # Ensure frequency stays within valid range (118.000 - 136.975)
        new_freq = max(118.000, min(136.975, new_freq))
        self.standby_freq = new_freq
        self.standby_label.config(text=f"{self.standby_freq:.3f}")
        
    def swap_frequencies(self):
        self.active_freq, self.standby_freq = self.standby_freq, self.active_freq
        self.active_label.config(text=f"{self.active_freq:.3f}")
        self.standby_label.config(text=f"{self.standby_freq:.3f}")

    def create_aircraft_info_section(self):
        # Create a frame for aircraft information
        aircraft_frame = ttk.LabelFrame(self.main_frame, text="Aircraft Information", padding="5")
        aircraft_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Create labels and entry fields for each aircraft info
        self.aircraft_labels = {}
        self.aircraft_entries = {}
        
        # First row: editable fields (callsign and type)
        row = 0
        for field in ['callsign', 'type']:
            ttk.Label(aircraft_frame, text=f"{field.title()}:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            self.aircraft_entries[field] = ttk.Entry(aircraft_frame, width=20)
            self.aircraft_entries[field].grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
            self.aircraft_entries[field].insert(0, self.aircraft_info[field])
            row += 1
            
        # Add a separator
        ttk.Separator(aircraft_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=5)
        row += 1
        
        # Second row: read-only fields (position, altitude, heading)
        for field in ['position', 'altitude', 'heading']:
            ttk.Label(aircraft_frame, text=f"{field.title()}:").grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            self.aircraft_entries[field] = ttk.Entry(aircraft_frame, width=20, state='readonly')
            self.aircraft_entries[field].grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
            self.aircraft_entries[field].insert(0, self.aircraft_info[field])
            row += 1
            
    def update_aircraft_info(self, field, value):
        """Update a specific aircraft information field"""
        if field in self.aircraft_entries:
            self.aircraft_info[field] = value
            # Only change state for read-only fields
            if field in ['position', 'altitude', 'heading']:
                self.aircraft_entries[field].config(state='normal')
            self.aircraft_entries[field].delete(0, tk.END)
            self.aircraft_entries[field].insert(0, value)
            if field in ['position', 'altitude', 'heading']:
                self.aircraft_entries[field].config(state='readonly')
            
            # If callsign is updated, make sure it's not empty
            if field == 'callsign' and not value:
                value = 'aabbcc'  # Reset to default if empty
                self.aircraft_info[field] = value
                self.aircraft_entries[field].delete(0, tk.END)
                self.aircraft_entries[field].insert(0, value)
            
    def get_aircraft_info(self):
        """Get all current aircraft information"""
        return {field: entry.get() for field, entry in self.aircraft_entries.items()}
        
    def clear_aircraft_info(self):
        """Clear all aircraft information fields"""
        for field in self.aircraft_info:
            self.update_aircraft_info(field, '')

    def create_atc_message_display(self):
        """Create the ATC message display area"""
        message_frame = ttk.LabelFrame(self.main_frame, text="ATC Messages", padding="5")
        message_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Create text widget for messages
        self.message_text = tk.Text(message_frame, height=4, width=50, wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.message_text.config(state=tk.DISABLED)  # Make read-only
        
    def create_pilot_message_input(self):
        """Create the pilot message input area"""
        input_frame = ttk.LabelFrame(self.main_frame, text="Pilot Message", padding="5")
        input_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Create message entry
        self.message_entry = ttk.Entry(input_frame, width=50)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # Create send button
        send_button = ttk.Button(input_frame, text="Send", command=self.send_pilot_message)
        send_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', self.send_pilot_message)
        # Also bind to the frame to ensure it works even when focus is elsewhere
        input_frame.bind('<Return>', self.send_pilot_message)
        
    def send_pilot_message(self, event=None):
        """Send a pilot message to the ATC state manager"""
        message = self.message_entry.get().strip()
        if message:
            try:
                # Get current callsign from the UI entry field
                current_callsign = self.aircraft_entries['callsign'].get()
                print(f"\nSending pilot message:")
                print(f"Message: {message}")
                print(f"Callsign: {current_callsign}")
                print(f"Frequency: {self.active_freq:.3f}")
                
                # Format message with timestamp
                data = {
                    'timestamp': time.strftime('%H:%M:%S'),
                    'message': message,
                    'callsign': current_callsign,
                    'frequency': f"{self.active_freq:.3f}"
                }
                
                # Send to ATC state manager
                self.pilot_sender.sendto(
                    json.dumps(data).encode('utf-8'),
                    ('127.0.0.1', 49004)  # Different port for pilot messages
                )
                
                # Clear the entry
                self.message_entry.delete(0, tk.END)
                
                # Add to message display
                self.display_atc_message(f"PILOT: {message}")
                
            except Exception as e:
                print(f"Error sending pilot message: {e}")
                
    def __del__(self):
        """Cleanup when the object is destroyed"""
        if hasattr(self, 'pilot_sender'):
            self.pilot_sender.close()

    def create_control_buttons(self):
        """Create control buttons for starting/stopping data reception"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=5, column=0, columnspan=3, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Receiving", command=self.toggle_reception)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
    def toggle_reception(self):
        """Toggle the reception of UDP data"""
        if not self.running:
            self.start_reception()
        else:
            self.stop_reception()
            
    def start_reception(self):
        """Start receiving UDP data"""
        self.running = True
        self.start_button.config(text="Stop Receiving")
        
        # Start simulator data reception
        self.sim_udp_receiver.start_receiving()
        
        # Start ATC message reception
        self.start_atc_receiver()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_aircraft_info_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
    def stop_reception(self):
        """Stop receiving UDP data"""
        self.running = False
        self.start_button.config(text="Start Receiving")
        self.sim_udp_receiver.stop()
        self.stop_atc_receiver()
        
    def start_atc_receiver(self):
        """Start the ATC message UDP receiver"""
        self.atc_udp_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.atc_udp_receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.atc_udp_receiver.bind(('', 49003))  # Use a different port for ATC messages
        self.atc_udp_receiver.settimeout(0.1)  # Short timeout for non-blocking
        
    def stop_atc_receiver(self):
        """Stop the ATC message UDP receiver"""
        if self.atc_udp_receiver:
            self.atc_udp_receiver.close()
            self.atc_udp_receiver = None
            
    def update_aircraft_info_loop(self):
        """Continuously update aircraft information and check for ATC messages"""
        while self.running:
            # Update simulator data
            data = self.sim_udp_receiver.get_latest_data()
            if data['gps'] and data['attitude']:
                gps = data['gps']
                attitude = data['attitude']
                
                # Update only the read-only fields
                self.update_aircraft_info('position', f"{gps.latitude:.4f}, {gps.longitude:.4f}")
                self.update_aircraft_info('altitude', f"{gps.altitude:.0f} ft")
                self.update_aircraft_info('heading', f"{attitude.true_heading:.0f}°")
            
            # Check for ATC messages
            if self.atc_udp_receiver:
                try:
                    data, _ = self.atc_udp_receiver.recvfrom(1024)
                    message = data.decode('utf-8')
                    self.display_atc_message(message)
                except socket.timeout:
                    pass  # No message received, continue
                except Exception as e:
                    print(f"Error receiving ATC message: {e}")
            
            time.sleep(1.0)  # Update every second
            
    def display_atc_message(self, message):
        """Display an ATC message in the message area"""
        try:
            # Try to parse as JSON
            data = json.loads(message)
            formatted_message = f"{data.get('timestamp', '')} - {data.get('message', message)}"
        except json.JSONDecodeError:
            # If not JSON, display as plain text
            formatted_message = message
            
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, formatted_message + "\n")
        self.message_text.see(tk.END)  # Scroll to bottom
        self.message_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = RadioDisplay(root)
    root.mainloop() 