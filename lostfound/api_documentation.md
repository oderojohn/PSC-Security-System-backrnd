# Lost and Found System API Documentation

## Overview
This API provides comprehensive functionality for managing lost and found items at Parklands Sports Club. It supports reporting lost items with images, reporting found items, automatic matching with configurable thresholds, email notifications, receipt printing, system settings management, and comprehensive reporting.

## Recent Updates (v2.0)
- ✅ **Image Upload Support**: Lost items now accept photo uploads
- ✅ **Configurable System Settings**: Adjustable match thresholds and system parameters
- ✅ **Auto-Printing**: Automatic receipt printing for lost/found items
- ✅ **Enhanced Email System**: Bulk email communications and individual notifications
- ✅ **Advanced Reporting**: CSV/PDF exports for all item types
- ✅ **Production Ready**: Security validations, logging, and performance optimizations

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
  "matches": [
    {
      "lost_item": {
        "id": 1,
        "tracking_id": "LI-A1B2C3D4",
        "item_name": "iPhone 12"
      },
      "found_item": {
        "id": 2,
        "item_name": "iPhone 12 Black",
        "place_found": "Tennis Court"
      },
      "match_score": 85.5,
      "match_reasons": [
        "Similar item names (85% match)",
        "Same location",
        "Reported within 2 hours of each other"
      ]
    }
  ],
  "acknowledgment": "Match notification sent to john@example.com"
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
      "card_last_four": null,
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
  "matches": [
    {
      "lost_item": {...},
      "found_item": {...},
      "match_score": 85.5,
      "match_reasons": ["Similar item names", "Same location"]
    }
  ],
  "acknowledgment": "Match notification sent to john@example.com"
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

**Query Parameters:**
- `tracking_id` (optional): Filter by tracking ID

**Response:**
```json
{
  "matches": [
    {
      "lost_item": {
        "id": 1,
        "tracking_id": "LI-A1B2C3D4",
        "item_name": "iPhone 12"
      },
      "found_item": {
        "id": 2,
        "item_name": "iPhone 12 Black",
        "place_found": "Tennis Court"
      },
      "match_score": 85.5,
      "match_reasons": [
        "Similar item names (85% match)",
        "Same location",
        "Reported within 2 hours of each other"
      ]
    }
  ]
}
```

### 2.10 Print Match Receipt
**Endpoint:** `POST /found/print_match/`

**Query Parameters:**
- `tracking_id`: Lost item tracking ID or Found item ID

**Response:**
```json
{
  "status": "success",
  "acknowledgment": "3 match chit(s) printed for tracking_id=LI-A1B2C3D4",
  "matches": [...]
}
```

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
| `lost_match_threshold` | 0.6 | Similarity threshold for lost item matches (0.0-1.0) |
| `found_match_threshold` | 0.5 | Similarity threshold for found item matches (0.0-1.0) |
| `match_days_back` | 7 | Number of days to look back for potential matches |
| `task_match_threshold` | 0.7 | Similarity threshold for background task matches (0.0-1.0) |
| `task_match_days_back` | 7 | Number of days back for background matching tasks |
| `generate_match_threshold` | 0.5 | Similarity threshold for manual match generation (0.0-1.0) |
| `print_match_threshold` | 0.5 | Similarity threshold for printing match receipts (0.0-1.0) |
| `auto_print_lost_receipt` | true | Automatically print receipts when lost items are reported (true/false) |
| `auto_print_found_receipt` | true | Automatically print receipts when found items are reported (true/false) |
| `email_notifications_enabled` | true | Enable email notifications for matches (true/false) |
| `max_image_size_mb` | 5 | Maximum image file size in MB for uploads |
| `task_match_threshold` | 0.7 | Threshold for background task matches |
| `task_match_days_back` | 7 | Days back for background matching |
| `generate_match_threshold` | 0.5 | Threshold for manual match generation |
| `print_match_threshold` | 0.5 | Threshold for printing match receipts |
| `auto_print_lost_receipt` | true | Auto-print receipts for lost items |

---

## 10. Error Responses

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

## 11. File Upload

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

## 12. Rate Limiting

- API endpoints are rate-limited to prevent abuse
- Authenticated users: 1000 requests/hour
- Anonymous users: 100 requests/hour

---

## 13. Webhooks (Future Enhancement)

The system supports webhooks for real-time notifications:
- Item reported
- Match found
- Item claimed
- Email sent

Contact system administrator to configure webhooks.