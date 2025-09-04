# Lost and Found System API Documentation

## Overview
This API provides comprehensive functionality for managing lost and found items at Parklands Sports Club. It supports reporting lost items with images, reporting found items, automatic matching with configurable thresholds, email notifications, receipt printing, system settings management, and comprehensive reporting.

**Key Features:**
- When posting lost/found items, potential matches are detected and emails are sent automatically if they exceed the threshold
- Match data is not returned in POST responses to keep responses lightweight
- Use `/found/generate_matches/` to get a list of potential matches with minimal data
- Use `/found/match_details/` with specific item IDs to get full match details when needed

## Recent Updates (v2.1)
- ✅ **Image Upload Support**: Lost items now accept photo uploads
- ✅ **Configurable System Settings**: Adjustable match thresholds and system parameters
- ✅ **Auto-Printing**: Automatic receipt printing for lost/found items
- ✅ **Enhanced Email System**: Bulk email communications and individual notifications
- ✅ **Advanced Reporting**: CSV/PDF exports for all item types
- ✅ **Production Ready**: Security validations, logging, and performance optimizations
- ✅ **Customizable Email Templates**: Email content can be customized from settings
- ✅ **Email Rate Limiting**: Configurable limits on auto-sent emails per day and per item
- ✅ **Email Logging**: Track all sent emails for auditing and compliance

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Base URL
```
/api/lostfound/
```

---

## 1. Lost Items Endpoints

### 1.1 List/Create Lost Items
**Endpoint:** `GET/POST /lost/`

#### GET - List Lost Items
**Query Parameters:**
- `type` (optional): Filter by type (`card` or `item`)
- `search` (optional): Search in item_name, owner_name, etc.

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "tracking_id": "LI-A1B2C3D4",
      "type": "item",
      "item_name": "iPhone 12",
      "description": "Black iPhone with blue case",
      "card_last_four": "A1234",
      "place_lost": "Tennis Court",
      "owner_name": "John Doe",
      "reporter_email": "john@example.com",
      "reporter_phone": "+254712345678",
      "reporter_member_id": "PSC001",
      "status": "pending",
      "photo": "/media/lost_items/photos/photo.jpg",
      "date_reported": "2024-01-15T10:30:00Z",
      "last_updated": "2024-01-15T10:30:00Z",
      "reported_by": 1
    }
  ]
}
```

#### POST - Create Lost Item
**Request Body (JSON):**
```json
{
  "type": "item",
  "item_name": "iPhone 12",
  "description": "Black iPhone with blue case",
  "place_lost": "Tennis Court",
  "owner_name": "John Doe",
  "reporter_email": "john@example.com",
  "reporter_phone": "+254712345678",
  "reporter_member_id": "PSC001"
}
```

**File Upload (multipart/form-data):**
```
photo: <image_file> (JPG, PNG, JPEG - max 5MB)
```

**Response:**
```json
{
  "id": 1,
  "tracking_id": "LI-A1B2C3D4",
  "type": "item",
  "item_name": "iPhone 12",
  "description": "Black iPhone with blue case",
  "place_lost": "Tennis Court",
  "owner_name": "John Doe",
  "reporter_email": "john@example.com",
  "reporter_phone": "+254712345678",
  "reporter_member_id": "PSC001",
  "status": "pending",
  "photo": "/media/lost_items/photos/photo.jpg",
  "date_reported": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z",
  "reported_by": 1,
  "acknowledgment": "Potential matches found and emails sent to john@example.com"
}
```

### 1.2 Retrieve/Update/Delete Lost Item
**Endpoint:** `GET/PUT/PATCH/DELETE /lost/{id}/`

#### GET - Retrieve Lost Item
**Response:** Same as individual item in list response

#### PUT/PATCH - Update Lost Item
**Request Body:** Same as POST, but all fields optional for PATCH

#### DELETE - Delete Lost Item
**Response:** `204 No Content`

### 1.3 Print Receipt for Lost Item
**Endpoint:** `POST /lost/{id}/print_receipt/`

**Response:**
```json
{
  "message": "Receipt printed successfully"
}
```

### 1.4 Send Email to Lost Item Reporter
**Endpoint:** `POST /lost/{id}/send_email/`

**Request Body:**
```json
{
  "subject": "Lost Item Update",
  "message": "We have found a potential match for your lost item..."
}
```

**Response:**
```json
{
  "message": "Email sent successfully"
}
```

### 1.5 Export Lost Items to CSV
**Endpoint:** `GET /lost/export_csv/`

**Response:** CSV file download with headers:
```
Tracking ID,Type,Item Name,Owner Name,Place Lost,Status,Date Reported
```

### 1.6 Export Lost Items to PDF
**Endpoint:** `GET /lost/export_pdf/`

**Response:** PDF file download

### 1.7 Print Receipt for Lost Item
**Endpoint:** `POST /lost/{id}/print_receipt/`

**Response:**
```json
{
  "message": "Receipt printed successfully"
}
```

### 1.8 Send Email to Lost Item Reporter
**Endpoint:** `POST /lost/{id}/send_email/`

**Request Body:**
```json
{
  "subject": "Lost Item Update",
  "message": "We have found a potential match for your lost item..."
}
```

**Response:**
```json
{
  "message": "Email sent successfully"
}
```

---

## 2. Found Items Endpoints

### 2.1 List/Create Found Items
**Endpoint:** `GET/POST /found/`

#### GET - List Found Items
**Query Parameters:**
- `type` (optional): Filter by type (`card` or `item`)

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "type": "item",
      "item_name": "iPhone 12",
      "description": "Black iPhone found on tennis court",
      "card_last_four": "A1234",
      "place_found": "Tennis Court",
      "finder_name": "Jane Smith",
      "finder_phone": "+254712345679",
      "owner_name": null,
      "status": "found",
      "photo": "/media/found_items/photos/found_phone.jpg",
      "date_reported": "2024-01-15T11:00:00Z",
      "last_updated": "2024-01-15T11:00:00Z"
    }
  ]
}
```

