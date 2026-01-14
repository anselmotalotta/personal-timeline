"""
Local API usage tracking and cost monitoring
"""
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class UsageRecord:
    """Record of API usage for local tracking"""
    timestamp: str
    provider: str
    endpoint: str
    tokens_used: int
    estimated_cost: float
    success: bool
    task_type: str
    response_time_ms: int

class LocalUsageTracker:
    """Track API usage locally for cost monitoring and analytics"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = config.get_data_path() / "api_usage.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize the local usage tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    estimated_cost REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    task_type TEXT,
                    response_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON api_usage(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider 
                ON api_usage(provider)
            """)
            
    def record_usage(self, 
                    provider: str,
                    endpoint: str, 
                    tokens_used: int,
                    estimated_cost: float,
                    success: bool,
                    task_type: str = "general",
                    response_time_ms: int = 0):
        """Record API usage locally (never expose credentials)"""
        
        # Validate that no credentials are being logged
        safe_provider = config.validate_no_credentials_in_logs(provider)
        safe_endpoint = config.validate_no_credentials_in_logs(endpoint)
        safe_task_type = config.validate_no_credentials_in_logs(task_type)
        
        # Additional sanitization for common credential patterns
        safe_provider = self._sanitize_credential_patterns(safe_provider)
        safe_endpoint = self._sanitize_credential_patterns(safe_endpoint)
        safe_task_type = self._sanitize_credential_patterns(safe_task_type)
        
        record = UsageRecord(
            timestamp=datetime.utcnow().isoformat(),
            provider=safe_provider,
            endpoint=safe_endpoint,
            tokens_used=tokens_used,
            estimated_cost=estimated_cost,
            success=success,
            task_type=safe_task_type,
            response_time_ms=response_time_ms
        )
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO api_usage 
                    (timestamp, provider, endpoint, tokens_used, estimated_cost, 
                     success, task_type, response_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.timestamp,
                    record.provider,
                    record.endpoint,
                    record.tokens_used,
                    record.estimated_cost,
                    record.success,
                    record.task_type,
                    record.response_time_ms
                ))
                
            if config.enable_usage_analytics:
                logger.info(f"Recorded API usage: {safe_provider} - {safe_endpoint} - ${estimated_cost:.4f}")
                
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            
    def _sanitize_credential_patterns(self, text: str) -> str:
        """Remove common credential patterns from text"""
        import re
        
        # Remove API key patterns
        text = re.sub(r'sk-[a-zA-Z0-9]+', '[API_KEY_REDACTED]', text)
        text = re.sub(r'api[_-]?key[_-]?[a-zA-Z0-9]+', '[API_KEY_REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'secret[_-]?[a-zA-Z0-9]+', '[SECRET_REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'token[_-]?[a-zA-Z0-9]+', '[TOKEN_REDACTED]', text, flags=re.IGNORECASE)
        
        return text
            
    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get usage summary for the last N days"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Total usage
                total_result = conn.execute("""
                    SELECT 
                        COUNT(*) as total_calls,
                        SUM(estimated_cost) as total_cost,
                        SUM(tokens_used) as total_tokens,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
                    FROM api_usage 
                    WHERE timestamp >= ?
                """, (cutoff_date,)).fetchone()
                
                # Usage by provider
                provider_results = conn.execute("""
                    SELECT 
                        provider,
                        COUNT(*) as calls,
                        SUM(estimated_cost) as cost,
                        SUM(tokens_used) as tokens,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
                    FROM api_usage 
                    WHERE timestamp >= ?
                    GROUP BY provider
                    ORDER BY cost DESC
                """, (cutoff_date,)).fetchall()
                
                # Usage by endpoint
                endpoint_results = conn.execute("""
                    SELECT 
                        endpoint,
                        COUNT(*) as calls,
                        SUM(estimated_cost) as cost,
                        AVG(response_time_ms) as avg_response_time
                    FROM api_usage 
                    WHERE timestamp >= ?
                    GROUP BY endpoint
                    ORDER BY calls DESC
                """, (cutoff_date,)).fetchall()
                
                summary = {
                    "period_days": days,
                    "total": {
                        "calls": total_result["total_calls"] or 0,
                        "cost": round(total_result["total_cost"] or 0, 4),
                        "tokens": total_result["total_tokens"] or 0,
                        "avg_response_time_ms": round(total_result["avg_response_time"] or 0, 2),
                        "success_rate": (total_result["successful_calls"] or 0) / max(total_result["total_calls"] or 1, 1)
                    },
                    "by_provider": [
                        {
                            "provider": row["provider"],
                            "calls": row["calls"],
                            "cost": round(row["cost"], 4),
                            "tokens": row["tokens"],
                            "avg_response_time_ms": round(row["avg_response_time"], 2),
                            "success_rate": row["successful_calls"] / row["calls"]
                        }
                        for row in provider_results
                    ],
                    "by_endpoint": [
                        {
                            "endpoint": row["endpoint"],
                            "calls": row["calls"],
                            "cost": round(row["cost"], 4),
                            "avg_response_time_ms": round(row["avg_response_time"], 2)
                        }
                        for row in endpoint_results
                    ]
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {"error": str(e)}
            
    def get_daily_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily usage breakdown"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                results = conn.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as calls,
                        SUM(estimated_cost) as cost,
                        SUM(tokens_used) as tokens
                    FROM api_usage 
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (cutoff_date,)).fetchall()
                
                return [
                    {
                        "date": row["date"],
                        "calls": row["calls"],
                        "cost": round(row["cost"], 4),
                        "tokens": row["tokens"]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Failed to get daily usage: {e}")
            return []
            
    def cleanup_old_records(self, keep_days: int = None):
        """Clean up old usage records based on retention policy"""
        if keep_days is None:
            keep_days = config.keep_api_logs_days
            
        cutoff_date = (datetime.utcnow() - timedelta(days=keep_days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("""
                    DELETE FROM api_usage 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old usage records")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            
    def export_usage_data(self, output_path: str, days: int = 30) -> bool:
        """Export usage data to JSON file for backup or analysis"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                results = conn.execute("""
                    SELECT * FROM api_usage 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_date,)).fetchall()
                
                data = {
                    "export_date": datetime.utcnow().isoformat(),
                    "period_days": days,
                    "total_records": len(results),
                    "records": [dict(row) for row in results]
                }
                
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                    
                logger.info(f"Exported {len(results)} usage records to {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to export usage data: {e}")
            return False

# Global usage tracker instance
usage_tracker = LocalUsageTracker()