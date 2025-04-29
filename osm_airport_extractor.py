import requests
import json
from typing import Dict, List, Tuple, Optional
import math

class AirportExtractor:
    def __init__(self, icao_code: str, center_lat: float, center_lon: float, radius_meters: int = 5000):
        self.icao_code = icao_code
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_meters = radius_meters
        self.overpass_url = "http://overpass-api.de/api/interpreter"

    def _build_query(self) -> str:
        """Build the Overpass QL query for airport features."""
        return f"""
        [out:json][timeout:25];
        (
          // Get the airport boundary
          way["aeroway"="aerodrome"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
          
          // Get runways
          way["aeroway"="runway"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
          
          // Get taxiways
          way["aeroway"="taxiway"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
          
          // Get parking positions
          node["aeroway"="parking_position"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
          node["aeroway"="apron"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
          
          // Get holding points
          node["aeroway"="holding_position"](around:{self.radius_meters},{self.center_lat},{self.center_lon});
        );
        out body;
        >;
        out skel qt;
        """

    def _get_osm_data(self) -> Dict:
        """Fetch data from Overpass API."""
        query = self._build_query()
        response = requests.post(self.overpass_url, data=query)
        response.raise_for_status()
        return response.json()

    def _calculate_way_length(self, nodes: List[Dict]) -> float:
        """Calculate the length of a way in meters."""
        length = 0
        for i in range(len(nodes) - 1):
            lat1, lon1 = nodes[i]['lat'], nodes[i]['lon']
            lat2, lon2 = nodes[i + 1]['lat'], nodes[i + 1]['lon']
            length += self._haversine_distance(lat1, lon1, lat2, lon2)
        return length

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the distance between two points using the Haversine formula."""
        R = 6371000  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi/2) * math.sin(delta_phi/2) +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _get_way_nodes(self, way: Dict, elements: Dict) -> List[Dict]:
        """Get the nodes for a way from the elements dictionary."""
        nodes = []
        for node_id in way['nodes']:
            for element in elements:
                if element['type'] == 'node' and element['id'] == node_id:
                    nodes.append(element)
        return nodes

    def _clean_duplicate_points(self, segments: List[Dict]) -> List[Dict]:
        """Remove segments with duplicate start and end points."""
        cleaned_segments = []
        for segment in segments:
            if segment['start'] != segment['end']:
                cleaned_segments.append(segment)
        return cleaned_segments

    def _get_associated_runway(self, holding_point: Dict, runways: List[Dict]) -> str:
        """Find the closest runway for a holding point."""
        if not holding_point.get('coords'):
            return ""
            
        hp_lat, hp_lon = holding_point['coords']
        min_distance = float('inf')
        closest_runway = ""
        
        for runway in runways:
            # Calculate distance to both thresholds
            dist1 = self._haversine_distance(
                hp_lat, hp_lon,
                runway['threshold1_coords'][0], runway['threshold1_coords'][1]
            )
            dist2 = self._haversine_distance(
                hp_lat, hp_lon,
                runway['threshold2_coords'][0], runway['threshold2_coords'][1]
            )
            
            # Take the minimum distance
            min_dist = min(dist1, dist2)
            if min_dist < min_distance:
                min_distance = min_dist
                closest_runway = runway['name']
                
        return closest_runway

    def extract_airport_data(self) -> Dict:
        """Extract and format airport data from OSM."""
        osm_data = self._get_osm_data()
        elements = osm_data['elements']
        
        airport_data = {
            "name": f"{self.icao_code} Airport",
            "icao": self.icao_code,
            "runways": [],
            "taxiways": [],
            "parking_positions": [],
            "holding_points": []
        }

        # Process elements
        for element in elements:
            if element['type'] == 'way':
                tags = element.get('tags', {})
                
                if tags.get('aeroway') == 'runway':
                    nodes = self._get_way_nodes(element, elements)
                    if len(nodes) >= 2:
                        runway = {
                            "name": tags.get('ref', ''),
                            "threshold1_coords": [nodes[0]['lat'], nodes[0]['lon']],
                            "threshold2_coords": [nodes[-1]['lat'], nodes[-1]['lon']],
                            "width": float(tags.get('width', 45)),  # Default width if not specified
                            "length": self._calculate_way_length(nodes)
                        }
                        airport_data['runways'].append(runway)
                
                elif tags.get('aeroway') == 'taxiway':
                    nodes = self._get_way_nodes(element, elements)
                    if len(nodes) >= 2:
                        taxiway = {
                            "name": tags.get('ref', ''),
                            "segments": []
                        }
                        for i in range(len(nodes) - 1):
                            segment = {
                                "start": [nodes[i]['lat'], nodes[i]['lon']],
                                "end": [nodes[i + 1]['lat'], nodes[i + 1]['lon']],
                                "width": float(tags.get('width', 30))  # Default width if not specified
                            }
                            taxiway['segments'].append(segment)
                        # Clean up duplicate points
                        taxiway['segments'] = self._clean_duplicate_points(taxiway['segments'])
                        if taxiway['segments']:  # Only add if there are valid segments
                            airport_data['taxiways'].append(taxiway)
            
            elif element['type'] == 'node':
                tags = element.get('tags', {})
                
                if tags.get('aeroway') in ['parking_position', 'apron']:
                    parking = {
                        "name": tags.get('ref', ''),
                        "coords": [element['lat'], element['lon']],
                        "type": tags.get('type', 'Commercial'),
                        "elevation": float(tags.get('ele', 0)),
                        "heading": float(tags.get('heading', 0)),
                        "size": float(tags.get('size', 80))
                    }
                    airport_data['parking_positions'].append(parking)
                
                elif tags.get('aeroway') == 'holding_position':
                    holding = {
                        "name": tags.get('ref', ''),
                        "coords": [element['lat'], element['lon']],
                        "associated_with": ""  # Will be filled later
                    }
                    airport_data['holding_points'].append(holding)

        # Associate holding points with runways
        for holding_point in airport_data['holding_points']:
            holding_point['associated_with'] = self._get_associated_runway(holding_point, airport_data['runways'])

        return airport_data

def main():
    # Example usage for Graz Airport
    extractor = AirportExtractor(
        icao_code="LOWG",
        center_lat=47.003979,
        center_lon=15.436094,
        radius_meters=5000
    )
    
    airport_data = extractor.extract_airport_data()
    
    # Save to file
    with open(f"{extractor.icao_code.lower()}_airport.json", 'w') as f:
        json.dump(airport_data, f, indent=4)
    
    print(f"Airport data extracted and saved to {extractor.icao_code.lower()}_airport.json")

if __name__ == "__main__":
    main() 