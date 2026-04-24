import requests

def geocode(location):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "trip-planner-assignment/1.0"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if not data:
        return None
    return {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
        "display_name": data[0]["display_name"]
    }

def parse_osrm_step(step):
    maneuver = step.get('maneuver', {})
    return {
        "type": maneuver.get('type', ''),
        "modifier": maneuver.get('modifier', ''),
        "name": step.get('name', ''),
        "distance": round(step.get('distance', 0) / 1609.34, 1)
    }

def get_driving_distance_miles(origin_coords, dest_coords):
    url = "http://router.project-osrm.org/route/v1/driving/{},{};{},{}".format(
        origin_coords["lon"], origin_coords["lat"],
        dest_coords["lon"], dest_coords["lat"]
    )
    params = {"overview": "full", "geometries": "geojson", "steps": "true"}
    response = requests.get(url, params=params)
    data = response.json()
    if data["code"] != "Ok":
        return None, None, []
        
    route = data["routes"][0]
    distance_miles = route["distance"] / 1609.34
    geometry = route["geometry"]
    
    # Parse turn-by-turn instructions
    instructions = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            instructions.append(parse_osrm_step(step))
            
    return round(distance_miles, 2), geometry, instructions