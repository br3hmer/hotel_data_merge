from django.test import TestCase, Client
from django.urls import reverse

import json

from unittest.mock import patch, Mock
from .merge_data import get_cached_hotel_data, hotel_cache

# Mock data mimicking supplier APIs (acme, patagonia, paperflies)
MOCK_ACME = [
    {
        "Id": "iJhz",
        "DestinationId": 5432,
        "Name": "Beach Villas Singapore",
        "Latitude": 1.264751,
        "Longitude": 103.824006,
        "Address": " 8 Sentosa Gateway, Beach Villas ",
        "City": "Singapore",
        "Country": "SG",
        "PostalCode": "098269",
        "Description": "  This 5 star hotel is located on the coastline of Singapore.",
        "Facilities": [
          "Pool",
          "BusinessCenter",
          "WiFi ",
          "DryCleaning",
          " Breakfast"
        ]
    },
    {
        "Id": "SjyX",
        "DestinationId": 5432,
        "Name": "InterContinental Singapore Robertson Quay",
        "Latitude": None,
        "Longitude": None,
        "Address": " 1 Nanson Road",
        "City": "Singapore",
        "Country": "SG",
        "PostalCode": "238909",
        "Description": "Enjoy sophisticated waterfront living at the new InterContinental® Singapore Robertson Quay, luxury's preferred address nestled in the heart of Robertson Quay along the Singapore River, with the CBD just five minutes drive away. Magnifying the comforts of home, each of our 225 studios and suites features a host of thoughtful amenities that combine modernity with elegance, whilst maintaining functional practicality. The hotel also features a chic, luxurious Club InterContinental Lounge.",
        "Facilities": [
          "Pool",
          "WiFi ",
          "Aircon",
          "BusinessCenter",
          "BathTub",
          "Breakfast",
          "DryCleaning",
          "Bar"
        ]
    },
    {
        "Id": "f8c9",
        "DestinationId": 1122,
        "Name": "Hilton Shinjuku Tokyo",
        "Latitude": "",
        "Longitude": "",
        "Address": "160-0023, SHINJUKU-KU, 6-6-2 NISHI-SHINJUKU, JAPAN",
        "City": "Tokyo",
        "Country": "JP",
        "PostalCode": "160-0023",
        "Description": "Hilton Tokyo is located in Shinjuku, the heart of Tokyo's business, shopping and entertainment district, and is an ideal place to experience modern Japan. A complimentary shuttle operates between the hotel and Shinjuku station and the Tokyo Metro subway is connected to the hotel. Relax in one of the modern Japanese-style rooms and admire stunning city views. The hotel offers WiFi and internet access throughout all rooms and public space.",
        "Facilities": [
          "Pool",
          "WiFi ",
          "BusinessCenter",
          "DryCleaning",
          " Breakfast",
          "Bar",
          "BathTub"
        ]
    }

]

MOCK_PATAGONIA = [
     {
        "id": "iJhz",
        "destination": 5432,
        "name": "Beach Villas Singapore",
        "lat": 1.264751,
        "lng": 103.824006,
        "address": "8 Sentosa Gateway, Beach Villas, 098269",
        "info": "Located at the western tip of Resorts World Sentosa, guests at the Beach Villas are guaranteed privacy while they enjoy spectacular views of glittering waters. Guests will find themselves in paradise with this series of exquisite tropical sanctuaries, making it the perfect setting for an idyllic retreat. Within each villa, guests will discover living areas and bedrooms that open out to mini gardens, private timber sundecks and verandahs elegantly framing either lush greenery or an expanse of sea. Guests are assured of a superior slumber with goose feather pillows and luxe mattresses paired with 400 thread count Egyptian cotton bed linen, tastefully paired with a full complement of luxurious in-room amenities and bathrooms boasting rain showers and free-standing tubs coupled with an exclusive array of ESPA amenities and toiletries. Guests also get to enjoy complimentary day access to the facilities at Asia’s flagship spa – the world-renowned ESPA.",
        "amenities": [
          "Aircon",
          "Tv",
          "Coffee machine",
          "Kettle",
          "Hair dryer",
          "Iron",
          "Tub"
        ],
        "images": {
          "rooms": [
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/2.jpg",
              "description": "Double room"
            },
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/4.jpg",
              "description": "Bathroom"
            }
          ],
          "amenities": [
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/0.jpg",
              "description": "RWS"
            },
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/6.jpg",
              "description": "Sentosa Gateway"
            }
          ]
        }
    },
    {
        "id": "f8c9",
        "destination": 1122,
        "name": "Hilton Tokyo Shinjuku",
        "lat": 35.6926,
        "lng": 139.690965,
        "address": None,
        "info": None,
        "amenities": None,
        "images": {
          "rooms": [
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i10_m.jpg",
              "description": "Suite"
            },
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i11_m.jpg",
              "description": "Suite - Living room"
            }
          ],
          "amenities": [
            {
              "url": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i57_m.jpg",
              "description": "Bar"
            }
          ]
        }
    }
]

