"""
Simple local data persistence for the POC.
Stores reports and JSON data under a .data/ directory.
Not for production use.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class DataPersistence:
    def __init__(self, base_dir: Optional[str] = None):
        # Default to a hidden .data directory inside the project
        self.base_dir = base_dir or os.path.join(os.getcwd(), ".data")
        os.makedirs(self.base_dir, exist_ok=True)
        self.reports_dir = os.path.join(self.base_dir, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        self.json_dir = os.path.join(self.base_dir, "json")
        os.makedirs(self.json_dir, exist_ok=True)

    def _safe_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).strip()

    def save_report(self, patient_name: str, report_text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save a report to disk and return the file path."""
        safe_patient = self._safe_name(patient_name or "unknown") or "unknown"
        patient_dir = os.path.join(self.reports_dir, safe_patient)
        os.makedirs(patient_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(patient_dir, f"report_{timestamp}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        # Save sidecar metadata
        if metadata:
            meta_path = report_path + ".meta.json"
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(metadata, mf, indent=2, default=str)
        return report_path

    def list_reports(self, patient_name: str) -> List[str]:
        safe_patient = self._safe_name(patient_name or "unknown") or "unknown"
        patient_dir = os.path.join(self.reports_dir, safe_patient)
        if not os.path.isdir(patient_dir):
            return []
        files = [os.path.join(patient_dir, f) for f in os.listdir(patient_dir) if f.endswith('.md')]
        return sorted(files, reverse=True)

    def load_report(self, path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def save_json(self, name: str, data: Dict[str, Any]) -> str:
        safe = self._safe_name(name or "data") or "data"
        path = os.path.join(self.json_dir, f"{safe}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def load_json(self, name: str) -> Optional[Dict[str, Any]]:
        safe = self._safe_name(name or "data") or "data"
        path = os.path.join(self.json_dir, f"{safe}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
