# Hotels Data Merge

This is a Django-based web application that aggregates hotel data from multiple supplier APIs, merges the data based on hotel IDs, and exposes a `POST /hotels` API endpoint to query hotels by destination ID or a list of hotel IDs. The application normalizes and cleans data, caches results for performance, and includes a comprehensive test suite.

## Features
- **API Endpoint**: `POST /hotels` accepts JSON payloads with either `destination` (integer) or `hotels` (list of hotel IDs) to retrieve merged hotel data.
- **Data Sources**: Fetches hotel data from three supplier APIs (Acme, Patagonia, Paperflies) via HTTP requests.
- **Data Merging**:
  - Merges hotel records by `hotel_id`, selecting the longest non-empty `name` and `description`.
  - Normalizes fields (e.g., `Id`, `hotel_id` → `id`) using a flexible mapping.
  - Deduplicates amenities, preferring spaced versions (e.g., "Business Center" over "BusinessCenter").
  - Categorizes amenities into `room` (e.g., "tv", "aircon") and `general`.
  - Merges unique images (supporting `url` or `link`) and booking conditions.
- **Caching**: Uses `cachetools.TTLCache` with a 1-hour TTL and max size of 100 to cache individual hotels by ID and lists by destination ID.
- **Testing**: Includes unit tests for data merging, API responses, caching, field normalization, and error handling.

## Project Structure
```
hotels_data_merge/
├── manage.py
├── hotels/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── wsgi.py
│   ├── merge_data.py
│   ├── tests.py
├── requirements.txt
└── README.md
```

- `manage.py`: Django management script.
- `hotels/settings.py`: Django configuration (includes `SECRET_KEY`, `DATABASES` for compatibility, though no database is used).
- `hotels/urls.py`: URL routing for the `POST /hotels` endpoint.
- `hotels/views.py`: Handles API requests and responses.
- `hotels/wsgi.py`: WSGI entry point for the application.
- `hotels/merge_data.py`: Core logic for fetching, normalizing, merging, and caching hotel data.
- `hotels/tests.py`: Unit tests with mocked API responses.
- `requirements.txt`: Python dependencies.

## Prerequisites
- Python 3.8+
- Virtualenv (recommended for dependency isolation)
- Access to supplier APIs (mock endpoints provided in `merge_data.py`)

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/br3hmer/hotel_data_merge
   cd hotels_data_merge
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Dependencies include:
   - `django>=5.0,<6.0`
   - `requests>=2.31.0`
   - `cachetools>=5.3.3`

4. **Run the Server**:
   - Start the Django development server
   ```bash
   python manage.py runserver
   ```

   - Hit endpoint
   ```
   curl -X POST http://localhost:8000/hotels -H "Content-Type: application/json" -d '{"destination": 5432}'
   curl -X POST http://localhost:8000/hotels -H "Content-Type: application/json" -d "{"hotels": ["iJhz"]}"
   ```

   The server starts at `http://localhost:8000`.


## Usage
### API Endpoint: `POST /hotels`
- **Method**: `POST`
- **URL**: `http://localhost:8000/hotels`
- **Content-Type**: `application/json`
- **Payload**: Either:
  - `{"hotels": ["id1", "id2", ...]}`: List of hotel IDs (strings).
  - `{"destination": 1234}`: Destination ID (integer).
- **Response**: JSON array of merged hotel objects, each with:
  - `id`: Hotel ID (string).
  - `destination_id`: Destination ID (integer).
  - `name`: Longest non-empty hotel name.
  - `location`: Dictionary with `lat`, `lng`, `address`, `city`, `country`, `postalCode`.
  - `description`: Longest non-empty description.
  - `amenities`: Dictionary with `general` and `room` lists (deduplicated, normalized).
  - `images`: Dictionary with `rooms`, `site`, `amenities` lists (unique by link).
  - `booking_conditions`: List of unique conditions.

