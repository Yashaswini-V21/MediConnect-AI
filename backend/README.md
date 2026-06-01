# ⚙️ MediConnect-AI: Python Flask Backend API Server

This folder contains the robust, production-grade Flask backend REST API server for the MediConnect-AI platform. It handles symptom analysis, hospital matching, patient-doctor bookings, advanced administrative RBAC, real-time Socket.IO communication, and secure clinical data encryption.

---

## 🛠️ Technology Stack & Core Engines

* **Framework**: Flask (Python 3.10+)
* **Database**: SQLite (local development) or PostgreSQL (production) with SQLAlchemy ORM
* **Realtime Services**: Socket.IO for push notifications and live occupancy monitoring
* **Machine Learning**: Custom symptom-to-specialty urgency classifier utilizing `scikit-learn` and TF-IDF vectors
* **AI Assistance**: Integrations with **Groq LLaMA** for clinic advisory answers, and **Bhashini / Sarvam AI** for seamless regional language translations
* **Security & Cryptography**: AES-256 encryption via cryptography Fernet, deterministic fallback derivation, and custom Role-Based Access Control (RBAC) middleware

---

## 📂 Backend Architecture

```
backend/
├── models/                     # Data Models & ML Artifacts
│   ├── artifacts/              # Pre-trained ML classifiers
│   ├── admin_model.py          # Hospital and Admin portal tables
│   ├── user_model.py           # Patient profile and search tables
│   ├── ml_classifier.py        # ML Urgency detection trainer
│   └── hospital_matcher.py     # Live department capacity matching
│
├── routes/                     # Blueprint API Endpoints
│   ├── admin_routes.py         # Advanced back-office admin system
│   ├── auth_routes.py          # OTP registration and Profile sync
│   ├── appointment_routes.py   # Booking and hospital review ratings
│   ├── ai_platform_routes.py   # Groq clinical consultation LLaMA
│   ├── hospital_routes.py      # Hospital details and emergency search
│   └── symptom_routes.py       # Basic triage route
│
├── utils/                      # Utilities & Core Services
│   ├── security.py             # AES Encryption, Audit Log & Rate limiting
│   ├── realtime.py             # Socket.IO pub/sub systems
│   ├── analytics.py            # Analytics statistics aggregation
│   └── email_sender.py         # Email OTP sender module stub
│
├── app.py                      # Main Flask application entrypoint
├── extensions.py               # Shared instances (db, socketio)
└── requirements.txt            # Package manifest
```

---

## 🚀 Setup & Launch Instructions

### Prerequisites
Make sure you have **Python 3.10+** installed.

### 1. Installation & Environment Setup
Create a virtual environment, activate it, and install the required modules:
```bash
python -m venv .venv
.venv\Scripts\activate      # On Windows
# source .venv/bin/activate # On Unix/macOS
pip install -r requirements.txt
```

### 2. Configuration Setup
Create a `.env` file in the root directory (based on `.env.example`) and fill in:
* `GROQ_API_KEY`: Required for LLaMA clinical assistant suggestions.
* `ENCRYPTION_KEY`: Run `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and paste the key here to secure health records.
* `ADMIN_SECRET_TOKEN`: Unique token for authorizing back-office administrators.

### 3. Initialize Database & ML Models
Before running, you need to compile/train the local triage ML classifier and initialize the database tables:
```bash
# Train the local symptom urgency classifier
python -c "from models.ml_classifier import train_and_save_model; train_and_save_model()"

# Initialize DB tables
python init_db.py
```

### 4. Running the API Server
Start the development server:
```bash
python app.py
```
The server will boot on [http://localhost:5000](http://localhost:5000) with automatic hot-reloading.

---

## 🛡️ Key Enterprise Safeguards
1. **Zero Bare Excepts**: All backend exception handling incorporates precise logging and standard, uniform JSON error outputs.
2. **Audit Logging**: Any write action regarding appointments, patients, or hospital schedules automatically writes a non-repudiation audit trail in the `audit_logs` table containing timestamp, IP address, user-agent, action description, and success status.
3. **Data Protection**: Patient symptoms and details are automatically encrypted with AES-256 keys, ensuring that even under database breaches, user medical histories remain fully protected.