#### POST - Create Found Item
**Request Body:**
```json
{
  "type": "item",
  "item_name": "iPhone 12",
  "description": "Black iPhone found on tennis court",
  "place_found": "Tennis Court",
  "finder_name": "Jane Smith",
  "finder_phone": "+254712345679",
  "photo": "<image_file>"
}
```

**Response:**
```json
{
  "id": 1,
  "type": "item",
  "item_name": "iPhone 12",
  "description": "Black iPhone found on tennis court",
  "place_found": "Tennis Court",
  "finder_name": "Jane Smith",
  "finder_phone": "+254712345679",
  "status": "found",
  "photo": "/media/found_items/photos/found_phone.jpg",
  "date_reported": "2024-01-15T11:00:00Z",
  "last_updated": "2024-01-15T11:00:00Z",
  "acknowledgment": "Potential matches found and emails sent to john@example.com"
}
```

### 2.2 Retrieve/Update/Delete Found Item
**Endpoint:** `GET/PUT/PATCH/DELETE /found/{id}/`

Same structure as Lost Items endpoints.

### 2.3 Print Receipt for Found Item
**Endpoint:** `POST /found/{id}/print_receipt/`

**Response:**
```json
{
  "message": "Receipt printed successfully"
}
```

### 2.4 Export Found Items to CSV
**Endpoint:** `GET /found/export_csv/`

**Response:** CSV file download

### 2.5 Export Found Items to PDF
**Endpoint:** `GET /found/export_pdf/`

**Response:** PDF file download

### 2.6 Print Receipt for Found Item
**Endpoint:** `POST /found/{id}/print_receipt/`

**Response:**
```json
{
  "message": "Receipt printed successfully"
}
```

### 2.7 Export Found Items to CSV
**Endpoint:** `GET /found/export_csv/`

**Response:** CSV file download

### 2.8 Export Found Items to PDF
**Endpoint:** `GET /found/export_pdf/`

**Response:** PDF file download

### 2.9 Generate Matches
**Endpoint:** `GET /found/generate_matches/`

