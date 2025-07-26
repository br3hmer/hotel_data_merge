from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .merge_data import get_cached_hotel_data
import json

# List of hotels
HOTEL_CACHE = None

@csrf_exempt
@require_POST
def hotels_api(request):
    global HOTEL_CACHE
    try:
        data = json.loads(request.body)
        hotel_id_list = data.get('hotels', [])
        destination_id = data.get('destination', None)

        if not hotel_id_list and destination_id is None:
            return HttpResponseBadRequest('Either "hotels" or "destination" parameter is required')

        # Get cached or freshly merged hotel data
        hotel_data = get_cached_hotel_data(hotel_id_list, destination_id)

        # Filter hotels based on input
        if hotel_id_list:
            result = [hotel for hotel in hotel_data if hotel['id'] in hotel_id_list]
        else:
            result = [hotel for hotel in hotel_data if hotel['destination_id'] == destination_id]
        
        return JsonResponse(result, safe=False)
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest(f'Invalid JSON payload: {str(e)}')
    except Exception as e:
        return HttpResponseBadRequest(f'Error: {str(e)}')