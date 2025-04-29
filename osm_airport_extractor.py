import requests
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from geo_utils import haversine_distance, calculate_heading

@dataclass
class Node:
    id: int
    lat: float
    lon: float
    tags: Dict[str, str]

@dataclass
class Way:
    id: int
    nodes: List[int]
    tags: Dict[str, str]

class OSMAirportExtractor:
    def __init__(self, overpass_url: str = "https://overpass-api.de/api/interpreter"):
        self.overpass_url = overpass_url
        self.nodes: Dict[int, Node] = {}
        self.ways: Dict[int, Way] = {}
        
    def _query_overpass(self, query: str) -> Dict:
        """Send a query to the Overpass API and return the response."""
        response = requests.post(self.overpass_url, data=query)
        response.raise_for_status()
        return response.json()
        
    def _process_osm_data(self, data: Dict) -> None:
        """Process the OSM data and store nodes and ways."""
        for element in data['elements']:
            if element['type'] == 'node':
                self.nodes[element['id']] = Node(
                    id=element['id'],
                    lat=element['lat'],
                    lon=element['lon'],
                    tags=element.get('tags', {})
                )
            elif element['type'] == 'way':
                self.ways[element['id']] = Way(
                    id=element['id'],
                    nodes=element['nodes'],
                    tags=element.get('tags', {})
                )
                
    def _calculate_way_length(self, way: Way) -> float:
        """Calculate the length of a way in meters."""
        length = 0
        for i in range(len(way.nodes) - 1):
            node1 = self.nodes[way.nodes[i]]
            node2 = self.nodes[way.nodes[i + 1]]
            length += haversine_distance(node1.lat, node1.lon, node2.lat, node2.lon)
        return length
        
    def _find_nearest_node(self, lat: float, lon: float, threshold: float = 0.001) -> Optional[Node]:
        """Find the nearest node to the given coordinates."""
        nearest = None
        min_distance = float('inf')
        
        for node in self.nodes.values():
            distance = haversine_distance(lat, lon, node.lat, node.lon)
            if distance < min_distance:
                min_distance = distance
                nearest = node
                
        if min_distance <= threshold:
            return nearest
        return None
        
    def extract_airport(self, icao: str) -> Dict:
        """Extract airport data from OSM."""
        # Query for the airport
        query = f"""
        [out:json];
        area["icao"="{icao}"]->.airport;
        (
            way(area.airport)["aeroway"];
            node(area.airport)["aeroway"];
        );
        out body;
        >;
        out skel qt;
        """
        
        data = self._query_overpass(query)
        self._process_osm_data(data)
        
        # Extract runways
        runways = []
        for way in self.ways.values():
            if way.tags.get('aeroway') == 'runway':
                # Get the first and last nodes of the way
                first_node = self.nodes[way.nodes[0]]
                last_node = self.nodes[way.nodes[-1]]
                
                # Calculate runway length and width
                length = self._calculate_way_length(way)
                width = float(way.tags.get('width', 45))  # Default width of 45 meters
                
                # Calculate runway heading
                heading = calculate_heading(first_node.lat, first_node.lon, last_node.lat, last_node.lon)
                
                runways.append({
                    'name': way.tags.get('ref', ''),
                    'threshold1_coords': [first_node.lat, first_node.lon],
                    'threshold2_coords': [last_node.lat, last_node.lon],
                    'width': width,
                    'length': length
                })
        
        # Extract taxiways
        taxiways = []
        for way in self.ways.values():
            if way.tags.get('aeroway') == 'taxiway':
                segments = []
                for i in range(len(way.nodes) - 1):
                    node1 = self.nodes[way.nodes[i]]
                    node2 = self.nodes[way.nodes[i + 1]]
                    segments.append({
                        'start': [node1.lat, node1.lon],
                        'end': [node2.lat, node2.lon],
                        'width': float(way.tags.get('width', 30))  # Default width of 30 meters
                    })
                taxiways.append({
                    'name': way.tags.get('ref', ''),
                    'segments': segments
                })
        
        # Extract parking positions
        parking_positions = []
        for node in self.nodes.values():
            if node.tags.get('aeroway') == 'parking_position':
                parking_positions.append({
                    'name': node.tags.get('ref', ''),
                    'coords': [node.lat, node.lon],
                    'type': node.tags.get('type', 'Commercial'),
                    'elevation': float(node.tags.get('elevation', 0)),
                    'heading': float(node.tags.get('heading', 0)),
                    'size': float(node.tags.get('size', 80))  # Default size of 80 meters
                })
        
        # Extract holding points
        holding_points = []
        for node in self.nodes.values():
            if node.tags.get('aeroway') == 'holding_position':
                holding_points.append({
                    'name': node.tags.get('ref', ''),
                    'coords': [node.lat, node.lon],
                    'associated_with': node.tags.get('associated_with', '')
                })
        
        return {
            'name': self._find_airport_name(),
            'icao': icao,
            'runways': runways,
            'taxiways': taxiways,
            'parking_positions': parking_positions,
            'holding_points': holding_points
        }
        
    def _find_airport_name(self) -> str:
        """Find the airport name from the OSM data."""
        for way in self.ways.values():
            if way.tags.get('aeroway') == 'aerodrome':
                return way.tags.get('name', '')
        return ''

def main():
    # Example usage for Graz Airport
    extractor = OSMAirportExtractor(
        overpass_url="https://overpass-api.de/api/interpreter"
    )
    
    airport_data = extractor.extract_airport(icao="LOWG")
    
    # Save to file
    with open(f"{airport_data['icao'].lower()}_airport.json", 'w') as f:
        json.dump(airport_data, f, indent=4)
    
    print(f"Airport data extracted and saved to {airport_data['icao'].lower()}_airport.json")

if __name__ == "__main__":
    main() 