**Description:** Generate potential matches between lost and found items based on configurable similarity thresholds. This endpoint performs a comprehensive search across all items to find potential matches.

**Query Parameters:**
- `tracking_id` (optional): Filter matches for a specific lost item tracking ID (e.g., `LI-A1B2C3D4`)
- If not provided, returns matches for all lost items

**Authentication:** Required (JWT token)

**Matching Algorithm:**
The system uses a weighted scoring algorithm with the following components:
- **Type Match (30%)**: Items must be the same type (card/item)
- **Name Similarity (20%)**: Uses SequenceMatcher for fuzzy string matching
- **Description Similarity (20%)**: Compares item descriptions
- **Location Similarity (15%)**: Matches place lost/found locations
- **Time Proximity (15%)**: Items reported within 7 days get higher scores

**Threshold Configuration:**
- Uses `generate_match_threshold` setting (default: 0.5)
- Only matches with scores above this threshold are returned

**Performance Notes:**
- Large datasets may take time to process
- Results are sorted by match score (highest first)
- Limited to items reported within the configured time window

**Response:**
```json
{
  "matches": [
    {
      "lost_item_id": 1,
      "found_item_id": 2,
      "match_score": 85.5,
      "match_reasons": [
        "Matching type: item",
        "Similar item names (85% match)",
        "Similar descriptions (72% match)",
        "Same location",
        "Reported within 2 hours of each other"
      ]
    },
    {
      "lost_item_id": 1,
      "found_item_id": 5,
      "match_score": 67.3,
      "match_reasons": [
        "Matching type: item",
        "Similar item names (78% match)",
        "Reported within 1 day of each other"
      ]
    }
  ]
}
```

**Response Fields:**
- `lost_item_id`: ID of the lost item
- `found_item_id`: ID of the potential matching found item
- `match_score`: Similarity score as percentage (0-100)
- `match_reasons`: Array of human-readable reasons for the match

**Error Responses:**
- `400 Bad Request`: Invalid tracking_id format
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Tracking ID not found

### 2.10 Get Match Details
**Endpoint:** `GET /found/match_details/`

**Description:** Get detailed information about a specific potential match between a lost and found item, including full item details and comprehensive matching analysis.

**Query Parameters:**
- `lost_item_id` (required): Numeric ID of the lost item
- `found_item_id` (required): Numeric ID of the found item

**Authentication:** Required (JWT token)

**Validation:**
- Both items must exist in the database
- Items must be of the same type (card/item)
- Returns error if no valid match exists between the items

**Response:**
```json
{
  "lost_item": {
    "id": 1,
    "tracking_id": "LI-A1B2C3D4",
    "type": "item",
    "item_name": "iPhone 12",
    "description": "Black iPhone with blue case",
    "card_last_four": null,
    "place_lost": "Tennis Court",
    "owner_name": "John Doe",
    "reporter_email": "john@example.com",
    "reporter_phone": "+254712345678",
    "reporter_member_id": "PSC001",
    "status": "pending",
    "photo": "/media/lost_items/photos/photo.jpg",
    "date_reported": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-15T10:30:00Z",
    "reported_by": 1
  },
  "found_item": {
    "id": 2,
    "type": "item",
    "item_name": "iPhone 12 Black",
    "description": "Black iPhone found on tennis court",
    "card_last_four": null,
    "place_found": "Tennis Court",
    "finder_name": "Jane Smith",
    "finder_phone": "+254712345679",
    "status": "found",
    "photo": "/media/found_items/photos/found_phone.jpg",
    "date_reported": "2024-01-15T11:00:00Z",
    "last_updated": "2024-01-15T11:00:00Z",
    "reported_by": 2
  },
  "match_score": 85.5,
  "match_reasons": [
    "Matching type: item",
    "Similar item names (85% match)",
    "Similar descriptions (72% match)",
    "Same location",
    "Reported within 2 hours of each other"
  ]
}
```

**Response Fields:**
- `lost_item`: Complete lost item object with all fields
- `found_item`: Complete found item object with all fields
- `match_score`: Similarity score as percentage (0-100)
- `match_reasons`: Detailed array of reasons why items match