#### Example Requests
- **By Hotel IDs**:
  ```bash
  curl -X POST http://localhost:8000/hotels -H "Content-Type: application/json" -d '{"hotels": ["iJhz", "SjyX"]}'
  ```
  Response (simplified):
  ```json
  [
    {
      "id": "iJhz",
      "destination_id": 5432,
      "name": "Beach Villas Singapore",
      "location": {
        "lat": 1.264751,
        "lng": 103.824006,
        "address": "8 Sentosa Gateway, Beach Villas, 098269",
        "city": "Singapore",
        "country": "SG",
        "postalCode": "098269"
      },
      "description": "Surrounded by tropical gardens, these upscale villas...",
      "amenities": {
        "general": ["business center", "childcare", "dry cleaning", "indoor pool", "outdoor pool", "wifi"],
        "room": ["coffee machine", "hair dryer", "iron", "kettle", "tv"]
      },
      "images": {
        "rooms": [{"link": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/2.jpg", "description": "Double room"}, ...],
        "site": [{"link": "https://d2ey9sqrvkqdfs.cloudfront.net/0qZF/1.jpg", "description": "Front"}],
        "amenities": []
      },
      "booking_conditions": ["All children are welcome...", "Pets are not allowed.", ...]
    },
    ...
  ]
  ```

- **By Destination ID**:
  ```bash
  curl -X POST http://localhost:8000/hotels -H "Content-Type: application/json" -d '{"destination": 5432}'
  ```
  Response: Array of hotels for `destination_id=5432`.

#### Error Responses
- **Invalid JSON**: 400 Bad Request (`"Invalid JSON payload"`)
- **Missing Parameters**: 400 Bad Request (`"Either 'hotels' or 'destination' parameter is required"`)
- **Empty Hotel List**: 200 OK with empty array (`[]`)

## Testing
The project includes a test suite in `hotels/tests.py` that verifies:
- Data merging and normalization.
- Caching behavior (`TTLCache` hits for `hotel_id` and `destination_id`).
- API responses for `hotels` and `destination` queries.
- Amenities deduplication (e.g., "Business Center" preferred).
- Error handling (invalid JSON, missing parameters, empty lists).

### Run Tests
```bash
python manage.py test
```

Tests use `unittest.mock` to simulate API responses, ensuring no external HTTP requests are made. The suite covers:
- `test_get_cached_hotel_data_by_hotel_ids`: Verifies merging and caching by hotel IDs.
- `test_get_cached_hotel_data_by_destination`: Tests fetching and caching by destination ID.
- `test_api_hotels_by_ids`: Checks API response for hotel ID queries.
- `test_api_hotels_by_destination`: Validates API response for destination queries.
- `test_invalid_json`, `test_missing_parameters`, `test_empty_hotels_list`: Ensure proper error handling.
- `test_amenities_deduplication`: Confirms spaced amenities are preferred.
- `test_field_normalization`: Verifies field mapping (e.g., `Id` → `id`).

## Design Decisions
- **POST vs. GET**: Uses `POST` for the `/hotels` endpoint to handle complex JSON payloads (lists of hotel IDs) and avoid URL length limits. `POST` also aligns with the processing-heavy nature of merging and caching.
- **Caching**: `cachetools.TTLCache` with 1-hour TTL ensures performance while refreshing data periodically. `maxsize=100` limits memory usage.
- **Normalization**: Flexible field mapping (e.g., `Id`, `hotel_id` → `id`) handles varied supplier data formats.
- **No Database**: Operates statelessly, storing merged data in memory (cache), as no persistent storage is needed.
- **Error Handling**: Robust handling of API failures, invalid inputs, and edge cases.

## Dependencies
- **Django**: Web framework for API and routing.
- **requests**: HTTP client for supplier API calls.
- **cachetools**: Provides `TTLCache` for in-memory caching.

## Future Improvements
- Add authentication (e.g., API keys) for the `/hotels` endpoint.
- Implement Redis for distributed caching in high-traffic scenarios.
- Implement a scheduler to call endpoint URLS and do merge periodically (maybe Cron/APScheduler)
- Add a database backend with 2 tables, hotels (primary key `hotel-id`) and destination (primary key `destination-id`)

## License
MIT License (see `LICENSE` file if included).