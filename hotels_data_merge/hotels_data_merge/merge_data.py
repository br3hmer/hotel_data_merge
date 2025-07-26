import requests
import copy
from collections import Counter, defaultdict
from cachetools import TTLCache

ID_WORD_LIST = ['Id', 'hotel_id', 'id']
DESTINATION_ID_WORD_LIST = ['DestinationId', 'destination_id', 'destination']
HOTEL_NAME_WORD_LIST = ['Name', 'hotel_name', 'name']
LATITUDE_WORD_LIST = ['Latitude', 'lat']
LONGITUDE_WORD_LIST = ['Longitude', 'lng']
ADDRESS_WORD_LIST = ['Address', 'address']
CITY_WORD_LIST = ['City', 'city']
COUNTRY_WORD_LIST = ['Country', 'country']
POSTALCODE_WORD_LIST = ['PostalCode', 'postalcode']
DESCRIPTION_WORD_LIST = ['Description', 'details']
AMENITIES_WORD_LIST = ['Facilities', 'amenities']

ROOM_AMENITIES_LIST = ["aircon", "bathtub", "coffee machine", "hair dryer", "iron", "kettle", "minibar", "tub", "tv"]

hotel_cache = TTLCache(maxsize=100, ttl=3600)

def get_cached_hotel_data(hotel_id_list, destination_id):
    """
    Uses both hotel_id and destionation_id as key
    """
    hotel_data_list = []
    non_cache_hotel_id_list = copy.deepcopy(hotel_id_list)
    if hotel_id_list:
        for hotel_id in hotel_id_list:
            if hotel_id in hotel_cache:
                print("hit hotel_id cache")
                hotel_data_list.append(hotel_cache[hotel_id])
                non_cache_hotel_id_list.remove(hotel_id)
    else:
        if destination_id in hotel_cache:
            print("hit destination_id cache")
            return hotel_cache[destination_id]
    
    merged_data = get_merged_hotel_data(non_cache_hotel_id_list, destination_id)

    if hotel_id_list and merged_data:
        for data in merged_data:
            hotel_cache[data['id']] = data
    elif destination_id and merged_data:
        hotel_cache[destination_id] = merged_data

    hotel_data_list.extend(merged_data)

    return hotel_data_list

# UTILITY FUNCTIONS
def dedup_amenities(amenities_list):
    """
    Keeps only similar strings that has whitespace in them
    For example, keeps "Business Center" and removes "BusinessCenter"
    """
    normalized_map = {}
    for amenity_str in amenities_list:
        normalized = amenity_str.replace(" ", "").lower()
        if normalized not in normalized_map:
            normalized_map[normalized] = amenity_str
        else:
            # Prefer the version with a space
            current = normalized_map[normalized]
            if " " in amenity_str and " " not in current:
                # replace with spaced version
                normalized_map[normalized] = amenity_str 

    return list(normalized_map.values())

def normalize_hotel_fields(hotel):
    """
    Normalize fields for hotel data data retrieved from URLS
    """
    normalized_hotel = {}
    normalized_hotel['id'] = find_associated_field_among_possible_words(hotel, ID_WORD_LIST)
    normalized_hotel['destination_id'] = find_associated_field_among_possible_words(hotel, DESTINATION_ID_WORD_LIST)
    normalized_hotel['name'] = find_associated_field_among_possible_words(hotel, HOTEL_NAME_WORD_LIST)
    
    # Normalize location
    location = hotel.get('location', {})
    normalized_hotel['location'] = {
        'lat': find_associated_field_among_possible_words(hotel, LATITUDE_WORD_LIST),
        'lng': find_associated_field_among_possible_words(hotel, LONGITUDE_WORD_LIST),
        'address': find_associated_field_among_possible_words(hotel, ADDRESS_WORD_LIST),
        'city': find_associated_field_among_possible_words(hotel, CITY_WORD_LIST),
        'country': find_associated_field_among_possible_words(hotel, COUNTRY_WORD_LIST),
        'postalCode': find_associated_field_among_possible_words(hotel, POSTALCODE_WORD_LIST),
    }
    
    # Normalize description
    normalized_hotel['description'] = find_associated_field_among_possible_words(hotel, DESCRIPTION_WORD_LIST),
    
    # Normalize amenities
    normalized_hotel['amenities'] = {'room': [], 'general': []}
    facilities = find_associated_field_among_possible_words(hotel, AMENITIES_WORD_LIST)
    if isinstance(facilities, list):
        for facility in facilities:
            facility = str(facility).lower()
            if facility in ROOM_AMENITIES_LIST:
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

# Core logic functions
def do_merge(hotel_id, hotels):
    """
    Core merging logic is here, merge data across hotels with identical hotel_id
    """
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
            merged['amenities'][category] = dedup_amenities(merged['amenities'][category])

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

def find_associated_field_among_possible_words(hotel, word_list):
    """
    Checks for multiple different strings that relates to an identical field
    For example, [Id, hote_id, id] all relates to id
    If not we need to do something like "hotel.get('Id', hotel.get('hotel_id', hotel.get('id')))""
    """
    for word in word_list:
        if word in hotel.keys():
            return hotel.get(word)

    # Case where we do not find specific field string
    return "FIELD_NOT_FOUND"

def get_merged_hotel_data(hotel_id_list, destination_id):
    if not hotel_id_list and not destination_id:
        return []

    supplier_urls = [
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/acme',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/patagonia',
        'https://5f2be0b4ffc88500167b85a0.mockapi.io/suppliers/paperflies'
    ]

    hotel_list = []
    for url in supplier_urls:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() 
            hotels = response.json()

            # Normalize hotel field names
            for hotel in hotels:
                hotel_list.append(normalize_hotel_fields(hotel))
        except requests.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            continue

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
    
    # for key,val in grouped_hotels_dict.items():
    #     print(f"grouped_hotels_dict[{key}]: {val}")

    merged_hotels = []
    if hotel_id_list:
        for key, hotels in grouped_hotels_dict.items():
            merged_hotels.append(do_merge(hotel_id=key, hotels=hotels))
    else:
        for key,hotels in grouped_hotels_dict.items():
            merged_hotels.append(do_merge(hotel_id=key[0], hotels=hotels))

    # for hotel in merged_hotels:
    #     print(f"merged_hotels: {hotel}")
    return merged_hotels