**Match Reasons Categories:**
- **Type matching**: Confirms both items are same type
- **Name similarity**: Fuzzy matching percentage for item names
- **Description similarity**: Content similarity analysis
- **Location matching**: Geographic proximity or exact location match
- **Time proximity**: How recently items were reported relative to each other

**Error Responses:**
- `400 Bad Request`: Missing required parameters or invalid item combination
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: One or both item IDs don't exist

### 2.11 Print Match Receipt
**Endpoint:** `POST /found/print_match/`

**Description:** Print physical match receipts (chits) for potential matches. This endpoint finds matches for a given tracking ID and sends them to the thermal printer for physical distribution.

**Query Parameters:**
- `tracking_id` (required): Can be either:
  - Lost item tracking ID (format: `LI-XXXXXXX`)
  - Found item numeric ID

**Authentication:** Required (JWT token)

**Processing Logic:**
1. **Lost Item Tracking ID**: Finds all potential matches for that lost item against available found items
2. **Found Item ID**: Finds all potential matches for that found item against all lost items
3. **Filtering**: Only considers items with status='found' for matching
4. **Printing**: Sends each match to thermal printer with formatted receipt

**Printer Integration:**
- Uses ESC/POS thermal printer commands
- Prints formatted match receipts with QR codes
- Includes item details, match scores, and contact information

**Response:**
```json
{
  "status": "success",
  "acknowledgment": "3 match chit(s) printed for tracking_id=LI-A1B2C3D4",
  "matches": [
    {
      "lost_item": {
        "id": 1,
        "tracking_id": "LI-A1B2C3D4",
        "type": "item",
        "item_name": "iPhone 12",
        "description": "Black iPhone with blue case",
        "place_lost": "Tennis Court",
        "owner_name": "John Doe",
        "reporter_email": "john@example.com",
        "status": "pending",
        "date_reported": "2024-01-15T10:30:00Z"
      },
      "found_item": {
        "id": 2,
        "type": "item",
        "item_name": "iPhone 12 Black",
        "description": "Black iPhone found on tennis court",
        "place_found": "Tennis Court",
        "finder_name": "Jane Smith",
        "status": "found",
        "date_reported": "2024-01-15T11:00:00Z"
      },
      "match_score": 85.5,
      "match_reasons": [
        "Matching type: item",
        "Similar item names (85% match)",
        "Same location",
        "Reported within 2 hours of each other"
      ]
    }
  ]
}
```

**Response Fields:**
- `status`: Operation status ("success" or "error")
- `acknowledgment`: Human-readable summary of printed chits
- `matches`: Array of match objects (same format as generate_matches)

**Error Responses:**
- `400 Bad Request`: Missing tracking_id or invalid format
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Tracking ID not found
- `500 Internal Server Error`: Printer communication failure

**Printer Requirements:**
- Network-connected thermal printer
- ESC/POS command support
- Configurable IP address and port in PackagePrinter class

## API Usage Examples

### Generate Matches for All Items
```bash
GET /api/items/found/generate_matches/
Authorization: Bearer <your_jwt_token>
```

### Generate Matches for Specific Lost Item
```bash
GET /api/items/found/generate_matches/?tracking_id=LI-A1B2C3D4
Authorization: Bearer <your_jwt_token>
```

### Get Detailed Match Information
```bash
GET /api/items/found/match_details/?lost_item_id=1&found_item_id=2
Authorization: Bearer <your_jwt_token>
```

### Print Match Receipts
```bash
POST /api/items/found/print_match/?tracking_id=LI-A1B2C3D4
Authorization: Bearer <your_jwt_token>
```

## Best Practices

### Match Generation
1. **Use Specific Tracking IDs**: When possible, filter by tracking_id to reduce processing time
2. **Cache Results**: Consider caching match results for frequently accessed items
3. **Batch Processing**: For bulk operations, process items in smaller batches