MOCK_PAPERFLIES = [
    {
        "hotel_id": "iJhz",
        "destination_id": 5432,
        "hotel_name": "Beach Villas Singapore",
        "location": {
          "address": "8 Sentosa Gateway, Beach Villas, 098269",
          "country": "Singapore"
        },
        "details": "Surrounded by tropical gardens, these upscale villas in elegant Colonial-style buildings are part of the Resorts World Sentosa complex and a 2-minute walk from the Waterfront train station. Featuring sundecks and pool, garden or sea views, the plush 1- to 3-bedroom villas offer free Wi-Fi and flat-screens, as well as free-standing baths, minibars, and tea and coffeemaking facilities. Upgraded villas add private pools, fridges and microwaves; some have wine cellars. A 4-bedroom unit offers a kitchen and a living room. There's 24-hour room and butler service. Amenities include posh restaurant, plus an outdoor pool, a hot tub, and free parking.",
        "amenities": {
          "general": [
            "outdoor pool",
            "indoor pool",
            "business center",
            "childcare"
          ],
          "room": [
            "tv",
            "coffee machine",
            "kettle",
            "hair dryer",
            "iron"
          ]
        },
        "images": {
          "rooms": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/2.jpg",
              "caption": "Double room"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/3.jpg",
              "caption": "Double room"
            }
          ],
          "site": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/1.jpg",
              "caption": "Front"
            }
          ]
        },
        "booking_conditions": [
          "All children are welcome. One child under 12 years stays free of charge when using existing beds. One child under 2 years stays free of charge in a child's cot/crib. One child under 4 years stays free of charge when using existing beds. One older child or adult is charged SGD 82.39 per person per night in an extra bed. The maximum number of children's cots/cribs in a room is 1. There is no capacity for extra beds in the room.",
          "Pets are not allowed.",
          "WiFi is available in all areas and is free of charge.",
          "Free private parking is possible on site (reservation is not needed).",
          "Guests are required to show a photo identification and credit card upon check-in. Please note that all Special Requests are subject to availability and additional charges may apply. Payment before arrival via bank transfer is required. The property will contact you after you book to provide instructions. Please note that the full amount of the reservation is due before arrival. Resorts World Sentosa will send a confirmation with detailed payment information. After full payment is taken, the property's details, including the address and where to collect keys, will be emailed to you. Bag checks will be conducted prior to entry to Adventure Cove Waterpark. === Upon check-in, guests will be provided with complimentary Sentosa Pass (monorail) to enjoy unlimited transportation between Sentosa Island and Harbour Front (VivoCity). === Prepayment for non refundable bookings will be charged by RWS Call Centre. === All guests can enjoy complimentary parking during their stay, limited to one exit from the hotel per day. === Room reservation charges will be charged upon check-in. Credit card provided upon reservation is for guarantee purpose. === For reservations made with inclusive breakfast, please note that breakfast is applicable only for number of adults paid in the room rate. Any children or additional adults are charged separately for breakfast and are to paid directly to the hotel."
        ]
    },
    {
        "hotel_id": "SjyX",
        "destination_id": 5432,
        "hotel_name": "InterContinental",
        "location": {
          "address": "1 Nanson Rd, Singapore 238909",
          "country": "Singapore"
        },
        "details": "InterContinental Singapore Robertson Quay is luxury's preferred address offering stylishly cosmopolitan riverside living for discerning travelers to Singapore. Prominently situated along the Singapore River, the 225-room inspiring luxury hotel is easily accessible to the Marina Bay Financial District, Central Business District, Orchard Road and Singapore Changi International Airport, all located a short drive away. The hotel features the latest in Club InterContinental design and service experience, and five dining options including Publico, an Italian landmark dining and entertainment destination by the waterfront.",
        "amenities": {
          "general": [
            "outdoor pool",
            "business center",
            "childcare",
            "parking",
            "bar",
            "dry cleaning",
            "wifi",
            "breakfast",
            "concierge"
          ],
          "room": [
            "aircon",
            "minibar",
            "tv",
            "bathtub",
            "hair dryer"
          ]
        },
        "images": {
          "rooms": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i93_m.jpg",
              "caption": "Double room"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i94_m.jpg",
              "caption": "Bathroom"
            }
          ],
          "site": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i1_m.jpg",
              "caption": "Restaurant"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i2_m.jpg",
              "caption": "Hotel Exterior"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i5_m.jpg",
              "caption": "Entrance"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/Sjym/i24_m.jpg",
              "caption": "Bar"
            }
          ]
        },
        "booking_conditions": []
    },
    {
        "hotel_id": "f8c9",
        "destination_id": 1122,
        "hotel_name": "Hilton Tokyo",
        "location": {
          "address": "160-0023, SHINJUKU-KU, 6-6-2 NISHI-SHINJUKU, JAPAN",
          "country": "Japan"
        },
        "details": "This sleek high-rise property is 10 minutes' walk from Shinjuku train station, 6 minutes' walk from the Tokyo Metropolitan Government Building and 3 km from Yoyogi Park. The polished rooms offer Wi-Fi and flat-screen TVs, plus minibars, sitting areas, and tea and coffeemaking facilities. Suites add living rooms, and access to a club lounge serving breakfast and cocktails. A free shuttle to Shinjuku station is offered. There's a chic Chinese restaurant, a sushi bar, and a grill restaurant with an open kitchen, as well as an English pub and a hip cocktail lounge. Other amenities include a gym, rooftop tennis courts, and a spa with an indoor pool.",
        "amenities": {
          "general": [
            "indoor pool",
            "business center",
            "wifi"
          ],
          "room": [
            "tv",
            "aircon",
            "minibar",
            "bathtub",
            "hair dryer"
          ]
        },
        "images": {
          "rooms": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i1_m.jpg",
              "caption": "Suite"
            },
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i15_m.jpg",
              "caption": "Double room"
            }
          ],
          "site": [
            {
              "link": "https://d2ey9sqrvkqdfs.cloudfront.net/YwAr/i55_m.jpg",
              "caption": "Bar"
            }
          ]
        },
        "booking_conditions": [
          "All children are welcome. One child under 6 years stays free of charge when using existing beds. There is no capacity for extra beds in the room.",
          "Pets are not allowed.",
          "Wired internet is available in the hotel rooms and charges are applicable. WiFi is available in the hotel rooms and charges are applicable.",
          "Private parking is possible on site (reservation is not needed) and costs JPY 1500 per day.",
          "When booking more than 9 rooms, different policies and additional supplements may apply.",
          "The hotel's free shuttle is offered from Bus Stop #21 in front of Keio Department Store at Shinjuku Station. It is available every 20-minutes from 08:20-21:40. The hotel's free shuttle is offered from the hotel to Shinjuku Train Station. It is available every 20-minutes from 08:12-21:52. For more details, please contact the hotel directly. At the Executive Lounge a smart casual dress code is strongly recommended. Attires mentioned below are strongly discouraged and may not permitted: - Night attire (slippers, Yukata robe, etc.) - Gym clothes/sportswear (Tank tops, shorts, etc.) - Beachwear (flip-flops, sandals, etc.) and visible tattoos. Please note that due to renovation works, the Executive Lounge will be closed from 03 January 2019 until late April 2019. During this period, guests may experience some noise or minor disturbances. Smoking preference is subject to availability and cannot be guaranteed."
        ]
    }
]

class HotelsApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('hotels_api')
        # Clear cache before each test to ensure isolation
        hotel_cache.clear()

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_get_cached_hotel_data_by_hotel_ids(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test fetching by hotel IDs
        hotels = get_cached_hotel_data(hotel_id_list=['iJhz', 'SjyX'], destination_id=None)
        self.assertEqual(len(hotels), 2)
        self.assertEqual({h['id'] for h in hotels}, {'iJhz', 'SjyX'})

        # Verify merged data for hotel_id: iJhz
        hotel_iJhz = next(h for h in hotels if h['id'] == 'iJhz')
        self.assertEqual(hotel_iJhz['name'], 'Beach Villas Singapore')
        self.assertEqual(hotel_iJhz['location']['country'], 'SG')
        self.assertEqual(hotel_iJhz['location']['postalCode'], '098269')
        self.assertIn('outdoor pool', hotel_iJhz['amenities']['general'])
        self.assertIn('tv', hotel_iJhz['amenities']['room'])
        self.assertTrue(len(hotel_iJhz['images']['rooms']) >= 2)
        self.assertTrue(len(hotel_iJhz['booking_conditions']) >= 5)
        # Dedup prefers spaced version 
        self.assertIn('business center', hotel_iJhz['amenities']['general']) 

        # Verify cache hit for hotel_id
        hotels_cached = get_cached_hotel_data(hotel_id_list=['iJhz'], destination_id=None)
        self.assertEqual([hotel_iJhz], hotels_cached)

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_get_cached_hotel_data_by_destination(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test fetching by destination ID
        hotels = get_cached_hotel_data(hotel_id_list=None, destination_id=5432)
        self.assertEqual(len(hotels), 2)
        self.assertTrue(all(h['destination_id'] == 5432 for h in hotels))

        # Verify cache hit for destination_id
        hotels_cached = get_cached_hotel_data(hotel_id_list=None, destination_id=5432)
        # Cache hit, same list
        self.assertEqual(hotels, hotels_cached)  

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_api_hotels_by_ids(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test POST /hotels with hotel IDs
        response = self.client.post(
            self.url,
            json.dumps({'hotels': ['iJhz', 'SjyX']}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual({h['id'] for h in data}, {'iJhz', 'SjyX'})

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_api_hotels_by_destination(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test POST /hotels with destination ID
        response = self.client.post(
            self.url,
            json.dumps({'destination': 5432}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertTrue(all(h['destination_id'] == 5432 for h in data))

    def test_invalid_json(self):
        # Test invalid JSON payload
        response = self.client.post(self.url, 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_parameters(self):
        # Test missing hotels and destination parameters
        response = self.client.post(self.url, json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_empty_hotels_list(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test POST /hotels with empty hotel list should return 400
        response = self.client.post(
            self.url,
            json.dumps({'hotels': []}),
            content_type='text/html; charset=utf-8'
        )
        self.assertEqual(response.status_code, 400)

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_amenities_deduplication(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test deduplication prefers spaced amenities
        hotels = get_cached_hotel_data(hotel_id_list=['iJhz'], destination_id=None)
        hotel = next(h for h in hotels if h['id'] == 'iJhz')
        self.assertIn('business center', hotel['amenities']['general'])
        self.assertNotIn('businesscenter', hotel['amenities']['general'])
        self.assertIn('wifi', hotel['amenities']['general'])
        self.assertNotIn('wi fi', hotel['amenities']['general'])

    @patch('hotels_data_merge.merge_data.requests.get')
    def test_field_normalization(self, mock_get):
        # Mock API responses
        mock_response = Mock()
        mock_response.json.side_effect = [MOCK_ACME, MOCK_PATAGONIA, MOCK_PAPERFLIES]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test field normalization
        hotels = get_cached_hotel_data(hotel_id_list=['iJhz'], destination_id=None)
        hotel = next(h for h in hotels if h['id'] == 'iJhz')
        self.assertEqual(hotel['id'], 'iJhz')
        self.assertEqual(hotel['destination_id'], 5432)
        self.assertEqual(hotel['name'], 'Beach Villas Singapore')
        self.assertEqual(hotel['location']['address'], '8 Sentosa Gateway, Beach Villas, 098269')
        self.assertEqual(hotel['location']['country'], 'SG')
        self.assertEqual(hotel['description'], "Located at the western tip of Resorts World Sentosa, guests at the Beach Villas are guaranteed privacy while they enjoy spectacular views of glittering waters. Guests will find themselves in paradise with this series of exquisite tropical sanctuaries, making it the perfect setting for an idyllic retreat. Within each villa, guests will discover living areas and bedrooms that open out to mini gardens, private timber sundecks and verandahs elegantly framing either lush greenery or an expanse of sea. Guests are assured of a superior slumber with goose feather pillows and luxe mattresses paired with 400 thread count Egyptian cotton bed linen, tastefully paired with a full complement of luxurious in-room amenities and bathrooms boasting rain showers and free-standing tubs coupled with an exclusive array of ESPA amenities and toiletries. Guests also get to enjoy complimentary day access to the facilities at Asia’s flagship spa – the world-renowned ESPA.")