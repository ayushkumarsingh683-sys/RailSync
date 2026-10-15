# 🚆 RailSync - High-Concurrency Railway Reservation System

RailSync is a robust, production-grade railway reservation backend and interactive web dashboard designed to handle high-traffic ticket bookings. It solves one of the most critical challenges in transit systems: **preventing race conditions and double-bookings during peak hours**.

---

## 🏗️ System Architecture

The application follows a decoupled client-server architecture, communicating via RESTful APIs with strict transaction management to ensure thread safety.

```text
  [ Frontend Dashboard ]          [ FastAPI Backend ]         [ Local SQLite DB ]
  (HTML5 / JS / Tailwind)  --HTTP-->  (Uvicorn Server)  --SQL-->  (Row-Level Locks / 
      Interactive Matrix         CORS Enabled & P2P           Transactions Rollback)
Core Concurrency Flow

    User Request: Multiple users attempt to book the same seat simultaneously via the frontend.

    API Layer: FastAPI processes requests concurrently using asynchronous routes and dependency injection for database sessions.

    Transaction Safety: SQLAlchemy utilizes database-level checks within an atomic transaction.

    Race Condition Prevention: The first request updates the seat status from AVAILABLE to BOOKED and commits. Subsequent concurrent requests for the same seat immediately encounter a 400 Bad Request state, successfully blocking double-booking.

🚀 Key Features

    Bulletproof Concurrency Control: Eliminates race conditions using atomic database commits and state validation.

    Interactive Seat Matrix: Real-time visual seat availability mapping (Coach S1).

    Instant PNR Generation: Unique cryptographic PNR code generation upon successful booking confirmation.

    Automated Seeding: Automatically seeds sample trains, coaches, and seats on the first startup.

    Comprehensive Testing Suite: Includes a dedicated Python script to simulate multi-threaded concurrency attacks.

🧰 Tech Stack

    Backend: Python, FastAPI, Uvicorn, SQLAlchemy

    Database: SQLite (configured with multi-threading support)

    Frontend: HTML5, Modern CSS / Tailwind concepts, Vanilla JavaScript (Fetch API)

    Testing: Python concurrent.futures for multi-threaded race simulation

⚙️ Getting Started & Installation
1. Clone the Repository
Bash

git clone [https://github.com/YOUR_USERNAME/RailSync.git](https://github.com/YOUR_USERNAME/RailSync.git)
cd RailSync

2. Set Up a Virtual Environment & Dependencies
Bash

python -m venv venv
# Activate virtual environment:
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt

3. Run the FastAPI Backend
Bash

uvicorn backend:app --reload

The server will start at http://127.0.0.1:8000 and automatically initialize railsync.db with sample data.
4. Launch the Frontend Dashboard

    Open railsync_dashboard.html in your browser (or use the Live Server extension in VS Code).

🧪 Concurrency Testing

To verify the race-condition protection mechanism under heavy load, run the concurrency test script:
Bash

python test_concurrency.py

Expected Result: Exactly 1 request succeeds (200 OK) while all simultaneous duplicate attempts return 400 Bad Request indicating the seat is already booked.
👤 Author

Ayush Kumar Singh

B.Tech Computer Science & AI | ABES Institute of Technology
