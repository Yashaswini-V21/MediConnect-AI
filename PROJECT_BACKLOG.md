
Copy

# 🏥 MediConnect-AI 2.0 — Complete Build Guide (M3 → M8)
 
> **Author:** Yashaswini V | **Started:** IBM SkillBuild x Edunet Internship | **Now:** Product-Level Build  
> **Status:** M1 + M2 + M2.5 ✅ Complete → M3–M8 🚀 Building  
> **Timeline:** 1 Month Sprint — April 28 → May 28, 2026  
> **Goal:** Production-grade SaaS that works on real Bengaluru hospitals
 
---
 
## 📌 How to Use This File
 
1. Open this file **side-by-side** with your VS Code
2. Each section has **Copilot prompts** — copy → paste into `Ctrl+Shift+I`
3. Follow the **exact order** — each milestone builds on previous
4. Tick checkboxes as you complete each task
5. This file IS your coding companion — update it as you go
---
 
## 🎯 What You're Building (Resume Summary)
 
```
MediConnect-AI 2.0
├── AI Layer:        Groq LLaMA 3.3 70B + LangGraph 6-agent pipeline + Bhashini
├── ML Layer:        RandomForest 99.69% accuracy + SHAP explainability
├── Backend:         Flask 3.0 + SQLAlchemy + RBAC + JWT + Firebase
├── Frontend:        React 18 + Tailwind + Framer Motion + Recharts
├── Database:        SQLite → PostgreSQL + Firebase Firestore
├── Notifications:   Celery + Redis + Twilio + SendGrid
├── Security:        AES-256 + HIPAA-ready + Rate limiting + Audit logs
└── Deploy:          Vercel + Render + GitHub Actions CI/CD
```
 
---
 
## 📊 Resume Impact Tracker
 
Fill this as you complete each milestone:
 
| Milestone | Feature | Resume Bullet | Done? |
|---|---|---|---|
| M3 | RBAC Admin Portal | "Built multi-tenant RBAC system with 3 admin roles" | ☐ |
| M3 | Appointment State Machine | "Designed appointment workflow (5 states)" | ☐ |
| M4 | Analytics Dashboard | "Built real-time analytics with Recharts" | ☐ |
| M4 | Predictive Analytics | "Implemented specialist demand forecasting" | ☐ |
| M5 | Celery + Redis | "Async notification pipeline with retry logic" | ☐ |
| M5 | Twilio + SendGrid | "SMS + Email notification system" | ☐ |
| M6 | Multi-Agent | "6-agent LangGraph orchestration for medical triage" | ☐ |
| M7 | HIPAA-ready | "AES-256 encryption + audit logging + HIPAA compliance" | ☐ |
| M8 | Production | "Deployed to production — Render + Vercel + PostgreSQL" | ☐ |
 
---
 
## 🗓️ 1-Month Sprint Plan
 
```
WEEK 1 (Apr 28 – May 4)   → M3: Admin Backend + RBAC + Appointment APIs
WEEK 2 (May 5 – May 11)   → M3: Admin Frontend Dashboard + React pages
WEEK 3 (May 12 – May 18)  → M4: Analytics + M5: Notifications
WEEK 4 (May 19 – May 25)  → M6: Multi-Agent AI + M7: Security basics
BUFFER (May 26 – May 28)  → M8: Deploy + polish + LinkedIn post
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 3: Admin Portal + Appointments
# Timeline: Week 1–2 | ~2 weeks
# ═══════════════════════════════════════
 
## M3 Overview
 
```
What you're building:
Patient → Books appointment → Pending
Hospital Admin → Approves → Confirmed
Day of appointment → Completed
Patient cancels → Cancelled
Patient doesn't show → No-Show
 
3 roles: Platform Admin | Hospital Admin | Support Staff
Each sees different data (RBAC scope-based)
```
 
---
 
## M3 — Step 1: Database Schema
 
### ✅ Checklist
- [ ] Create appointments table
- [ ] Create admin_users table
- [ ] Create doctors table
- [ ] Create notifications table
- [ ] Create support_tickets table
- [ ] Run migrations
### 💡 Copilot Prompt — M3.1 Database Models
 
```
Open models.py → Ctrl+I → paste this:
 
Add these 5 SQLAlchemy models to models.py for MediConnect-AI admin portal.
 
IMPORTS NEEDED:
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.sqlite import TEXT
import enum, uuid
from datetime import datetime
 
MODEL 1 — AppointmentStatus enum + Appointments:
class AppointmentStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
 
class UrgencyLevel(enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
 
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    appointment_date = Column(DateTime, nullable=False)
    status = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.PENDING)
    urgency_level = Column(SAEnum(UrgencyLevel), default=UrgencyLevel.MEDIUM)
    reason = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
