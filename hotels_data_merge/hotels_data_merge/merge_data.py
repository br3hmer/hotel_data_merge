import requests
from collections import Counter, defaultdict

def merge_hotel_data():
    supplier_urls = [
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies'
    ]

    def normalize_fields(hotel):
        normalized_hotel = {}
        # Handle different ID and name keys
        normalized_hotel['id'] = hotel.get('Id', hotel.get('hotel_id', hotel.get('id')))
        normalized_hotel['destination_id'] = hotel.get('DestinationId', hotel.get('destination_id'))
        normalized_hotel['name'] = hotel.get('Name', hotel.get('hotel_name'))
        
        # Normalize location
        location = hotel.get('location', {})
        normalized_hotel['location'] = {
            'lat': hotel.get('Latitude', location.get('lat')),
            'lng': hotel.get('Longitude', location.get('lng')),
            'address': hotel.get('Address', location.get('address', '')),
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
            room_amenities_list = ["tv","coffee machine","kettle","hair dryer","iron", "aircon", "tub"]

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

        print("pear")

        # Normalize images
        normalized_hotel['images'] = hotel.get('images', {'rooms': [], 'site': [], 'amenities': []})
        
        # Normalize booking conditions
        normalized_hotel['booking_conditions'] = hotel.get('booking_conditions', [])

        return normalized_hotel

    def do_merge(hotel_id, hotels):
        destination_ids = []

        # Get most common destination_id if there is dirty data for same hotel_id
        for hotel in hotels:
            destination_ids.append(hotel['destination_id'])

        destination_id_counts = Counter(destination_ids)
        most_common_destination_id = [id for id, count in destination_id_counts.items() if count == max(destination_id_counts.values())]

        merged = {
            'id': hotel_id,
            'destination_id': most_common_destination_id,
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
    hotels_by_id_dict = defaultdict(list)
    for hotel in hotel_list:
        hotels_by_id_dict[hotel['id']].append(hotel)
    
    # for key,val in hotels_by_id_dict.items():
    #     print(f"hotels_by_id_dict[{key}]: {val}")

    merged_hotels = []
    for hotel_id, hotels in hotels_by_id_dict.items():
        merged_hotels.append(do_merge(hotel_id, hotels))
    
    return merged_hotels