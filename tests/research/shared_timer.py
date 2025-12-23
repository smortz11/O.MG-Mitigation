"""
tests/research/shared_timer.py

Shared timing logger for latency measurements
Both SENDER and ENDPOINT log timestamps to correlate later
"""

import time
import json
from pathlib import Path

class SharedTimer:
    def __init__(self, device_name, log_file='tests/research/results/timing_log.jsonl'):
        """
        Initialize timer for a device
        
        Args:
            device_name: "SENDER" or "ENDPOINT"
            log_file: Path to shared log file
        """
        self.device = device_name
        self.log_file = log_file
        self.session_id = int(time.time() * 1000)  # Millisecond timestamp as session ID
        self.enabled = True
        
        # Create results directory if it doesn't exist
        Path('tests/research/results').mkdir(parents=True, exist_ok=True)
        
        # Clear log file at start of SENDER
        if device_name == "SENDER":
            Path(log_file).write_text("")
            print(f"[{device_name}] Timing log cleared: {log_file}")
        
        print(f"[{device_name}] Timing logger initialized (session: {self.session_id})")
    
    def log_event(self, event_type, key, metadata=None):
        """
        Log a timing event
        
        Args:
            event_type: "capture", "encrypt_send", "receive", "decrypt_inject"
            key: The key being processed (e.g., 'KEY_A', 'a', etc.)
            metadata: Optional dict with extra info
        
        Returns:
            timestamp (float): The perf_counter timestamp
        """
        if not self.enabled:
            return None
        
        timestamp = time.perf_counter()
        
        event = {
            'session': self.session_id,
            'device': self.device,
            'event': event_type,
            'key': str(key),
            'timestamp': timestamp,
            'wall_time': time.time(),
            'metadata': metadata or {}
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"[{self.device}] ERROR logging event: {e}")
        
        return timestamp
    
    def disable(self):
        """Stop logging events"""
        self.enabled = False
        print(f"[{self.device}] Timing logger disabled")
    
    def enable(self):
        """Resume logging events"""
        self.enabled = True
        print(f"[{self.device}] Timing logger enabled")
