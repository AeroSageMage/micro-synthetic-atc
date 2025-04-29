import re

points = []
with open("tools/output_recorder/output_GPS_DATA.csv") as f:
    for line in f:
        match = re.search(r"latitude=([0-9.]+), altitude=.*?ground_speed=([0-9.]+)", line)
        lon_match = re.search(r"longitude=([0-9.]+)", line)
        if match and lon_match:
            lat = float(match.group(1))
            lon = float(lon_match.group(1))
            speed = float(match.group(2))
            if 3 < speed < 15:  # likely taxiing
                points.append((lat, lon))

# Reduce to every Nth point for clarity (e.g., every 10th)
reduced_points = points[::10]

# Print as JSON segments
for i in range(len(reduced_points) - 1):
    start = reduced_points[i]
    end = reduced_points[i + 1]
    print(f'{{\"start\": [{start[0]:.6f}, {start[1]:.6f}], \"end\": [{end[0]:.6f}, {end[1]:.6f}], \"width\": 30}},')