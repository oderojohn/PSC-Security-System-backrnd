# API Documentation for myapp

This document provides comprehensive API documentation for the `myapp` Django application, which manages packages, settings, and printing services for a package reception system.

## Overview

The API is built using Django REST Framework and provides endpoints for:
- Package management (CRUD operations)
- Package picking and status updates
- Printing receipts and labels
- Application settings management
- Statistics and reporting
- Package history tracking

## Authentication & Permissions

The API uses custom permission classes:
- `IsAdmin`: Administrative access
- `IsStaff`: Staff-level access
- `IsReception`: Reception desk access

Different endpoints require different permission levels as specified below.

## Base URL

All endpoints are relative to the application's base URL.

## Endpoints

### Packages

#### 1. List Packages
- **Method**: GET
- **URL**: `/packages/`
- **Permissions**: `IsStaff`
- **Description**: Retrieve a list of packages with optional filtering and search
- **Query Parameters**:
  - `status`: Filter by status (`pending`, `picked`)
  - `type`: Filter by package type (`package`, `document`, `keys`)
  - `shelf`: Filter by shelf location
  - `search`: Search across multiple fields (code, description, recipient_name, recipient_phone, dropped_by, picked_by, shelf)
  - `time_range`: Filter picked packages by time (`today`, `week`, `month`)
- **Response**: Array of package objects
- **Example Response**:
```json
[
  {
    "id": 1,
    "code": "A1ABCDE",
    "type": "package",
    "description": "Electronics package",
    "recipient_name": "John Doe",
    "recipient_phone": "0712345678",
    "status": "pending",
    "created_at": "2023-12-01T10:00:00Z",
    "updated_at": "2023-12-01T10:00:00Z",
    "dropped_by": "Courier Service",
    "dropper_phone": "0798765432",
    "picked_by": null,
    "picker_phone": null,
    "picker_id": null,
    "picked_at": null,
    "shelf": "A1",
    "package_type": "Package"
  }
]
```

#### 2. Create Package
- **Method**: POST
- **URL**: `/packages/`
- **Permissions**: `IsAdmin | IsReception | IsStaff`
- **Description**: Create a new package. Automatically generates code and assigns shelf based on recipient name. Optionally prints receipt if auto-print is enabled.
- **Request Body**:
```json
{
  "type": "package",
  "description": "Package description",
  "recipient_name": "John Doe",
  "recipient_phone": "0712345678",
  "dropped_by": "Courier Name",
  "dropper_phone": "0798765432"
}
```
- **Response**: Created package object
- **Notes**:
  - `code`, `shelf`, `created_at`, `updated_at` are read-only and auto-generated
  - Shelf assignment uses first letter of recipient name
  - Triggers automatic printing if `auto_print_on_create` is enabled in settings

#### 3. Retrieve Package
- **Method**: GET
- **URL**: `/packages/{id}/`
- **Permissions**: `IsStaff`
- **Description**: Get details of a specific package
- **Response**: Single package object

#### 4. Update Package
- **Method**: PUT/PATCH
- **URL**: `/packages/{id}/`
- **Permissions**: `IsAdmin | IsReception | IsStaff`
- **Description**: Update package information
- **Request Body**: Partial or full package data (same as create)
- **Response**: Updated package object

#### 5. Delete Package
- **Method**: DELETE
- **URL**: `/packages/{id}/`
- **Permissions**: `IsAdmin | IsReception | IsStaff`
- **Description**: Delete a package
- **Response**: 204 No Content

#### 6. Pick Package
- **Method**: POST
- **URL**: `/packages/{id}/pick/`
- **Permissions**: `IsStaff | IsReception`
- **Description**: Mark a package as picked by a recipient
- **Request Body**:
```json
{
  "picked_by": "John Doe",
  "picker_phone": "0712345678",
  "picker_id": "ID123456"
}
```
- **Response**: Updated package object with `status: "picked"`
- **Notes**:
  - Sets `picked_at` timestamp
  - Clears shelf assignment (except for keys)
  - Creates history entry

#### 7. Reprint Package Receipt
- **Method**: POST
- **URL**: `/packages/{id}/reprint/`
- **Permissions**: `IsAdmin | IsReception | IsStaff`
- **Description**: Reprint the package receipt/label
- **Response**:
```json
{
  "message": "Package receipt reprinted successfully"
}
```
- **Notes**:
  - Requires `enable_reprint` to be true in settings
  - Limited by `max_reprint_attempts`
  - Creates history entry

#### 8. Get Package History
- **Method**: GET
- **URL**: `/packages/{id}/history/`
- **Permissions**: `IsStaff`
- **Description**: Get the history of actions performed on a package
- **Response**:
```json
[
  {
    "action": "created",
    "old_status": null,
    "new_status": "pending",
    "performed_by": "System",
    "notes": "Package created by Courier Service",
    "timestamp": "2023-12-01T10:00:00Z"
  },
  {
    "action": "picked",
    "old_status": "pending",
    "new_status": "picked",
    "performed_by": "John Doe",
    "notes": "Picked by John Doe with ID ID123456",
    "timestamp": "2023-12-01T14:30:00Z"
  }
]
```

#### 9. Get Package Statistics
- **Method**: GET
- **URL**: `/packages/stats/`
- **Permissions**: `IsStaff`
- **Description**: Get overall package statistics
- **Response**:
```json
{
  "pending": 15,
  "picked": 45,
  "total": 60,
  "shelves_occupied": 12
}
```