### Match Details
1. **Validate Item IDs**: Always check that both items exist before requesting details
2. **Handle No Matches**: Implement proper error handling for cases with no valid matches
3. **Performance**: Match details endpoint is faster than generate_matches for specific pairs

### Printing
1. **Network Reliability**: Ensure printer network connectivity before calling print endpoints
2. **Error Handling**: Implement retry logic for printer communication failures
3. **Status Verification**: Check printer status before sending large batches

### Rate Limiting
- **Authentication Required**: All match endpoints require valid JWT tokens
- **Request Limits**: Respect API rate limits (1000 requests/hour for authenticated users)
- **Error Handling**: Implement exponential backoff for rate-limited requests

### Data Validation
- **Input Sanitization**: Always validate tracking_id formats before sending requests
- **Type Checking**: Ensure item IDs are numeric when required
- **Status Validation**: Verify item availability status before match operations

---

## 3. Pickup Logs Endpoints

### 3.1 List/Create Pickup Logs
**Endpoint:** `GET/POST /pickuplogs/`

#### GET - List Pickup Logs
**Query Parameters:**
- `search` (optional): Search by name, member ID, item name
- `time_frame` (optional): `today`, `week`, `month`

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "item": 1,
      "picked_by_member_id": "PSC001",
      "picked_by_name": "John Doe",
      "picked_by_phone": "+254712345678",
      "pickup_date": "2024-01-16T14:30:00Z"
    }
  ]
}
```

#### POST - Create Pickup Log
**Request Body:**
```json
{
  "item": 1,
  "picked_by_member_id": "PSC001",
  "picked_by_name": "John Doe",
  "picked_by_phone": "+254712345678"
}
```

### 3.2 Retrieve/Update/Delete Pickup Log
**Endpoint:** `GET/PUT/PATCH/DELETE /pickuplogs/{id}/`

### 3.3 Pickup History
**Endpoint:** `GET /pickuplogs/pickuphistory/`

**Query Parameters:**
- `limit` (optional): Number of records (default: 20, max: 100)

**Response:**
```json
[
  {
    "pickup_details": {...},
    "item_details": {...},
    "pickup_date": "2024-01-16T14:30:00Z",
    "verified_by": "Admin User"
  }
]
```

---

## 4. System Settings Endpoints

### 4.1 List/Create System Settings
**Endpoint:** `GET/POST /settings/`

#### GET - List System Settings
**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "key": "lost_match_threshold",
      "value": "0.6",
      "description": "Similarity threshold for lost item matches",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### POST - Create System Setting
**Request Body:**
```json
{
  "key": "new_setting",
  "value": "setting_value",
  "description": "Description of the setting"
}
```

### 4.2 Retrieve/Update/Delete System Setting
**Endpoint:** `GET/PUT/PATCH/DELETE /settings/{id}/`

### 4.3 Get Specific Setting
**Endpoint:** `GET /settings/get_setting/`

**Query Parameters:**
- `key`: Setting key

**Response:**
```json
{
  "key": "lost_match_threshold",
  "value": "0.6"
}
```

### 4.4 Set Specific Setting
**Endpoint:** `POST /settings/set_setting/`

**Request Body:**
```json
{
  "key": "lost_match_threshold",
  "value": "0.7",
  "description": "Updated similarity threshold"
}
```

**Response:**
```json
{
  "id": 1,
  "key": "lost_match_threshold",
  "value": "0.7",
  "description": "Updated similarity threshold",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

## 5. System Settings Endpoints

### 5.1 List/Create System Settings
**Endpoint:** `GET/POST /settings/`

#### GET - List System Settings
**Response:**
```json
{
  "count": 11,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "key": "lost_match_threshold",
      "value": "0.6",
      "description": "Similarity threshold for lost item matches (0.0-1.0)",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### POST - Create System Setting
**Request Body:**
```json
{
  "key": "new_setting",
  "value": "setting_value",
  "description": "Description of the setting"
}
```

### 5.2 Retrieve/Update/Delete System Setting
**Endpoint:** `GET/PUT/PATCH/DELETE /settings/{id}/`

### 5.3 Get Specific Setting
**Endpoint:** `GET /settings/get_setting/`

**Query Parameters:**
- `key`: Setting key

**Response:**
```json
{
  "key": "lost_match_threshold",
  "value": "0.6"
}
```

### 5.4 Set Specific Setting
**Endpoint:** `POST /settings/set_setting/`

**Request Body:**
```json
{
  "key": "lost_match_threshold",
  "value": "0.7",
  "description": "Updated similarity threshold"
}
```

**Response:**
```json
{
  "id": 1,
  "key": "lost_match_threshold",
  "value": "0.7",
  "description": "Updated similarity threshold",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

## 6. Bulk Email Endpoints

### 5.1 Send Bulk Email
**Endpoint:** `POST /lost/send_bulk_email/`

**Request Body:**
```json
{
  "recipients": ["user1@example.com", "user2@example.com"],
  "subject": "Lost and Found Update",
  "message": "Important update regarding lost items..."
}
```

**Response:**
```json
{
  "message": "Email sent to 2 recipients"
}
```

---

## 7. Statistics and Reports Endpoints

### 6.1 Weekly Report
**Endpoint:** `GET /pickuplogs/weekly_report/`

**Query Parameters:**
- `weeks` (optional): Number of weeks back (default: 4)

**Response:**
```json
{
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-29T23:59:59Z",
  "lost_items_total": 25,
  "lost_items_by_type": [
    {"type": "item", "count": 20},
    {"type": "card", "count": 5}
  ],
  "found_items_total": 18,
  "found_items_by_type": [
    {"type": "item", "count": 15},
    {"type": "card", "count": 3}
  ],
  "claimed_items_count": 12,
  "claim_rate": 0.667,
  "lost_items_daily": [...],
  "found_items_daily": [...]
}
```

### 6.2 Item Statistics
**Endpoint:** `GET /stats/`

**Response:**
```json
{
  "lost": {
    "total": 25,
    "pending": 10,
    "recent": 5
  },
  "found": {
    "total": 18,
    "unclaimed": 6,
    "claimed": 12,
    "recent": 3
  },
  "pickups": {
    "total": 12,
    "recent": 2
  },
  "weekly_trends": {...}
}
```

---

## 9. System Settings Keys

The following settings can be configured:

| Key | Default | Description |
|-----|---------|-------------|
| `lost_match_threshold` | 0.4 | Similarity threshold for lost item matches (0.0-1.0) - Lower for better matching |
| `found_match_threshold` | 0.35 | Similarity threshold for found item matches (0.0-1.0) - Lower for better matching |
| `match_days_back` | 14 | Number of days to look back for potential matches - Extended window |
| `task_match_threshold` | 0.5 | Similarity threshold for background task matches (0.0-1.0) |
| `task_match_days_back` | 14 | Number of days back for background matching tasks - Extended window |
| `generate_match_threshold` | 0.3 | Similarity threshold for manual match generation (0.0-1.0) - Lower for comprehensive results |
| `print_match_threshold` | 0.4 | Similarity threshold for printing match receipts (0.0-1.0) |
| `auto_print_lost_receipt` | true | Automatically print receipts when lost items are reported (true/false) |
| `auto_print_found_receipt` | true | Automatically print receipts when found items are reported (true/false) |
| `email_notifications_enabled` | true | Enable email notifications for matches (true/false) |
| `max_image_size_mb` | 5 | Maximum image file size in MB for uploads |
| `acknowledgment_email_subject` | Lost Item Report Confirmation - Parklands Sports Club | Subject line for lost item acknowledgment emails |
| `acknowledgment_email_template` | [Template text] | Template for lost item acknowledgment emails (supports placeholders) |
| `match_notification_email_subject` | Potential Match Found - Parklands Sports Club | Subject line for match notification emails |
| `match_notification_email_template` | [Template text] | Template for match notification emails (supports placeholders) |
| `max_auto_emails_per_day` | 50 | Maximum number of auto-sent emails per day |
| `max_auto_emails_per_item` | 3 | Maximum number of auto-sent emails per lost item |
| `task_match_threshold` | 0.7 | Threshold for background task matches |
| `task_match_days_back` | 7 | Days back for background matching |
| `generate_match_threshold` | 0.5 | Threshold for manual match generation |
| `print_match_threshold` | 0.5 | Threshold for printing match receipts |
| `auto_print_lost_receipt` | true | Auto-print receipts for lost items |

## Matching Algorithm Details

### Overview
The Lost and Found system uses an intelligent matching algorithm to identify potential matches between lost and found items. The algorithm combines multiple similarity metrics with configurable weights to produce a comprehensive match score.

### Scoring Components

#### **For Regular Items (Phones, Keys, etc.):**

**1. Type Matching (30% weight)**
- **Purpose**: Ensures only same-type items are matched
- **Score**: 0.3 if types match, 0.0 if different
- **Rationale**: Cards can only match cards, items can only match items

**2. Enhanced Name Similarity (25% weight)**
- **Method**: Combined direct similarity + keyword matching
- **Score Range**: 0.0 to 0.25
- **Features**:
  - Direct string similarity using SequenceMatcher
  - Keyword overlap analysis
  - Case-insensitive matching
- **Example**: "iPhone 12" vs "iPhone 12 Pro" gets high similarity

**3. Enhanced Description Similarity (20% weight)**
- **Method**: SequenceMatcher + color keyword extraction
- **Score Range**: 0.0 to 0.2
- **Features**:
  - Text similarity analysis
  - Color keyword matching (black, white, red, blue, etc.)
  - Safe handling of None/empty values

**4. Enhanced Location Similarity (15% weight)**
- **Method**: SequenceMatcher + location keyword matching
- **Score Range**: 0.0 to 0.15
- **Features**:
  - Direct location text similarity
  - Location context keywords (tennis, court, gym, pool, etc.)
  - Geographic proximity indication

**5. Extended Time Proximity (10% weight)**
- **Method**: Extended exponential decay over 14 days
- **Formula**: `max(0, 1 - (time_diff_hours / 336)) * 0.1`
- **Purpose**: Items reported within 2 weeks can still match well

#### **For Card Items (Specialized Algorithm):**

**1. Type Matching (20% weight)**
- **Purpose**: Ensures both items are cards
- **Score**: 0.2 if both are cards

**2. Card Number Matching (60% weight for exact, 40% for partial)**
- **Method**: Exact string comparison + similarity analysis
- **Most Important Factor**: Cards must have matching or very similar last 4 digits
- **Examples**:
  - "K123D" = "K123D" → 100% match (exact)
  - "K123D" = "K123E" → ~80% match (very similar)
  - "K123D" = "0000" → Very low match (completely different)

**3. Location Similarity (10% weight)**
- **Method**: Text similarity for card locations
- **Less Important**: Cards are more about the number than location

**4. Time Proximity (7% weight)**
- **Method**: Shorter 7-day window for cards
- **Purpose**: Cards should be claimed quickly when found

**Card Matching Logic:**
- **Exact Match**: Same card number = high confidence match
- **Partial Match**: Similar numbers (e.g., off-by-one digit) = medium confidence
- **No Match**: Completely different numbers = very low score
- **Missing Data**: Cards without numbers get very low scores

### Total Score Calculation
```
total_score = type_score + name_score + desc_score + location_score + time_score
```

### Configuration Settings
- `lost_match_threshold`: Threshold for automatic lost item matching (default: 0.6)
- `found_match_threshold`: Threshold for automatic found item matching (default: 0.5)
- `generate_match_threshold`: Threshold for manual match generation (default: 0.5)
- `print_match_threshold`: Threshold for printing match receipts (default: 0.5)
- `match_days_back`: Number of days to look back for matches (default: 7)

### Match Reasons Generation
The system generates human-readable explanations for each match:
- "Matching type: [type]"
- "Similar item names ([percentage]% match)"
- "Similar descriptions ([percentage]% match)"
- "Same location"
- "Reported within [X] hour(s)/day(s) of each other"

### Performance Considerations
- **Database Queries**: Optimized with select_related for foreign keys
- **Algorithm Complexity**: O(n*m) where n=lost items, m=found items
- **Memory Usage**: Minimal - processes items in batches
- **Response Time**: Typically <2 seconds for moderate datasets

### Threshold Recommendations

#### **For Regular Items:**
- **High Confidence (0.7+)**: Excellent matches with multiple strong indicators
- **Medium Confidence (0.5-0.7)**: Good similarity across several factors
- **Low Confidence (0.3-0.5)**: Basic similarity, may need manual verification
- **Potential Match (0.2-0.3)**: Weak similarity, requires careful review
- **No Match (<0.2)**: Insufficient similarity for consideration

#### **For Card Items:**
- **Exact Match (0.8+)**: Same card number - very high confidence
- **Strong Match (0.6-0.8)**: Very similar card numbers (e.g., K123D vs K123E)
- **Partial Match (0.4-0.6)**: Somewhat similar card numbers
- **Weak Match (0.2-0.4)**: Cards with some number similarity but different
- **No Match (<0.2)**: Completely different card numbers or missing data

### Algorithm Improvements
- **Better Missing Data Handling**: Gracefully handles incomplete item information
- **Keyword-Based Matching**: Extracts and matches important keywords from names and descriptions
- **Color Recognition**: Identifies and matches color descriptions
- **Location Context**: Recognizes location-specific keywords
- **Extended Time Window**: 14-day window instead of 7 days for better matching
- **Normalized Scoring**: Accounts for available data to prevent unfairly low scores

## Email Template Placeholders

The email templates support the following placeholders that will be automatically replaced:

### Acknowledgment Email Placeholders:
- `{owner_name}` - Name of the person who reported the lost item
- `{tracking_id}` - Unique tracking ID for the lost item
- `{item_name}` - Name of the lost item
- `{description}` - Description of the lost item
- `{place_lost}` - Location where the item was lost
- `{reporter_member_id}` - Member ID of the reporter
- `{reporter_phone}` - Phone number of the reporter
- `{reporter_email}` - Email address of the reporter

### Match Notification Email Placeholders:
- `{owner_name}` - Name of the person who reported the lost item
- `{match_count}` - Number of potential matches found
- `{tracking_id}` - Unique tracking ID for the lost item
- `{match_details}` - Detailed list of matches with scores and reasons

## Email Rate Limiting

The system implements rate limiting to prevent email spam:

- **Daily Limit**: Maximum emails per day (default: 50)
- **Per-Item Limit**: Maximum emails per lost item (default: 3)
- **Email Logging**: All sent emails are logged for auditing

If limits are exceeded, emails will not be sent and the system will log the attempt.

---

## 10. Validation Rules

### Card Last Four Validation
When reporting a card type item, the `card_last_four` field must follow this format:
- Must start with a letter (A-Z)
- Followed by exactly 4 digits (0-9)
- Optional ending letter (A-Z)

**Valid Examples:**
- `A1234`
- `A1234B`
- `B5678`
- `B5678C`

**Invalid Examples:**
- `1234` (doesn't start with letter)
- `ABCD` (no digits)
- `A123` (less than 4 digits)
- `A12345` (more than 4 digits)

### Required Fields
- For `type: "card"`: `card_last_four` is required
- For `type: "item"`: `item_name` is required

## 11. Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Description of the validation error"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## 12. File Upload

For image uploads, use `multipart/form-data` with the field name `photo`:

```
Content-Type: multipart/form-data
Body:
photo: <image_file>
type: item
item_name: iPhone 12
...
```

Supported image formats: JPG, PNG, JPEG
Maximum file size: Configurable (default: Django settings)

---

## 13. Rate Limiting

- API endpoints are rate-limited to prevent abuse
- Authenticated users: 1000 requests/hour
- Anonymous users: 100 requests/hour

---

## 14. Webhooks (Future Enhancement)

The system supports webhooks for real-time notifications:
- Item reported
- Match found
- Item claimed
- Email sent

Contact system administrator to configure webhooks.