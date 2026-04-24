# 🚛 ELD Trip Planner - Backend API

This is the backend API for the ELD Trip Planner application, designed to automatically plan commercial truck routes while strictly adhering to Federal Motor Carrier Safety Administration (FMCSA) Hours of Service (HOS) regulations.

## 🌐 Live Deployment
- **API Base URL (Railway):** [https://web-production-3e4c.up.railway.app](https://web-production-3e4c.up.railway.app)
- **Primary Endpoint:** `POST /api/trip/plan/`

## 🚀 Core Features

### Advanced HOS Routing Engine (`hos_calculator.py`)
The backend is powered by a custom Python-based routing engine that acts as a deterministic state machine. It enforces FMCSA rules in real-time as it calculates the route:
- **11-Hour Driving Limit:** Enforces daily maximum driving limits.
- **14-Hour Shift Window:** Strictly tracks the 14-hour on-duty window per day. Prevents any driving after 14 hours of total on-duty time (including breaks and fuel stops) without a mandatory 10-hour rest.
- **30-Minute Breaks:** Automatically inserts 30-minute breaks before the driver exceeds 8 hours of continuous driving.
- **70-Hour Cycle Limit & 34-Hour Restarts:** Accurately drains the 70-hour/8-day cycle clock for all on-duty actions and properly invokes the 34-hour restart (off-duty) when the cycle is exhausted.
- **Fuel Stops:** Intelligently schedules 30-minute fuel stops based on vehicle range.

### Geocoding & Routing Integration
Uses OSRM (Open Source Routing Machine) to fetch highly accurate driving distances and turn-by-turn routing instructions to properly segment "Deadhead" (to pickup) and "Loaded" (to dropoff) travel.

## 💻 Technology Stack
- **Framework:** Django & Django REST Framework
- **Language:** Python
- **Database:** SQLite (local)
- **Deployment:** Railway with Gunicorn

## 🛠️ Local Development

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Django development server
python manage.py runserver
```
