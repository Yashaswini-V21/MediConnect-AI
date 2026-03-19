"""
AI Reliability and Evaluation Dashboard
Metrics tracking for latency, fallback, high-risk detection, speech success
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class ReliabilityMetrics:
    """Tracks system reliability metrics for dashboard"""
    
    def __init__(self):
        # Event tracking
        self.triage_events = []
        self.safety_events = []
        self.voice_events = []
        self.routing_events = []
        
        # Aggregated stats (daily)
        self.daily_stats = defaultdict(lambda: {
            'triage_count': 0,
            'avg_latency_ms': 0,
            'fallback_triggered': 0,
            'emergency_detected': 0,
            'success_rate': 0,
            'voice_success_rate': 0
        })
    
    def log_triage_event(
        self,
        flow_id: str,
        risk_level: str,
        latency_ms: float,
        fallback_used: bool = False,
        error: Optional[str] = None
    ) -> None:
        """Log triage pipeline event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'flow_id': flow_id,
            'risk_level': risk_level,
            'latency_ms': latency_ms,
            'fallback_used': fallback_used,
            'error': error,
            'success': error is None
        }
        
        self.triage_events.append(event)
        logger.info(f"Triage event logged: {risk_level}, {latency_ms:.0f}ms, fallback={fallback_used}")
    
    def log_safety_event(
        self,
        flow_id: str,
        is_emergency: bool,
        flag_matched: Optional[str] = None,
        latency_ms: float = 0
    ) -> None:
        """Log safety guardrail event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'flow_id': flow_id,
            'is_emergency': is_emergency,
            'flag_matched': flag_matched,
            'latency_ms': latency_ms
        }
        
        self.safety_events.append(event)
        if is_emergency:
            logger.critical(f"Emergency detected: {flag_matched}")
        else:
            logger.debug(f"Safety check passed")
    
    def log_voice_event(
        self,
        flow_id: str,
        language: str,
        success: bool,
        transcript_length: int = 0,
        latency_ms: float = 0,
        error: Optional[str] = None
    ) -> None:
        """Log voice/speech event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'flow_id': flow_id,
            'language': language,
            'success': success,
            'transcript_length': transcript_length,
            'latency_ms': latency_ms,
            'error': error
        }
        
        self.voice_events.append(event)
        logger.info(f"Voice event: {language}, success={success}, chars={transcript_length}")
    
    def log_routing_event(
        self,
        flow_id: str,
        hospitals_found: int,
        distance_to_nearest_km: float,
        eta_minutes: int,
        success: bool = True
    ) -> None:
        """Log routing/mapping event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'flow_id': flow_id,
            'hospitals_found': hospitals_found,
            'nearest_distance_km': distance_to_nearest_km,
            'eta_minutes': eta_minutes,
            'success': success
        }
        
        self.routing_events.append(event)
        logger.info(f"Routing event: {hospitals_found} hospitals, {distance_to_nearest_km:.1f}km away")
    
    def get_daily_metrics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregated daily metrics
        
        Args:
            date: YYYY-MM-DD format, defaults to today
            
        Returns:
            Daily metrics summary
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Filter events for date
        triage_today = [e for e in self.triage_events if e['timestamp'].startswith(date)]
        safety_today = [e for e in self.safety_events if e['timestamp'].startswith(date)]
        voice_today = [e for e in self.voice_events if e['timestamp'].startswith(date)]
        routing_today = [e for e in self.routing_events if e['timestamp'].startswith(date)]
        
        # Calculate metrics
        metrics = {
            'date': date,
            'timestamp_generated': datetime.utcnow().isoformat(),
            'triage': self._calculate_triage_metrics(triage_today),
            'safety': self._calculate_safety_metrics(safety_today),
            'voice': self._calculate_voice_metrics(voice_today),
            'routing': self._calculate_routing_metrics(routing_today),
            'overall': self._calculate_overall_metrics(
                triage_today, safety_today, voice_today, routing_today
            )
        }
        
        return metrics
    
    def _calculate_triage_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate triage-specific metrics"""
        if not events:
            return {
                'total_analyses': 0,
                'avg_latency_ms': 0,
                'critical_cases': 0,
                'fallback_rate': 0,
                'success_rate': 100
            }
        
        successful = [e for e in events if e['success']]
        critical = [e for e in events if e['risk_level'] == 'CRITICAL']
        fallback_used = [e for e in events if e['fallback_used']]
        
        avg_latency = sum(e['latency_ms'] for e in events) / len(events) if events else 0
        
        return {
            'total_analyses': len(events),
            'avg_latency_ms': round(avg_latency, 2),
            'critical_cases': len(critical),
            'high_cases': len([e for e in events if e['risk_level'] == 'HIGH']),
            'moderate_cases': len([e for e in events if e['risk_level'] == 'MODERATE']),
            'low_cases': len([e for e in events if e['risk_level'] == 'LOW']),
            'fallback_rate_percent': round((len(fallback_used) / len(events) * 100), 1),
            'success_rate_percent': round((len(successful) / len(events) * 100), 1)
        }
    
    def _calculate_safety_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate safety guardrail metrics"""
        if not events:
            return {
                'total_checks': 0,
                'emergencies_detected': 0,
                'emergency_rate': 0,
                'top_flags': {}
            }
        
        emergencies = [e for e in events if e['is_emergency']]
        flags = defaultdict(int)
        for e in emergencies:
            if e.get('flag_matched'):
                flags[e['flag_matched']] += 1
        
        return {
            'total_checks': len(events),
            'emergencies_detected': len(emergencies),
            'emergency_rate_percent': round((len(emergencies) / len(events) * 100), 1),
            'top_flags': dict(sorted(flags.items(), key=lambda x: x[1], reverse=True)[:5]),
            'avg_latency_ms': round(sum(e['latency_ms'] for e in events) / len(events), 2) if events else 0
        }
    
    def _calculate_voice_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate speech/voice metrics"""
        if not events:
            return {
                'total_attempts': 0,
                'success_rate': 0,
                'english_rate': 0,
                'kannada_rate': 0,
                'avg_latency_ms': 0
            }
        
        successful = [e for e in events if e['success']]
        english = [e for e in events if 'en' in e.get('language', 'en').lower()]
        kannada = [e for e in events if 'kn' in e.get('language', '').lower()]
        
        return {
            'total_attempts': len(events),
            'success_rate_percent': round((len(successful) / len(events) * 100), 1),
            'failed_attempts': len(events) - len(successful),
            'english_usage_percent': round((len(english) / len(events) * 100), 1) if events else 0,
            'kannada_usage_percent': round((len(kannada) / len(events) * 100), 1) if events else 0,
            'avg_transcript_length': round(sum(e['transcript_length'] for e in events) / len(events), 0) if events else 0,
            'avg_latency_ms': round(sum(e['latency_ms'] for e in events) / len(events), 2) if events else 0
        }
    
    def _calculate_routing_metrics(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate routing/mapping metrics"""
        if not events:
            return {
                'total_routes': 0,
                'success_rate': 0,
                'avg_distance_km': 0,
                'avg_eta_minutes': 0
            }
        
        successful = [e for e in events if e['success']]
        
        avg_distance = sum(e['nearest_distance_km'] for e in events) / len(events) if events else 0
        avg_eta = sum(e['eta_minutes'] for e in events) / len(events) if events else 0
        
        return {
            'total_routes': len(events),
            'success_rate_percent': round((len(successful) / len(events) * 100), 1),
            'avg_distance_km': round(avg_distance, 2),
            'avg_eta_minutes': round(avg_eta, 1),
            'max_distance_km': max(e['nearest_distance_km'] for e in events) if events else 0,
            'avg_hospitals_found': round(sum(e['hospitals_found'] for e in events) / len(events), 1) if events else 0
        }
    
    def _calculate_overall_metrics(
        self,
        triage_events: List[Dict],
        safety_events: List[Dict],
        voice_events: List[Dict],
        routing_events: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate overall system metrics"""
        all_events = len(triage_events) + len(safety_events) + len(voice_events) + len(routing_events)
        
        latencies = (
            [e['latency_ms'] for e in triage_events] +
            [e['latency_ms'] for e in safety_events] +
            [e['latency_ms'] for e in voice_events]
        )
        
        return {
            'total_interactions': all_events,
            'avg_latency_ms': round(sum(latencies) / len(latencies), 2) if latencies else 0,
            'p95_latency_ms': round(sorted(latencies)[int(len(latencies)*0.95)], 2) if latencies else 0,
            'system_health': "HEALTHY" if all_events > 0 else "IDLE"
        }
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get current dashboard summary for UI"""
        today_metrics = self.get_daily_metrics()
        
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'today': today_metrics,
            'health_status': today_metrics['overall']['system_health'],
            'key_indicators': {
                'triage_success_rate': today_metrics['triage']['success_rate_percent'],
                'emergency_detection_rate': today_metrics['safety']['emergency_rate_percent'],
                'voice_success_rate': today_metrics['voice']['success_rate_percent'],
                'avg_triage_latency_ms': today_metrics['triage']['avg_latency_ms'],
                'critical_cases_today': today_metrics['triage']['critical_cases']
            }
        }


# Singleton instance
_metrics_instance = None

def get_reliability_metrics() -> ReliabilityMetrics:
    """Get singleton metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = ReliabilityMetrics()
    return _metrics_instance