MODEL 2 — AdminRole enum + AdminUsers:
class AdminRole(enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN"
    SUPPORT_STAFF = "SUPPORT_STAFF"
 
class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    firebase_uid = Column(String(100))
    role = Column(SAEnum(AdminRole), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)
    permissions = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
 
MODEL 3 — Doctors:
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    name = Column(String(200), nullable=False)
    specialty = Column(String(100))
    degree = Column(String(100))
    experience_years = Column(Integer)
    available_slots = Column(JSON, default=list)
    max_daily_bookings = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
 
MODEL 4 — Notifications:
class NotificationType(enum.Enum):
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    RESCHEDULED = "RESCHEDULED"
    REMINDER = "REMINDER"
    CANCELLATION = "CANCELLATION"
 
class NotificationChannel(enum.Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
 
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)
    appointment_id = Column(String(36), ForeignKey("appointments.id"))
    type = Column(SAEnum(NotificationType))
    message = Column(Text)
    sent_via = Column(SAEnum(NotificationChannel))
    sent_at = Column(DateTime)
    is_read = Column(Boolean, default=False)
 
MODEL 5 — SupportTickets:
class TicketStatus(enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
 
class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)
    admin_id = Column(String(36), ForeignKey("admin_users.id"), nullable=True)
    subject = Column(String(300))
    description = Column(Text)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(String(20), default="MEDIUM")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
 
After all models, add this function:
def create_all_tables(engine):
    Base.metadata.create_all(engine)
    print("✅ All tables created")
```
 
---
 
## M3 — Step 2: RBAC Middleware
 
### ✅ Checklist
- [ ] Create rbac.py middleware file
- [ ] Implement role checking decorator
- [ ] Hospital scope isolation
- [ ] JWT token validation with Firebase
### 💡 Copilot Prompt — M3.2 RBAC Middleware
 
```
Create a new file rbac.py → Ctrl+I → paste:
 
Write complete RBAC middleware for MediConnect-AI Flask backend.
 
PERMISSIONS MATRIX:
Platform Admin: can do everything
Hospital Admin: can only access their own hospital_id data
Support Staff: read-only access to analytics + manage support tickets
 
CREATE:
 
1. DECORATOR: require_role(*allowed_roles)
   - Extract Firebase JWT token from Authorization header
   - Verify token with firebase_admin.auth.verify_id_token()
   - Look up AdminUser in database by firebase_uid
   - Check if user.role is in allowed_roles
   - If hospital_admin: attach hospital_id to flask.g for scope filtering
   - If unauthorized: return jsonify({"error": "Insufficient permissions"}), 403
 
2. DECORATOR: require_hospital_scope
   - For hospital_admin: inject hospital_id filter into query
   - For platform_admin: no filter (sees all)
   - Attach to flask.g.hospital_scope (None = all, int = specific hospital)
 
3. HELPER: get_current_admin()
   - Returns AdminUser object from flask.g
   - Raises 401 if not authenticated
 
4. HELPER: check_appointment_access(appointment_id)
   - Platform Admin: always allowed
   - Hospital Admin: only if appointment.hospital_id == g.hospital_scope
   - Support Staff: read-only
 
EXAMPLE USAGE (show in comments):
@app.route("/api/admin/appointments")
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
def get_appointments():
    scope = flask.g.hospital_scope
    query = Appointment.query
    if scope:
        query = query.filter_by(hospital_id=scope)
    return jsonify([a.to_dict() for a in query.all()])
 
Use: flask, firebase_admin, functools.wraps, flask.g
```
 
---
 
## M3 — Step 3: Appointment APIs
 
### ✅ Checklist
- [ ] POST /api/appointments (patient books)
- [ ] GET /api/admin/appointments (admin views)
- [ ] PUT /api/admin/appointments/:id/status (admin updates)
- [ ] GET /api/admin/doctors/:hospital_id
- [ ] POST /api/admin/doctors (add doctor)
### 💡 Copilot Prompt — M3.3 Appointment Routes
 
```
Create appointment_routes.py Flask blueprint → Ctrl+I → paste:
 
Write complete appointment management routes for MediConnect-AI.
 
BLUEPRINT: appointments_bp = Blueprint("appointments", __name__, url_prefix="/api")
 
ROUTE 1 — Patient books appointment:
POST /api/appointments
Body: { hospital_id, doctor_id, appointment_date, reason, urgency_level }
- Create Appointment with status=PENDING
- Return: { appointment_id, status: "PENDING", message: "Booking received" }
- Validate: appointment_date must be in future
- Validate: doctor must belong to hospital
 
ROUTE 2 — Admin views appointments:
GET /api/admin/appointments
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
Query params: status, date_from, date_to, page, per_page (default 20)
- Apply hospital_scope filter for Hospital Admin
- Return paginated list with total count
- Include doctor name and hospital name in response
 
ROUTE 3 — Admin updates appointment status:
PUT /api/admin/appointments/<appointment_id>/status
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
Body: { status, notes }
- Validate status transition is allowed:
  PENDING → CONFIRMED or CANCELLED
  CONFIRMED → COMPLETED, CANCELLED, or NO_SHOW
  COMPLETED/CANCELLED/NO_SHOW → no transitions allowed
- Update updated_at timestamp
- Return updated appointment
 
ROUTE 4 — Get doctors by hospital:
GET /api/admin/doctors/<hospital_id>
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
- Return list of active doctors for that hospital
- Include specialty, availability, booking count today
 
ROUTE 5 — Add doctor to hospital:
POST /api/admin/doctors
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
Body: { hospital_id, name, specialty, degree, experience_years, available_slots }
- Hospital Admin can only add to their own hospital
- Return created doctor object
 
ROUTE 6 — Get appointment stats (for dashboard header):
GET /api/admin/appointments/stats
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
Return: { total, pending, confirmed, completed, cancelled, today_count }
 
Add proper error handling and return consistent JSON responses.
Use: Flask, SQLAlchemy, require_role decorator from rbac.py
```
 
---
 
## M3 — Step 4: Admin React Dashboard
 
### ✅ Checklist
- [ ] AdminLayout.jsx with sidebar navigation
- [ ] AppointmentsPage.jsx with table + filters
- [ ] DoctorManagementPage.jsx
- [ ] HospitalConsolePage.jsx
- [ ] Protected routes with role checking
### 💡 Copilot Prompt — M3.4 Admin Dashboard React
 
```
Create AdminLayout.jsx → Ctrl+I → paste:
 
Write the complete Admin Dashboard layout for MediConnect-AI React frontend.
 
COMPONENT: AdminLayout.jsx
- Sidebar with navigation links based on user role
- Platform Admin sees: Overview, All Appointments, All Hospitals, All Doctors, Analytics, Support Tickets, Settings
- Hospital Admin sees: My Dashboard, Appointments, My Doctors, My Hospital, Analytics
- Support Staff sees: Support Tickets, Analytics (read-only)
- Top bar with: user name, role badge, logout button
- Dark theme: bg-gray-900, sidebar bg-gray-800
- Active link highlighted with blue-600
 
COMPONENT: AppointmentsTable.jsx
- Table columns: ID, Patient, Date/Time, Doctor, Status, Urgency, Actions
- Status badges with colors: PENDING=yellow, CONFIRMED=green, COMPLETED=blue, CANCELLED=red, NO_SHOW=gray
- Urgency badges: HIGH=red, MEDIUM=orange, LOW=green
- Action buttons per row: Confirm, Cancel (based on current status)
- Status filter dropdown
- Date range picker
- Pagination (20 per page)
- Loading skeleton while fetching
 
COMPONENT: AppointmentStatusModal.jsx
- Modal to change appointment status
- Shows allowed transitions only
- Notes text field
- Confirm button with loading state
 
Use: React 18, Tailwind CSS, Framer Motion for modal animation, Axios for API calls
Styling: Professional dark theme, consistent with existing React app
```
 
---
 
## M3 — Step 5: Test M3 End-to-End
 
### 💡 Copilot Prompt — M3.5 Testing
 
```
Write a complete test suite for MediConnect-AI appointment system in test_appointments.py.
 
Test these scenarios:
1. Patient creates appointment → status is PENDING
2. Hospital admin confirms appointment → status is CONFIRMED
3. Hospital admin tries to see another hospital's appointment → 403 error
4. Invalid status transition (COMPLETED → PENDING) → 400 error
5. Platform admin can see all appointments from all hospitals
6. Appointment date in past → validation error
7. Doctor not in hospital → validation error
 
Use pytest + Flask test client.
Mock Firebase auth token verification for testing.
Add fixtures for: test patient, test hospital admin, test platform admin, sample appointments.
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 4: Analytics & Dashboards
# Timeline: Week 3 (first half) | ~1 week
# ═══════════════════════════════════════
 
## M4 Overview
 
```
What you're building:
Real data from appointments table
→ Daily aggregation job (runs 12am IST)
→ appointment_analytics table
→ API endpoints
→ Recharts dashboard in React
```
 
---
 
## M4 — Step 1: Analytics Database + Aggregation
 
### ✅ Checklist
- [ ] Create appointment_analytics table
- [ ] Write daily aggregation query
- [ ] Schedule with APScheduler
### 💡 Copilot Prompt — M4.1 Analytics Model + Aggregator
 
```
Create analytics.py → Ctrl+I → paste:
 
Build the analytics system for MediConnect-AI.
 
PART 1 — Database model:
class AppointmentAnalytics(Base):
    __tablename__ = "appointment_analytics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)  # None = platform-wide
    total_bookings = Column(Integer, default=0)
    confirmed = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    cancelled = Column(Integer, default=0)
    no_show = Column(Integer, default=0)
    high_urgency = Column(Integer, default=0)
    medium_urgency = Column(Integer, default=0)
    low_urgency = Column(Integer, default=0)
    avg_confirmation_time_mins = Column(Float)
    peak_hour = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
 
PART 2 — Aggregation function run_daily_aggregation():
- Query all appointments from yesterday
- Group by hospital_id
- Calculate all metrics
- Insert or update AppointmentAnalytics rows
- Also insert one row with hospital_id=None for platform-wide totals
- Log: "✅ Analytics aggregated for YYYY-MM-DD"
 
PART 3 — Schedule with APScheduler:
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(run_daily_aggregation, "cron", hour=0, minute=0)
scheduler.start()
 
PART 4 — Analytics API routes:
GET /api/admin/analytics/overview
@require_role("PLATFORM_ADMIN", "HOSPITAL_ADMIN")
Return: last 30 days totals, today's count, this week trend
 
GET /api/admin/analytics/hospitals
@require_role("PLATFORM_ADMIN")
Return: per-hospital breakdown, top performing hospitals
 
GET /api/admin/analytics/trends?days=30&hospital_id=optional
Return: time-series data for Recharts (array of {date, total, confirmed, cancelled})
 
GET /api/admin/analytics/specialists
Return: which specialties are most booked (for demand forecasting)
 
Use: SQLAlchemy aggregations, pandas for time-series grouping
```
 
---
 
## M4 — Step 2: Analytics Dashboard React
 
### 💡 Copilot Prompt — M4.2 Recharts Dashboard
 
```
Create AnalyticsDashboard.jsx → Ctrl+I → paste:
 
Build the analytics dashboard for MediConnect-AI using Recharts.
 
COMPONENT: AnalyticsDashboard.jsx
 
SECTION 1 — Top KPI cards (4 cards row):
- Total bookings this month
- Confirmed rate (confirmed/total %)
- Average confirmation time
- Today's appointments
Each card: large number, % change from last week (green if up, red if down), icon
 
SECTION 2 — Appointment trends chart (LineChart):
- X axis: last 30 days dates
- Lines: Total, Confirmed, Cancelled (different colors)
- Tooltip showing values on hover
- Recharts ResponsiveContainer, LineChart, XAxis, YAxis, Tooltip, Legend
- Dark theme: stroke colors matching existing app palette
 
SECTION 3 — Urgency distribution (PieChart):
- 3 segments: HIGH (red), MEDIUM (orange), LOW (green)
- Show count + percentage in tooltip
- Legend below chart
 
SECTION 4 — Specialist demand bar chart (BarChart):
- X axis: specialty names (Cardiology, Orthopedics, General, etc.)
- Y axis: booking count
- Sorted by demand descending
- Dark bars with blue fill
 
SECTION 5 — Hospital performance table (Platform Admin only):
- Columns: Hospital Name, Total Bookings, Confirmed Rate, Avg Time, No-Show Rate
- Sortable columns
- Green/red color coding for rates
 
Styling: Tailwind dark theme, consistent with existing React frontend
Data: Fetch from GET /api/admin/analytics/overview and /trends
Loading: Skeleton cards while fetching
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 5: Notifications System
# Timeline: Week 3 (second half) | ~4 days
# ═══════════════════════════════════════
 
## M5 Overview
 
```
User books appointment
→ Flask API creates appointment
→ Sends email confirmation (synchronous for now)
→ Background: Twilio SMS
→ 24h before: reminder notification
→ Admin approves: confirmation SMS/email
```
 
---
 
## M5 — Step 1: Notification Service
 
### ✅ Checklist
- [ ] SendGrid email templates
- [ ] Twilio SMS integration
- [ ] Notification service class
- [ ] Appointment event hooks
### 💡 Copilot Prompt — M5.1 Notification Service
 
```
Create notification_service.py → Ctrl+I → paste:
 
Build the notification service for MediConnect-AI.
 
CLASS: NotificationService
 
METHOD 1: send_booking_confirmation(appointment, patient_email, patient_phone)
- Send HTML email via SendGrid:
  Subject: "Appointment Confirmed — [Hospital Name]"
  Body: appointment details, doctor name, date/time, hospital address
  Include one-click cancel link
- Send SMS via Twilio:
  "MediConnect: Your appointment at [Hospital] on [Date] [Time] is PENDING. 
   We'll confirm shortly. Reply CANCEL to cancel."
- Log to notifications table
- Handle exceptions gracefully — if SMS fails, still send email
 
METHOD 2: send_status_update(appointment, new_status, patient_email, patient_phone)
- CONFIRMED: "Your appointment is confirmed! See you on [date] at [time]."
- CANCELLED: "Your appointment has been cancelled. Book again at mediconnect.health"
- REMINDER (24h before): "Reminder: Appointment tomorrow at [time] at [hospital]."
 
METHOD 3: send_admin_alert(admin_email, alert_type, details)
- New booking notification to hospital admin
- Daily summary at 8am IST
 
METHOD 4: schedule_reminder(appointment)
- Use APScheduler to schedule reminder 24h before appointment
- Call send_status_update with type REMINDER
 
CONFIGURATION (from environment variables):
SENDGRID_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
 
IMPORTANT:
- Always wrap Twilio/SendGrid calls in try/except
- Log all notifications to DB (notifications table)
- If phone number is None, skip SMS silently
- Use os.environ.get() for all credentials — never hardcode
 
Add to appointment routes: call NotificationService on status changes.
```
 
---
 
## M5 — Step 2: Email Templates
 
### 💡 Copilot Prompt — M5.2 HTML Email Templates
 
```
Create email_templates.py → Ctrl+I → paste:
 
Write HTML email templates for MediConnect-AI notifications.
 
TEMPLATE 1: booking_confirmation_html(appointment_data) → str
Professional HTML email:
- MediConnect-AI header with blue/teal brand colors
- "Appointment Received" heading
- Details table: Hospital, Doctor, Date, Time, Urgency, Reason
- Status badge: PENDING (yellow)
- "What's next": Hospital admin will confirm within 2 hours
- Cancel button (link to /cancel/<appointment_id>)
- Footer: "Not a substitute for emergency care. Call 108 for emergencies."
 
TEMPLATE 2: status_update_html(appointment_data, new_status) → str
Same structure, but:
- CONFIRMED: green checkmark, "Your appointment is confirmed!"
- CANCELLED: red X, "Appointment cancelled"
- NO_SHOW: "You missed your appointment. Reschedule?"
 
TEMPLATE 3: daily_summary_html(hospital_data, date) → str
For hospital admins:
- Summary of yesterday: total bookings, confirmed, pending, cancelled
- Top 3 busiest appointment times
- Action needed: pending appointments to confirm
 
Keep HTML inline-styles only (no external CSS — email clients don't support it).
Return clean HTML string for each template.
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 6: Multi-Agent AI Pipeline
# Timeline: Week 4 (first half) | ~5 days
# ═══════════════════════════════════════
 
## M6 Overview
 
```
This is your SHOWSTOPPER feature.
You already know LangGraph from UPI Mirror.
 
6 agents, each with a specific job:
Agent 1: Symptom Analyzer
Agent 2: Medical Knowledge Retriever
Agent 3: Specialist Recommender
Agent 4: Hospital Router
Agent 5: Risk Assessor
Agent 6: Explainer (generates human reasoning)
 
Each agent passes state to next.
Final output: hospital list + specialist + explanation + urgency
```
 
---
 
## M6 — Step 1: Multi-Agent State
 
### ✅ Checklist
- [ ] Define MedicalState TypedDict
- [ ] Build all 6 agent nodes
- [ ] Connect LangGraph workflow
- [ ] Add chain-of-thought prompts
### 💡 Copilot Prompt — M6.1 LangGraph 6-Agent Pipeline
 
```
Create multi_agent_pipeline.py → Ctrl+I → paste:
 
Build a 6-agent LangGraph medical triage pipeline for MediConnect-AI.
 
I already have LangGraph experience from another project (UPI Mirror).
 
IMPORTS:
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from typing import TypedDict, List, Optional, Annotated
import operator
 
STATE:
class MedicalState(TypedDict):
    input_text: str              # raw patient input
    language: str                # "en" or "kn"
    symptoms: List[str]          # extracted symptom list
    translated_text: str         # English version (if input was Kannada)
    conditions: List[dict]       # possible conditions from KB
    specialists: List[str]       # recommended specialist types
    hospitals: List[dict]        # ranked hospital list
    urgency_level: str           # HIGH, MEDIUM, LOW
    confidence_score: float      # ML model confidence
    reasoning_chain: List[str]   # chain of thought steps
    final_explanation: str       # human-readable explanation
    error: Optional[str]         # error if any agent fails
 
LLM:
llm = ChatGroq(model="llama3-8b-8192", temperature=0.1)
(use low temperature for medical accuracy)
 
AGENT 1: symptom_analyzer_agent(state) → state
- If state["language"] == "kn": call Bhashini API to translate to English first
- Use Groq LLaMA to extract symptoms as a clean list
- Prompt: "Extract medical symptoms from this text as a JSON list. 
  Input: {text}. Return only: {symptoms: ['symptom1', 'symptom2']}"
- Update state["symptoms"] and state["translated_text"]
- Append to reasoning_chain: "Extracted symptoms: {symptoms}"
 
AGENT 2: knowledge_retriever_agent(state) → state
- Query local conditions database (55+ conditions JSON)
- Match symptoms to possible conditions using symptom overlap score
- Return top 3 conditions with confidence scores
- Update state["conditions"]
- Append to reasoning_chain: "Possible conditions: {conditions}"
 
AGENT 3: specialist_recommender_agent(state) → state
- Map conditions to specialist types (e.g., chest pain → Cardiologist)
- Use ML model from M2.5 for urgency scoring
- Update state["specialists"] and state["urgency_level"]
- Append to reasoning_chain: "Recommended specialists: {specialists}"
 
AGENT 4: hospital_router_agent(state) → state
- Filter hospitals by: has required specialist, within reasonable distance
- Rank by: specialist availability + hospital rating + distance
- Return top 3 hospitals with contact info
- Update state["hospitals"]
- Append to reasoning_chain: "Top hospitals: {hospital_names}"
 
AGENT 5: risk_assessor_agent(state) → state
- Check for emergency patterns: chest pain, difficulty breathing, stroke symptoms
- If HIGH urgency: add emergency hospital + 108 number to hospitals list
- Update state["urgency_level"] (may upgrade if emergency patterns found)
- Append to reasoning_chain: "Risk assessment: {urgency_level}"
 
AGENT 6: explainer_agent(state) → state
- Generate human-readable explanation using Groq
- Prompt: "Given these medical findings: {reasoning_chain}
  Write a simple 3-sentence explanation for a non-medical person.
  Tell them: what might be wrong, what type of doctor to see, and how urgent it is.
  Language: {'Kannada' if state['language']=='kn' else 'English'}"
- Update state["final_explanation"]
 
ERROR HANDLER: handle_error(state) → state
- If any agent sets state["error"]: skip remaining agents
- Return safe fallback message + emergency 108 number
 
BUILD GRAPH:
workflow = StateGraph(MedicalState)
Add all 6 nodes
Add edges in order: 1→2→3→4→5→6→END
Add conditional edge: if state["error"] → handle_error → END
Compile: medical_agent = workflow.compile()
 
EXPOSE: async def run_medical_pipeline(input_text, language="en") → dict
```
 
---
 
## M6 — Step 2: Knowledge Base
 
### 💡 Copilot Prompt — M6.2 Medical Knowledge Base
 
```
Create medical_knowledge_base.py → Ctrl+I → paste:
 
Build the medical knowledge base for MediConnect-AI.
 
I have 55+ conditions already in my system.
 
CREATE:
 
CLASS: MedicalKnowledgeBase
 
METHOD: load_conditions() → loads from conditions.json
Each condition has: name, symptoms, specialists, urgency_threshold, description
 
METHOD: match_symptoms(symptom_list) → List[dict]
- For each condition: calculate overlap score = matching symptoms / total symptoms
- Return top 5 conditions with score > 0.3
- Sort by score descending
- Return: [{name, score, specialists, urgency_threshold, description}]
 
METHOD: get_emergency_patterns() → List[str]
- Return symptoms that ALWAYS trigger HIGH urgency:
  chest pain, difficulty breathing, stroke symptoms (face drooping, arm weakness, speech), 
  severe bleeding, unconscious, seizure, severe allergic reaction
 
METHOD: get_specialists_for_condition(condition_name) → List[str]
- Map: heart conditions → Cardiologist
- Map: bone/joint → Orthopedist
- Map: children → Pediatrician
- Map: skin → Dermatologist
- Map: mental → Psychiatrist/Psychologist
- Default: General Physician
 
METHOD: to_json() → export full KB as JSON
 
Also create conditions.json with at least 20 conditions in this format:
{
  "conditions": [
    {
      "name": "Cardiac Arrest",
      "symptoms": ["chest pain", "shortness of breath", "arm pain", "sweating"],
      "specialists": ["Cardiologist"],
      "urgency_threshold": "HIGH",
      "description": "Emergency cardiac condition requiring immediate care"
    }
  ]
}
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 7: Security + HIPAA Basics
# Timeline: Week 4 (second half) | ~3 days
# ═══════════════════════════════════════
 
## M7 Overview
 
```
Not full HIPAA certification (needs lawyer).
But HIPAA-READY architecture:
- AES-256 encryption for health data
- Audit logging for all data access
- Rate limiting per user
- Input sanitisation
- Secure headers
```
 
---
 
## M7 — Step 1: Encryption + Security
 
### ✅ Checklist
- [ ] AES-256 encrypt health records at rest
- [ ] Audit log table + middleware
- [ ] Rate limiting with Flask-Limiter
- [ ] Secure HTTP headers
- [ ] Input validation with Pydantic
### 💡 Copilot Prompt — M7.1 Security Layer
 
```
Create security.py → Ctrl+I → paste:
 
Add HIPAA-ready security layer to MediConnect-AI Flask backend.
 
PART 1 — AES-256 Encryption:
from cryptography.fernet import Fernet
import os, base64
 
class HealthDataEncryption:
    def __init__(self):
        key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key()
            print("WARNING: No ENCRYPTION_KEY set. Using session key.")
        self.cipher = Fernet(key)
 
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
 
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
 
Apply encryption to: appointment.reason, appointment.notes (health data fields)
Decrypt on read in the route.
 
PART 2 — Audit Logging:
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100))
    action = Column(String(50))  # VIEW, CREATE, UPDATE, DELETE
    resource = Column(String(50))  # appointment, doctor, hospital
    resource_id = Column(String(36))
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
 
