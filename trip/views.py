from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TripInputSerializer
from .hos_calculator import plan_trip
from .geocoder import get_driving_distance_miles

class PlanTripView(APIView):
    def post(self, request):
        serializer = TripInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data

        current_coords = data['current_location']
        pickup_coords  = data['pickup_location']
        dropoff_coords = data['dropoff_location']

        # Get distances: current → pickup, then pickup → dropoff
        distance_to_pickup, deadhead_geometry, deadhead_instructions = get_driving_distance_miles(current_coords, pickup_coords)
        distance_to_dropoff, loaded_geometry, loaded_instructions = get_driving_distance_miles(pickup_coords, dropoff_coords)

        if not distance_to_pickup or not distance_to_dropoff:
            return Response(
                {"error": "Could not calculate route"},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = plan_trip(
            current_location=current_coords['display_name'],
            pickup_location=pickup_coords['display_name'],
            dropoff_location=dropoff_coords['display_name'],
            current_cycle_hours=data['current_cycle_hours'],
            distance_to_pickup=distance_to_pickup,
            distance_to_dropoff=distance_to_dropoff
        )

        # Add location info to response
        result["locations"] = {
            "current": current_coords,
            "pickup": pickup_coords,
            "dropoff": dropoff_coords
        }
        
        # Include separate geometries and instructions for map rendering
        result["route_geometry"] = {
            "deadhead": deadhead_geometry,
            "loaded": loaded_geometry
        }
        
        result["route_instructions"] = {
            "deadhead": deadhead_instructions,
            "loaded": loaded_instructions
        }

        return Response(result)