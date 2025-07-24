from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .merge_data import merge_hotel_data
import json

@csrf_exempt
@require_POST
def hotels_api(request):
    global HOTEL_CACHE
    try:
        print("request.body: ", request.body)
        data = json.loads(request.body)
        print("data: ", data)
        hotels = data.get('hotels', [])
        destination = data.get('destination', None)

        if not hotels and destination is None:
            return HttpResponseBadRequest('Either "hotels" or "destination" parameter is required')

        result = merge_hotel_data()
        return JsonResponse(result, safe=False)
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest(f'Invalid JSON payload: {str(e)}')
    except Exception as e:
        return HttpResponseBadRequest(f'Error: {str(e)}')