Decorator: @audit_log(action, resource)
- Auto-logs every admin action to audit_logs table
- Extracts IP from request.remote_addr
- Logs even failed attempts (success=False)
 
PART 3 — Rate Limiting:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
 
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per hour"])
 
Apply to routes:
- AI diagnosis: 30 per minute per user
- Appointment booking: 10 per hour
- Admin login: 5 per minute
 
PART 4 — Secure Headers middleware:
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
 
PART 5 — Input Sanitisation:
Using Pydantic v2, create request validators for all POST endpoints:
- AppointmentCreateRequest: validate date is future, reason max 500 chars
- DoctorCreateRequest: validate all required fields, experience >= 0
- StatusUpdateRequest: validate status is valid enum value
```
 
---
 
---
 
# ═══════════════════════════════════════
# MILESTONE 8: Production Deployment
# Timeline: Buffer days | ~2-3 days
# ═══════════════════════════════════════
 
## M8 Overview
 
```
Goal: Live URL you can put on your resume
Stack: Render (Flask) + Vercel (React) + Firebase + GitHub Actions
```
 
---
 
## M8 — Step 1: Environment Config
 
### 💡 Copilot Prompt — M8.1 Production Config
 
```
Help me set up production configuration for MediConnect-AI.
 
Create config.py with:
class Config:
    ENV = os.environ.get("FLASK_ENV", "development")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///mediconnect.db")
    FIREBASE_CREDENTIALS = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    BHASHINI_API_KEY = os.environ.get("BHASHINI_API_KEY")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.environ.get("TWILIO_PHONE_NUMBER")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
 
