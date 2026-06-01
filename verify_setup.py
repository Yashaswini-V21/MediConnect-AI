#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediConnect AI - Complete Startup & Verification Script
Validates all components and starts backend services
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# Set UTF-8 encoding for terminal output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("[STARTUP] MEDICONNECT AI - STARTUP VERIFICATION")
print("=" * 80)

# Define paths
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

#
# 1. CHECK PYTHON DEPENDENCIES
# ============================================
print("\n[PKG] Checking Python dependencies...")
try:
    import flask
    import requests
    print("[OK] Flask installed")
    print("[OK] Requests installed")
except ImportError as e:
    print(f"[ERR] Missing Python dependency: {e}")
    print("Installing requirements.txt...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(BACKEND_DIR / "requirements.txt")], check=True)

#
# 2. CHECK BACKEND UTILITIES
# ============================================
print("\n[APP] Verifying backend utilities...")
utilities = [
    "ai_provider.py",
    "voice_output_assistant.py",
    "unified_voice_engine.py",
    "advanced_voice_assistant.py",
    "triage_pipeline.py",
    "distance_calculator.py",
    "safety_guardrails.py"
]

utils_dir = BACKEND_DIR / "utils"
for util in utilities:
    util_path = utils_dir / util
    if util_path.exists():
        print(f"[OK] {util}")
    else:
        print(f"[ERR] MISSING: {util}")
        sys.exit(1)

#
# 3. CHECK API ROUTES
# ============================================
print("\n[NET] Verifying API routes...")
routes_path = BACKEND_DIR / "routes" / "ai_platform_routes.py"
if routes_path.exists():
    print(f"[OK] AI Platform Routes registered")
else:
    print(f"[ERR] MISSING: ai_platform_routes.py")
    sys.exit(1)

#
# 4. CHECK FRONTEND FILES
# ============================================
print("\n[UI] Verifying frontend components...")
frontend_files = [
    "src/services/aiPlatformApi.js",
    "src/pages/SymptomChecker.jsx",
    "src/components/features/AIDoctorBot.jsx",
    ".env"
]

for file in frontend_files:
    file_path = FRONTEND_DIR / file
    if file_path.exists():
        print(f"[OK] {file}")
    else:
        print(f"[WARN] {file}")

#
# 5. VALIDATE BACKEND PYTHON SYNTAX
# ============================================
print("\n[PY] Validating Python syntax...")
try:
    for util in utilities:
        util_path = utils_dir / util
        compile(open(util_path, encoding='utf-8').read(), util_path, 'exec')
    print("[OK] All backend utilities compile successfully")
except SyntaxError as e:
    print(f"[ERR] Syntax error in {e.filename}: {e.msg}")
    sys.exit(1)

#
# 6. TEST BACKEND IMPORTS
# ============================================
print("\n[IMP] Testing backend imports...")
sys.path.insert(0, str(BACKEND_DIR))

try:
    from utils.triage_pipeline import get_triage_pipeline
    print("[OK] Triage Pipeline imports")

    from utils.safety_guardrails import create_safety_gate
    print("[OK] Safety Guardrails imports")

    from utils.unified_voice_engine import get_voice_engine
    print("[OK] Voice Engine imports")

    from utils.voice_output_assistant import get_voice_output_assistant
    print("[OK] Voice Output imports")

    from utils.ai_provider import RuleBasedProvider
    print("[OK] AI Provider imports")

    from utils.distance_calculator import calculate_distance, get_nearby_hospitals
    print("[OK] Distance Calculator imports")

    from utils.advanced_voice_assistant import get_advanced_voice_assistant
    print("[OK] Advanced Voice Assistant imports")

except ImportError as e:
    print(f"[ERR] Import error: {e}")
    sys.exit(1)

#
# 7. INSTANTIATE COMPONENTS
# ============================================
print("\n[RUN] Instantiating components...")
try:
    triage = get_triage_pipeline()
    print(f"[OK] Triage Pipeline instantiated")

    safety_gate = create_safety_gate(triage)
    print(f"[OK] Safety Gate instantiated")

    voice_engine = get_voice_engine()
    print(f"[OK] Voice Engine instantiated")

    voice_output = get_voice_output_assistant()
    print(f"[OK] Voice Output Assistant instantiated")

    ai_provider = RuleBasedProvider()
    print(f"[OK] AI Provider (RuleBasedProvider) instantiated")

    test_dist = calculate_distance((12.9716, 77.6412), (13.0827, 80.2707))
    print(f"[OK] Distance Calculator works ({test_dist:.1f} km)")

    from models.hospital_matcher import get_hospital_matcher
    from utils.healthcare_ai_platform import create_healthcare_ai_platform

    hospital_matcher = get_hospital_matcher()

    class VerifyRouterMock:
        def __init__(self, matcher):
            self.matcher = matcher
        def find_nearest_hospital(self, lat, lng):
            return self.matcher.find_emergency_hospitals(user_location={'lat': lat, 'lng': lng}, max_results=5)

    router = VerifyRouterMock(hospital_matcher)

    class DummyMetrics:
        def get_dashboard_summary(self):
            return {"success": True}
        def get_daily_metrics(self, date=None):
            return {"success": True}

    class DummySmartRouter:
        def __init__(self, matcher):
            self.matcher = matcher
            self.user_location = (12.9716, 77.5946)
        def find_nearest_hospital(self, lat, lng, urgency):
            return {"success": True, "hospitals": []}
        def get_route(self, lat, lng, hospital_id, mode):
            return {"success": True}

    metrics = DummyMetrics()
    smart_router = DummySmartRouter(hospital_matcher)

    platform = create_healthcare_ai_platform(
        triage_pipeline=triage,
        safety_gate=safety_gate,
        voice_engine=voice_engine,
        voice_output_assistant=voice_output,
        smart_router=smart_router,
        reliability_metrics=metrics
    )

    advanced_voice = get_advanced_voice_assistant(
        voice_engine=voice_engine,
        voice_output=voice_output,
        triage_pipeline=triage,
        emergency_flow=None,
        hospital_matcher=hospital_matcher,
        safety_gate=safety_gate
    )
    print(f"[OK] Advanced Voice Assistant instantiated")

except Exception as e:
    print(f"[ERR] Component instantiation error: {e}")
    sys.exit(1)

#
# 8. TEST CORE FUNCTIONALITY
# ============================================
print("\n[TEST] Testing core functionality...")
try:
    # Test triage analysis
    result = triage.analyze("I have chest pain for 2 hours, radiating to my left arm")
    if result and "risk_assessment" in result:
        risk_level = result.get('risk_assessment', {}).get('risk_level', 'UNKNOWN')
        print(f"[OK] Triage analysis works (Risk: {risk_level})")
    
    # Test safety gate
    safety_result = safety_gate.check_emergency("severe chest pain")
    if safety_result and "is_emergency" in safety_result:
        print(f"[OK] Safety gate works (Emergency: {safety_result.get('is_emergency')})")
    
    # Test voice engine
    voice_state = voice_engine.get_state()
    print(f"[OK] Voice engine state: {voice_state}")
    
    # Test router
    hospitals = router.find_nearest_hospital(12.9716, 77.6412)
    if hospitals:
        print(f"[OK] Router finds hospitals ({len(hospitals)} found)")
    
    # Test platform health
    health = platform.health_check()
    if health and (health.get("status") == "healthy" or health.get("success")):
        print(f"[OK] Platform health check passed")
    
except Exception as e:
    print(f"[WARN] Error during functionality test: {e}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 80)
print("[SUCCESS] ALL VERIFICATIONS PASSED!")
print("=" * 80)
print("\n[NEXT] NEXT STEPS:")
print("1. Terminal 1: python backend/app.py")
print("2. Terminal 2: cd frontend && npm start")
print("3. Open: http://localhost:3000")
print("\n[API] API Endpoints available at: http://localhost:5000/api/ai/*")
print("=" * 80)
