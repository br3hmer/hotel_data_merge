import requests
from collections import Counter, defaultdict

def merge_hotel_data(hotel_id_list, destination_id):
    supplier_urls = [
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies'
    ]

    def normalize_fields(hotel):
        normalized_hotel = {}
        # Handle different ID and name keys
        normalized_hotel['id'] = hotel.get('Id', hotel.get('hotel_id', hotel.get('id')))
        normalized_hotel['destination_id'] = hotel.get('DestinationId', hotel.get('destination_id', hotel.get('destination')))
        normalized_hotel['name'] = hotel.get('Name', hotel.get('hotel_name', hotel.get('name')))
        
        # Normalize location
        location = hotel.get('location', {})
        normalized_hotel['location'] = {
            'lat': hotel.get('Latitude', location.get('lat')),
            'lng': hotel.get('Longitude', location.get('lng')),
            'address': hotel.get('Address', hotel.get('address', location.get('address', ''))),
            'city': hotel.get('City', location.get('city', '')),
            'country': hotel.get('Country', location.get('country', '')),
            'postalCode': hotel.get('PostalCode', location.get('postalCode', ''))
        }
        
        # Normalize description
        normalized_hotel['description'] = hotel.get('Description', hotel.get('details', ''))
        
        # Normalize amenities
        normalized_hotel['amenities'] = {'room': [], 'general': []}
        facilities = hotel.get('Facilities', hotel.get('amenities', {}))
        if isinstance(facilities, list):
            room_amenities_list = ["aircon", "bathtub", "coffee machine", "hair dryer", "iron", "kettle", "minibar", "tub", "tv"]

            for facility in facilities:
                facility = str(facility).lower()

                if facility in room_amenities_list:
                    normalized_hotel['amenities']['room'].append(facility)
                else:
                    normalized_hotel['amenities']['general'].append(facility)
        elif facilities:
            normalized_hotel['amenities'] = {
                'general': facilities.get('general', []),
                'room': facilities.get('room', [])
            }

        # Normalize images
        normalized_hotel['images'] = hotel.get('images', {'rooms': [], 'site': [], 'amenities': []})
        
        # Normalize booking conditions
        normalized_hotel['booking_conditions'] = hotel.get('booking_conditions', [])

        return normalized_hotel

    def do_merge(hotel_id, hotels):
        merged = {
            'id': hotel_id,
            'destination_id': hotels[0].get('destination_id'),
            'name': '',
            'location': {'lat': None, 'lng': None, 'address': '', 'city': '', 'country': '', 'postalCode': ''},
            'description': '',
            'amenities': {'general': [], 'room': []},
            'images': {'rooms': [], 'site': [], 'amenities': []},
            'booking_conditions': []
        }
        
        hotel_names = []
        description_list = []

        for hotel in hotels:
            if hotel.get('name'):
                hotel_names.append(hotel.get('name')) 

            hotel_location = hotel.get('location', {})
            for key in ['lat', 'lng', 'address', 'city', 'postalCode']:
                if hotel_location.get(key) and not merged['location'][key]:
                    merged['location'][key] = hotel_location.get(key)

            if not merged['location']['country']:
                merged['location']['country'] = hotel_location.get('country', '')

            if hotel.get('description'):
                description_list.append(hotel.get('description')) 

            amenities = hotel.get('amenities', {})
            for category in ['general', 'room']:
                merged['amenities'][category].extend([str(a).strip().lower() for a in amenities.get(category, [])])

            images = hotel.get('images', {})
            for category in ['rooms', 'site', 'amenities']:
                for img in images.get(category, []):
                    img_entry = {}
                    img_entry["link"] = img.get('url', img.get('link', ''))
                    img_entry["description"] = img.get('caption', img.get('description', ''))

                    if not any(i['link'] == img_entry['link'] for i in merged['images'][category]):
                        merged['images'][category].append(img_entry)

            conditions = hotel.get('booking_conditions', [])
            merged['booking_conditions'].extend([str(c).strip() for c in conditions])

        merged['name'] = max(hotel_names, key=len, default='')
        merged['description'] = max(description_list, key=len, default='')
        for category in ['general', 'room']:
            merged['amenities'][category] = sorted(list(set(merged['amenities'][category])))
        merged['booking_conditions'] = sorted(list(set(merged['booking_conditions'])))
        
        return merged

    hotel_list = []
    for url in supplier_urls:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            hotels = response.json()

            # Normalize field names
            for hotel in hotels:
                hotel_list.append(normalize_fields(hotel))
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            raise e

    # Group by hotel ID
    grouped_hotels_dict = defaultdict(list)
    if hotel_id_list:
        for hotel in hotel_list:
            if hotel['id'] in hotel_id_list:
                grouped_hotels_dict[hotel['id']].append(hotel)
    # Group by tuple of (hotel_id, destination_id)
    else:
        for hotel in hotel_list:
            if hotel['destination_id'] == destination_id:
                group_by_key = (hotel['id'], hotel['destination_id'])
                grouped_hotels_dict[group_by_key].append(hotel)
    
    for key,val in grouped_hotels_dict.items():
        print(f"grouped_hotels_dict[{key}]: {val}")

    merged_hotels = []
    if hotel_id_list:
        for key, hotels in grouped_hotels_dict.items():
            merged_hotels.append(do_merge(hotel_id=key, hotels=hotels))
    else:
        for key,hotels in grouped_hotels_dict.items():
            merged_hotels.append(do_merge(hotel_id=key[0], hotels=hotels))

    for hotel in merged_hotels:
        print(f"merged_hotels: {hotel}")
    return merged_hotels