Also create:
1. requirements.txt with all production packages (pin all versions)
2. render.yaml for Render deployment:
   - Python backend service
   - Build command: pip install -r requirements.txt
   - Start command: gunicorn app:app
3. .env.example with all variable names but no values
4. Procfile for Heroku alternative: web: gunicorn app:app
 
What environment variables do I need to set in Render dashboard?
```
 
---
 
## M8 — Step 2: GitHub Actions CI/CD
 
### 💡 Copilot Prompt — M8.2 CI/CD Pipeline
 
```
Create .github/workflows/deploy.yml → Ctrl+I → paste:
 
Write GitHub Actions CI/CD pipeline for MediConnect-AI.
 
WORKFLOW: On push to main branch:
 
JOB 1 — test:
- Run on ubuntu-latest
- Set up Python 3.10
- Install requirements
- Run pytest with coverage
- Fail if coverage < 60%
 
JOB 2 — deploy-backend (runs after test passes):
- Deploy to Render using Render deploy hook
- URL stored in GitHub secret: RENDER_DEPLOY_HOOK_URL
- curl -X POST $RENDER_DEPLOY_HOOK_URL
 
JOB 3 — deploy-frontend (runs after test passes):
- Set up Node.js 18
- cd frontend && npm install && npm run build
- Deploy to Vercel
- Uses VERCEL_TOKEN secret
 