#### 10. Export Packages
- **Method**: GET
- **URL**: `/packages/export/`
- **Permissions**: `IsAdmin | IsStaff`
- **Description**: Export packages data as CSV file
- **Query Parameters**: Same as list endpoint
- **Response**: CSV file download
- **CSV Headers**: Code, Type, Description, Recipient Name, Recipient Phone, Dropped By, Dropper Phone, Picked By, Picker Phone, Shelf, Status, Created At, Updated At

#### 11. Get Package Summary
- **Method**: GET
- **URL**: `/packages/summary/`
- **Permissions**: `IsStaff`
- **Description**: Get daily summary and type distribution
- **Response**:
```json
{
  "daily_summary": [
    {
      "created_at__date": "2023-12-01",
      "total": 10,
      "pending": 8,
      "picked": 2
    }
  ],
  "type_distribution": [
    {
      "type": "package",
      "count": 45
    },
    {
      "type": "document",
      "count": 12
    },
    {
      "type": "keys",
      "count": 3
    }
  ]
}
```

### Application Settings

#### 1. List Settings
- **Method**: GET
- **URL**: `/settings/`
- **Permissions**: `IsAdmin | IsStaff`
- **Description**: Get application settings (singleton instance)
- **Response**:
```json
{
  "id": 1,
  "printer_ip": "192.168.10.173",
  "printer_port": 9100,
  "enable_qr_codes": true,
  "default_package_type": "package",
  "auto_print_on_create": true,
  "enable_reprint": true,
  "max_reprint_attempts": 3,
  "notification_email": null,
  "enable_sms_notifications": false,
  "sms_api_key": null,
  "created_at": "2023-12-01T09:00:00Z",
  "updated_at": "2023-12-01T09:00:00Z"
}
```

#### 2. Create Settings
- **Method**: POST
- **URL**: `/settings/`
- **Permissions**: `IsAdmin`
- **Description**: Create initial settings (only if none exist)
- **Request Body**: Settings object (all fields optional except printer_ip/port)
- **Response**: Created settings object

#### 3. Update Settings
- **Method**: PUT/PATCH
- **URL**: `/settings/`
- **Permissions**: `IsAdmin`
- **Description**: Update application settings
- **Request Body**: Partial or full settings data
- **Response**: Updated settings object

#### 4. Delete Settings
- **Method**: DELETE
- **URL**: `/settings/`
- **Permissions**: `IsAdmin`
- **Description**: Delete settings (prevents deletion to maintain singleton)
- **Response**: 403 Forbidden (actually prevented in code)

## Data Models

### Package
- `id`: Integer (auto-generated)
- `code`: String (auto-generated, unique)
- `type`: String (choices: 'package', 'document', 'keys')
- `description`: Text
- `recipient_name`: String
- `recipient_phone`: String
- `status`: String (choices: 'pending', 'picked')
- `created_at`: DateTime (auto-generated)
- `updated_at`: DateTime (auto-generated)
- `dropped_by`: String
- `dropper_phone`: String
- `picked_by`: String (nullable)
- `picker_phone`: String (nullable)
- `picker_id`: String (nullable)
- `picked_at`: DateTime (nullable)
- `shelf`: String (auto-assigned, nullable)

### AppSettings (Singleton)
- `id`: Integer (always 1)
- `printer_ip`: String (default: '192.168.10.173')
- `printer_port`: Integer (default: 9100)
- `enable_qr_codes`: Boolean (default: true)
- `default_package_type`: String (default: 'package')
- `auto_print_on_create`: Boolean (default: true)
- `enable_reprint`: Boolean (default: true)
- `max_reprint_attempts`: Integer (default: 3)
- `notification_email`: Email (nullable)
- `enable_sms_notifications`: Boolean (default: false)
- `sms_api_key`: String (nullable)
- `created_at`: DateTime (auto-generated)
- `updated_at`: DateTime (auto-generated)

### PackageHistory
- `id`: Integer (auto-generated)
- `package`: ForeignKey to Package
- `action`: String (e.g., 'created', 'picked', 'reprinted')
- `old_status`: String (nullable)
- `new_status`: String (nullable)
- `performed_by`: String (nullable)
- `notes`: Text (nullable)
- `timestamp`: DateTime (auto-generated)
- `ip_address`: IPAddress (nullable)

## Error Responses

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "error": "Error message description"
}
```

### Validation Errors
```json
{
  "field_name": ["Error message 1", "Error message 2"]
}
```

## Printing Service

The application includes an integrated thermal printer service for generating package receipts and labels.

### Features
- Network thermal printer support
- QR code generation (optional)
- Phone number masking for privacy
- Automatic logo printing
- Multiple text sizes and formatting
- Retry logic for connection failures

### Printer Configuration
Configured through `/settings/` endpoint:
- IP address and port
- QR code enable/disable
- Auto-print on package creation
- Reprint functionality

## Notes

1. **Shelf Assignment**: Packages are automatically assigned to shelves based on the first letter of the recipient's name (A-Z). Each letter has up to 200 available slots.

2. **Code Generation**: Package codes are unique and generated as `{shelf}{5-character random suffix}` (e.g., "A1ABCDE").

3. **Phone Masking**: Phone numbers are automatically masked in printed receipts (e.g., "0712******78").

4. **Singleton Settings**: AppSettings is a singleton model - only one instance can exist.

5. **History Tracking**: All package actions (create, pick, reprint) are logged in PackageHistory.

6. **Permissions**: Ensure proper user roles are assigned for different operations.

7. **Printing**: Requires network-accessible thermal printer with ESC/POS protocol support.

## Rate Limiting

No explicit rate limiting is implemented in the current version.

## Versioning

API versioning is not currently implemented. All endpoints are at the root level.