# CommunityConnectAPI

## 1. Project Overview
CommunityConnect is a robust citizen reporting platform built to bridge the gap between residents and local authorities. It allows users to report community issues (like infrastructure damage or environmental concerns), attach supporting documentation, and track the resolution process in real-time.

**Key Features:**
*   **Role-Based Access:** Distinct workflows for Citizens, Staff, and Administrators.
*   **Secure File Handling:** Integrated malware scanning via ClamAV and automated OCR for documents.
*   **Efficient Storage:** Implementation of SHA-256 deduplication and Perceptual Hashing (pHash) for images.
*   **Asynchronous Processing:** Heavy tasks like virus scanning and text extraction are handled in the background.
*   **API-First Design:** Fully documented RESTful API using OpenAPI/Swagger.

## 2. Architecture Explanation
The system leverages a containerized microservices architecture to ensure scalability and isolation of concerns.

*   **Web Tier (Django & Gunicorn):** Handles the core business logic and provides the REST API.
*   **Worker Tier (Celery):** Manages background tasks. It interfaces with Tesseract for OCR and ClamAV for security scans.
*   **Data Tier (PostgreSQL):** Stores relational data, including user roles, report metadata, and file hashes.
*   **Messaging/Caching (Redis):** Acts as the message broker for Celery and handles transient data.
*   **Security Service (ClamAV):** A dedicated container running the ClamAV daemon for real-time virus definitions and scanning.
*   **Deployment (Docker):** The entire stack is orchestrated via Docker Compose, ensuring "it works on my machine" consistency.

## 3. Setup Instructions

### Prerequisites
*   Docker and Docker Compose
*   A `.env` file in the root directory

### Installation Steps

1.  **Configure Environment:**
    Create a `.env` file based on the following template:
    ```env
    DEBUG=True
    SECRET_KEY=your-secret-key
    ALLOWED_HOSTS=localhost,127.0.0.1
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_HOST=db
    DB_PORT=5432
    ```

2.  **Build and Start:**
    Use Docker Compose to build the images (utilizing the `uv` package manager for fast builds) and start the services:
    ```bash
    docker-compose up --build
    ```

3.  **Initialize Database:**
    The `entrypoint.sh` script automatically handles migrations and static file collection. To create an initial admin user, run:
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

4.  **Access the Platform:**
    *   Web API: `http://localhost:8000/`
    *   Admin Interface: `http://localhost:8000/admin/`

## 4. API Documentation
The API is self-documenting. Once the server is running, you can access the interactive documentation at:

*   **Swagger UI:** `http://localhost:8000/`
*   **Redoc:** `http://localhost:8000/api/redoc/`

### Core Endpoints
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/users/token/` | POST | Obtain JWT access/refresh tokens. |
| `/api/v1/reports/` | GET/POST | List or create incident reports. |
| `/api/v1/reports/{id}/` | GET/PUT/DELETE | Manage specific reports. |

**Note on Security:** Access to files is restricted based on their `processing_status`. The `AttachmentSerializer` will return `null` for the file URL until the ClamAV scan confirms the file is `CLEAN`.

## 5. Key Design Decisions

### 5.1 Fast Dependency Management
We use **Astral's `uv`** inside the `Dockerfile` instead of standard `pip`. This significantly reduces build times and provides deterministic environment resolution via `uv.lock`.

### 5.2 Security-First File Pipeline
To protect the system and its users:
*   **Sandboxed Scanning:** Files are scanned by a dedicated ClamAV service before being made available for download.
*   **Quarantine Logic:** Any file flagged as malicious is automatically moved to a `QUARANTINE_ROOT` directory outside the public media path, and the database record is updated to prevent access.

### 5.3 Intelligent Storage (Deduplication)
To optimize disk usage, the `AttachmentService` performs two types of checks:
1.  **Exact Match:** Uses SHA-256 hashing to identify identical files. If a file already exists, the database points to the existing file on disk rather than saving a duplicate.
2.  **Near-Duplicate Detection:** Uses Perceptual Hashing (pHash) for images to identify cases where the same image was uploaded with different resolutions or minor edits.

### 5.4 Performance Optimization
*   **Query Optimization:** The `ReportViewSet` uses `prefetch_related('attachments')` to solve the N+1 query problem, ensuring that report lists with many attachments load efficiently.
*   **Background Processing:** OCR (Tesseract) and PDF processing (poppler-utils) are isolated in Celery tasks to ensure the web request-response cycle remains fast.

### 5.5 Custom Permissions
We implemented specialized permission classes (`IsOwnerOrStaff`, `IsAdminRole`) to ensure that:
*   **Citizens** can only see and modify their own reports.
*   **Staff** can view and manage all reports within the system.
*   **Admins** have full system-wide access.

---