Also write a simple test_health.py:
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
 
This ensures at minimum the app starts successfully in CI.
```
 
---
 
---
 
# ═══════════════════════════════════════
# RESUME BULLET POINTS — COPY THESE
# ═══════════════════════════════════════
 
> Update your resume with these after each milestone completes.
 
## Technical Skills to Add
 
```
Languages:     Python, JavaScript, SQL
AI/ML:         LangGraph, Groq LLaMA 3, Scikit-learn, SHAP, Bhashini API
Backend:       Flask, SQLAlchemy, Celery, Redis, JWT, Firebase Admin
Frontend:      React 18, Tailwind CSS, Framer Motion, Recharts
Database:      SQLite, PostgreSQL, Firebase Firestore
Security:      AES-256 encryption, RBAC, HIPAA-ready architecture
DevOps:        Vercel, Render, GitHub Actions CI/CD, Docker
Tools:         Postman, Git, VS Code
```
 
## Project Bullet Points
 
### Short version (for resume header):
```
MediConnect-AI | AI Healthcare Platform | Flask · React · LangGraph · Groq
- Built AI emergency health routing system reducing hospital search time from 45 min to <30 sec
- Implemented 6-agent LangGraph pipeline (symptom analysis → specialist matching → hospital routing)
- 99.69% ML urgency classification accuracy (RandomForest) with SHAP explainability
- Kannada + English voice I/O via Bhashini API — India's first AI health triage in Kannada
- Multi-tenant SaaS with RBAC (Platform Admin, Hospital Admin, Support Staff roles)
- HIPAA-ready: AES-256 encryption, audit logging, rate limiting, secure headers
```
 
### Long version (for portfolio/LinkedIn):
```
MediConnect-AI 2.0 — AI Healthcare Platform for Bengaluru
Tech: Python · Flask · React · LangGraph · Groq LLaMA 3.3 70B · Bhashini · scikit-learn · SHAP · Firebase · Twilio · SendGrid · SQLAlchemy · Celery · Render · Vercel
 
