import tkinter as tk
from tkinter import ttk
import math
from tools.rewinger import UDPReceiver
import threading
import time
import socket
import json
from atc_state_manager import ATCStateManager, ATCState, AircraftStatus

class RadioDisplay:
    def __init__(self, root, atc_state_manager: ATCStateManager):
        self.root = root
        self.root.title("Radio Display")
        self.atc_state_manager = atc_state_manager
        
        # Initialize frequencies
        self.active_freq = float(atc_state_manager.get_current_frequency().frequency)
        self.standby_freq = 121.500  # Default standby frequency
        
        # Initialize aircraft info with default callsign
        self.aircraft_info = {
            'callsign': atc_state_manager.callsign,
            'type': '',
            'position': '',
            'altitude': '',
            'heading': ''
        }
        
        # Initialize UDP receiver for simulator data only
        self.sim_udp_receiver = UDPReceiver()
        self.running = False
        self.update_thread = None
        
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
        
        # Start update thread
        self.start_reception()

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
        
        # Create response buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.readback_button = ttk.Button(button_frame, text="Readback", command=self.create_readback)
        self.readback_button.pack(side=tk.LEFT, padx=2)
        
        self.wilco_button = ttk.Button(button_frame, text="Wilco", command=self.send_wilco)
        self.wilco_button.pack(side=tk.LEFT, padx=2)
        
        self.ready_button = ttk.Button(button_frame, text="Ready", command=self.send_ready)
        self.ready_button.pack(side=tk.LEFT, padx=2)
        
        # Create send button
        send_button = ttk.Button(input_frame, text="Send", command=self.send_pilot_message)
        send_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', self.send_pilot_message)
        input_frame.bind('<Return>', self.send_pilot_message)

    def create_readback(self):
        """Create a readback of the last ATC message"""
        try:
            # Get the last message from the text widget
            last_line = self.message_text.get("end-2c linestart", "end-1c").strip()
            
            # Extract the message part (remove timestamp if present)
            if " - " in last_line:
                message = last_line.split(" - ", 1)[1]
            else:
                message = last_line
                
            # Remove "ATC: " prefix if present
            if message.startswith("ATC: "):
                message = message[5:]
                
            # Get current callsign
            callsign = self.aircraft_entries['callsign'].get()
            
            # Remove ATC station names from the start of the message
            station_prefixes = ["Ground: ", "Tower: ", "Departure: ", "Approach: ", "Center: "]
            for prefix in station_prefixes:
                if message.startswith(prefix):
                    message = message[len(prefix):]
                    break
            
            # Create readback by moving callsign to the end
            if callsign in message:
                # Remove callsign from start if present
                message = message.replace(f"{callsign}, ", "")
                # Add callsign at the end
                readback = f"{message}, {callsign}"
            else:
                # If no callsign in message, just add it at the end
                readback = f"{message}, {callsign}"
            
            # Set the readback in the message entry
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, readback)
            
        except Exception as e:
            print(f"Error creating readback: {e}")
        
    def send_wilco(self):
        """Send a 'Wilco' acknowledgment"""
        callsign = self.aircraft_entries['callsign'].get()
        message = f"Wilco, {callsign}"
        self.send_pilot_message(message)

    def send_ready(self):
        """Send a 'Ready' report"""
        callsign = self.aircraft_entries['callsign'].get()
        message = f"Ready to {self.get_ready_action()}, {callsign}"
        self.send_pilot_message(message)

    def get_ready_action(self):
        """Get the action to report ready for based on current state"""
        # This would need to be implemented based on the current state and expected action
        return "taxi"  # Default for now

    def send_pilot_message(self, message=None):
        """Send a pilot message to the ATC state manager"""
        if message is None:
            message = self.message_entry.get().strip()
        
        if message:
            try:
                # Get current callsign
                current_callsign = self.aircraft_entries['callsign'].get()
                print(f"\nSending pilot message:")
                print(f"Message: {message}")
                print(f"Callsign: {current_callsign}")
                print(f"Frequency: {self.active_freq:.3f}")
                
                # Add pilot message to display first
                self.display_atc_message(f"PILOT: {message}")
                
                # Send to ATC state manager
                self.atc_state_manager.handle_pilot_message(
                    message=message,
                    current_frequency=f"{self.active_freq:.3f}",
                    callsign=current_callsign
                )
                
                # Clear the entry if it was a manual message
                if message == self.message_entry.get().strip():
                    self.message_entry.delete(0, tk.END)
                
                # Update UI based on new state
                self.update_ui_for_state()
                
            except Exception as e:
                print(f"Error sending pilot message: {e}")

    def display_atc_message(self, message):
        """Display an ATC message in the message area"""
        try:
            # Try to parse as JSON (for UDP messages)
            data = json.loads(message)
            formatted_message = f"{data.get('timestamp', '')} - {data.get('message', message)}"
        except json.JSONDecodeError:
            # If not JSON, it's a direct message from state manager
            timestamp = time.strftime('%H:%M:%S')
            formatted_message = f"{timestamp} - {message}"
            
            # Use after() to schedule the UI update in the main thread
            # Add a realistic delay for ATC responses (1.5 seconds)
            # Don't add delay for pilot messages
            if message.startswith("PILOT:"):
                self.root.after(0, self._update_message_display, formatted_message)
            else:
                self.root.after(1500, self._update_message_display, formatted_message)
        
    def _update_message_display(self, formatted_message):
        """Update the message display in the main thread"""
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, formatted_message + "\n")
        self.message_text.see(tk.END)  # Scroll to bottom
        self.message_text.config(state=tk.DISABLED)
        
        # Update UI based on new message
        self.update_ui_for_state()

    def update_ui_for_state(self):
        """Update UI elements based on current ATC state and expected response"""
        # Use after() to schedule the UI update in the main thread
        self.root.after(0, self._update_ui_in_main_thread)
        
    def _update_ui_in_main_thread(self):
        """Update UI elements in the main thread"""
        # Get current state and expected response
        current_state = self.atc_state_manager.current_state
        expected_response = self.atc_state_manager.get_expected_response()
        
        # Update frequency display
        current_freq = self.atc_state_manager.get_current_frequency()
        self.active_freq = float(current_freq.frequency)
        self.active_label.config(text=f"{self.active_freq:.3f}")
        
        # Update callsign if it changed in the state manager
        if self.atc_state_manager.callsign != self.aircraft_info['callsign']:
            self.update_aircraft_info('callsign', self.atc_state_manager.callsign)
        
        # Enable/disable buttons based on state
        if expected_response:
            self.readback_button.config(state='normal' if expected_response.requires_readback else 'disabled')
            self.wilco_button.config(state='normal' if expected_response.requires_acknowledgment else 'disabled')
            self.ready_button.config(state='normal' if expected_response.requires_ready_report else 'disabled')
        else:
            # Disable all response buttons if no response expected
            self.readback_button.config(state='disabled')
            self.wilco_button.config(state='disabled')
            self.ready_button.config(state='disabled')

    def start_reception(self):
        """Start receiving UDP data"""
        self.running = True
        self.start_button.config(text="Stop Receiving")
        
        # Start simulator data reception
        self.sim_udp_receiver.start_receiving()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_aircraft_info_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
    def stop_reception(self):
        """Stop receiving UDP data"""
        self.running = False
        self.start_button.config(text="Start Receiving")
        self.sim_udp_receiver.stop()
        
    def update_aircraft_info_loop(self):
        """Continuously update aircraft information"""
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
                
                # Update aircraft status in state manager
                # This would need to be implemented based on position and other factors
                # self.atc_state_manager.update_aircraft_status(new_status)
            
            time.sleep(1.0)  # Update every second

    def create_control_buttons(self):
        """Create control buttons for the radio display"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=5, column=0, columnspan=3, pady=5)
        
        # Create start/stop button
        self.start_button = ttk.Button(control_frame, text="Start Receiving", command=self.toggle_reception)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
    def toggle_reception(self):
        """Toggle the reception state"""
        if self.running:
            self.stop_reception()
        else:
            self.start_reception()

if __name__ == "__main__":
    from airport_manager import AirportManager
    
    # Initialize ATC state manager
    airport_manager = AirportManager("airport_layout.json")
    atc_state_manager = ATCStateManager(airport_manager)
    
    # Create and run the UI
    root = tk.Tk()
    app = RadioDisplay(root, atc_state_manager)
    root.mainloop() 