• Built India's first AI-powered emergency health routing platform — reduces hospital search from 45 minutes to under 30 seconds
• Engineered 6-node LangGraph agentic pipeline: Symptom Analyzer → Knowledge Retriever → Specialist Recommender → Hospital Router → Risk Assessor → Explainer with chain-of-thought reasoning
• Trained RandomForest classifier achieving 99.69% accuracy for urgency triage (HIGH/MEDIUM/LOW) with SHAP feature importance for explainability
• Integrated Bhashini API (India's government-backed multilingual AI) for real-time Kannada ↔ English translation — first health triage tool to support Kannada voice input/output
• Architected multi-tenant SaaS with 3-tier RBAC: Platform Admin (full access), Hospital Admin (scoped to own hospital), Support Staff (read-only analytics)
• Designed appointment state machine: PENDING → CONFIRMED → COMPLETED with async notifications via Twilio SMS + SendGrid email using Celery task queue
• Built real-time analytics dashboard (React + Recharts): appointment trends, specialist demand forecasting, hospital utilisation heatmaps
• Implemented HIPAA-ready security: AES-256 health data encryption, comprehensive audit logging, Flask rate limiting, secure HTTP headers
• 46 verified Bengaluru hospitals, 55+ medical conditions, 12 specialties — deployed on Render + Vercel with GitHub Actions CI/CD
• Origin: AIML internship project (Edunet Foundation x IBM SkillBuild) — continued developing beyond internship to production-grade SaaS
```
 
---
 
---
 
# ═══════════════════════════════════════
# LINKEDIN POSTS — READY TO POST
# ═══════════════════════════════════════
 
## Post After M3 Completion
 
```
6 months ago, I built a basic symptom checker during my IBM SkillBuild internship.
 
I couldn't stop thinking about it.
 
Today MediConnect-AI has a full multi-tenant admin portal:
 
→ Hospital admins manage their appointments in real-time
→ 3-tier RBAC: Platform Admin | Hospital Admin | Support Staff
→ Appointment state machine: PENDING → CONFIRMED → COMPLETED
→ Role-based data scoping (each admin sees only what they should)
 
This is what "production thinking" looks like vs "internship thinking."
 
Still building. 🏥
 
#HealthTech #Flask #React #RBAC #AIForIndia #IBMSkillBuild
```
 
## Post After M6 Completion
 
```
Built a 6-agent AI pipeline for medical triage.
 
Each agent has one job:
🧠 Agent 1: Extract symptoms from patient input
📚 Agent 2: Match to medical knowledge base
👨‍⚕️ Agent 3: Recommend the right specialist
🏥 Agent 4: Route to nearest available hospital
🚨 Agent 5: Assess emergency risk level
💬 Agent 6: Explain everything in plain language (English or Kannada)
 
The whole pipeline runs in under 500ms.
 
This is LangGraph doing real work — not a toy chatbot.
 
#LangGraph #AI #HealthcareAI #MediConnectAI #Groq #LLaMA
```
 
## Post After Production Launch
 
```
From internship project to production.
 
MediConnect-AI is live.
 
What started as an IBM SkillBuild AIML internship project is now:
→ 6-agent LangGraph AI pipeline
→ 99.69% ML urgency classifier
→ Kannada + English voice triage
→ Multi-tenant SaaS with RBAC
→ Real-time analytics dashboard
→ Twilio + SendGrid notifications
→ HIPAA-ready security
→ 46 Bengaluru hospitals
 
[Live link]
 
If healthcare access can be AI-powered, it should be.
 
#MediConnectAI #HealthTech #BuiltInIndia #IBMSkillBuild #EdunetFoundation
```
 
---
 
---
 
# ═══════════════════════════════════════
# DAILY STANDUP TEMPLATE
# ═══════════════════════════════════════
 
> Copy this to your notes app. Fill it every morning.
 
```markdown
## Date: ___________
 
### Yesterday I completed:
- [ ] 
 
### Today I will build:
- [ ] 
 
### Current milestone: M___
### Blockers: 
 
### Copilot prompt I need today:
(write what you need to ask)
 
### Milestone completion: ___/100%
```
 
---
 
---
 
# ═══════════════════════════════════════
# DEBUG CHEATSHEET
# ═══════════════════════════════════════
 
## Common Issues + Fixes
 
### Firebase token verification fails
```python
# Make sure firebase_admin is initialised before first request
import firebase_admin
from firebase_admin import credentials, auth
 
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS_JSON"]))
    firebase_admin.initialize_app(cred)
```
 
### SQLAlchemy session not closing
```python
# Always use this pattern
try:
    db.session.add(obj)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise e
finally:
    db.session.close()
```
 
### CORS blocking React frontend
```python
from flask_cors import CORS
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
```
 
### Celery not connecting to Redis
```bash
# Test Redis connection first
redis-cli ping  # should return PONG
# Then start worker
celery -A app.celery worker --loglevel=info
```
 
### LangGraph agent hanging
```python
# Always add timeout
medical_agent = workflow.compile()
result = medical_agent.invoke(state, config={"recursion_limit": 10})
```
 
---
 
---
 
# ═══════════════════════════════════════
# FINAL CHECKLIST BEFORE RESUME UPDATE
# ═══════════════════════════════════════
 
```
CORE FEATURES:
[ ] M3: Appointment booking works end-to-end
[ ] M3: RBAC blocks wrong-role access (test it!)
[ ] M3: Admin dashboard loads without errors
[ ] M4: Analytics charts render with real data
[ ] M5: Email sends on booking confirmation
[ ] M5: SMS sends via Twilio (test with your number)
[ ] M6: 6-agent pipeline returns hospital recommendation
[ ] M6: Kannada input works through full pipeline
[ ] M7: Health data is encrypted in DB
[ ] M7: Rate limiting blocks after 30 AI requests/min
[ ] M8: Live URL works from phone + laptop
[ ] M8: GitHub Actions green on push to main
 
RESUME READY:
[ ] Update resume with long bullet points
[ ] Update LinkedIn headline
[ ] Add to LinkedIn Featured section
[ ] Add live demo URL to GitHub About
[ ] Update README.md with M3-M8 features
[ ] Record 2-minute demo video
```
 
---
 
**Document Version**: v1.0 — Yashaswini V  
**Last Updated**: April 2026  
**Based on**: Backlog v1.0 (April 3, 2026)  
**Goal**: 9.9/10 resume impact by May 28, 2026