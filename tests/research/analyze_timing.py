"""
tests/research/analyze_timing.py

Analyze timing log and calculate latencies
Run this after collecting timing data from SENDER and ENDPOINT
"""

import json
import statistics
from collections import defaultdict
from pathlib import Path

def load_timing_log(log_file='tests/research/results/timing_log.jsonl'):
    """Load all timing events from log file"""
    events = []
    
    if not Path(log_file).exists():
        print(f"ERROR: Log file not found: {log_file}")
        print("Make sure you ran run_sender_timed.py and run_endpoint_timed.py first")
        return events
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"WARNING: Skipping malformed line {line_num}: {e}")
    
    print(f"Loaded {len(events)} timing events")
    return events

def group_events_by_key(events):
    """
    Group events by key presses to match capture → send → receive → inject
    """
    # Separate by device
    sender_events = [e for e in events if e['device'] == 'SENDER']
    endpoint_events = [e for e in events if e['device'] == 'ENDPOINT']
    
    print(f"  SENDER events: {len(sender_events)}")
    print(f"  ENDPOINT events: {len(endpoint_events)}")
    
    # Match SENDER captures with ENDPOINT receives
    sender_captures = [e for e in sender_events if e['event'] == 'capture']
    sender_sends = [e for e in sender_events if e['event'] == 'encrypt_send']
    endpoint_receives = [e for e in endpoint_events if e['event'] == 'receive']
    endpoint_injects = [e for e in endpoint_events if e['event'] == 'decrypt_inject']
    
    print(f"\n  Captures: {len(sender_captures)}")
    print(f"  Sends: {len(sender_sends)}")
    print(f"  Receives: {len(endpoint_receives)}")
    print(f"  Injects: {len(endpoint_injects)}")
    
    # Match events in sequence (assume same order)
    min_length = min(len(sender_captures), len(sender_sends), 
                     len(endpoint_receives), len(endpoint_injects))
    
    matched_sequences = []
    for i in range(min_length):
        sequence = {
            'capture': sender_captures[i],
            'send': sender_sends[i],
            'receive': endpoint_receives[i],
            'inject': endpoint_injects[i]
        }
        matched_sequences.append(sequence)
    
    print(f"\nMatched {len(matched_sequences)} complete keystroke sequences")
    return matched_sequences

def calculate_latencies(sequences):
    """Calculate latency metrics from matched sequences"""
    latencies = []
    
    for seq in sequences:
        try:
            capture_ts = seq['capture']['timestamp']
            send_ts = seq['send']['timestamp']
            receive_ts = seq['receive']['timestamp']
            inject_ts = seq['inject']['timestamp']
            
            latency = {
                'key': seq['capture']['key'],
                'encryption_time_ms': (send_ts - capture_ts) * 1000,
                'transmission_time_ms': (receive_ts - send_ts) * 1000,
                'decryption_time_ms': (inject_ts - receive_ts) * 1000,
                'total_latency_ms': (inject_ts - capture_ts) * 1000,
                'timestamps': {
                    'capture': capture_ts,
                    'send': send_ts,
                    'receive': receive_ts,
                    'inject': inject_ts
                }
            }
            
            latencies.append(latency)
        except KeyError as e:
            print(f"WARNING: Incomplete sequence, missing {e}")
    
    return latencies

def calculate_statistics(latencies):
    """Calculate statistical measures from latency data"""
    if not latencies:
        return None
    
    total_latencies = [l['total_latency_ms'] for l in latencies]
    encryption_times = [l['encryption_time_ms'] for l in latencies]
    transmission_times = [l['transmission_time_ms'] for l in latencies]
    decryption_times = [l['decryption_time_ms'] for l in latencies]
    
    stats = {
        'count': len(latencies),
        'total_latency': {
            'mean': statistics.mean(total_latencies),
            'median': statistics.median(total_latencies),
            'stdev': statistics.stdev(total_latencies) if len(total_latencies) > 1 else 0,
            'min': min(total_latencies),
            'max': max(total_latencies),
            'p95': sorted(total_latencies)[int(len(total_latencies) * 0.95)] if len(total_latencies) > 20 else None
        },
        'encryption_overhead': {
            'mean': statistics.mean(encryption_times),
            'median': statistics.median(encryption_times)
        },
        'transmission_time': {
            'mean': statistics.mean(transmission_times),
            'median': statistics.median(transmission_times)
        },
        'decryption_overhead': {
            'mean': statistics.mean(decryption_times),
            'median': statistics.median(decryption_times)
        }
    }
    
    return stats

def print_results(stats):
    """Print formatted results for paper"""
    if not stats:
        print("\nNo statistics to display")
        return
    
    print("\n" + "="*70)
    print("LATENCY ANALYSIS RESULTS")
    print("="*70)
    print(f"\nTotal Keystrokes Analyzed: {stats['count']}")
    
    print(f"\n{'END-TO-END LATENCY (Physical Key Press → Virtual Keyboard)':-^70}")
    print(f"  Mean:             {stats['total_latency']['mean']:>8.2f} ms")
    print(f"  Median:           {stats['total_latency']['median']:>8.2f} ms")
    print(f"  Std Deviation:    {stats['total_latency']['stdev']:>8.2f} ms")
    print(f"  Min:              {stats['total_latency']['min']:>8.2f} ms")
    print(f"  Max:              {stats['total_latency']['max']:>8.2f} ms")
    if stats['total_latency']['p95']:
        print(f"  95th Percentile:  {stats['total_latency']['p95']:>8.2f} ms")
    
    print(f"\n{'BREAKDOWN BY COMPONENT':-^70}")
    print(f"  Encryption (SENDER):     {stats['encryption_overhead']['mean']:>8.2f} ms")
    print(f"  Transmission (USB):      {stats['transmission_time']['mean']:>8.2f} ms")
    print(f"  Decryption (ENDPOINT):   {stats['decryption_overhead']['mean']:>8.2f} ms")
    
    print("\n" + "="*70)
    print("\nFOR YOUR PAPER:")
    print(f"  Average latency: {stats['total_latency']['mean']:.2f} ms")
    print(f"  Standard deviation: {stats['total_latency']['stdev']:.2f} ms")
    print("="*70 + "\n")

def save_results(stats, latencies, output_file='tests/research/results/latency_results.json'):
    """Save results to JSON file"""
    results = {
        'statistics': stats,
        'individual_measurements': latencies
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: {output_file}")

def main():
    """Main analysis function"""
    print("Loading timing data...")
    events = load_timing_log()
    
    if not events:
        return
    
    print("\nGrouping events into keystroke sequences...")
    sequences = group_events_by_key(events)
    
    if not sequences:
        print("Could not match any complete keystroke sequences.")
        return
    
    print("\nCalculating latencies...")
    latencies = calculate_latencies(sequences)
    
    print("\nCalculating statistics...")
    stats = calculate_statistics(latencies)
    
    print_results(stats)
    save_results(stats, latencies)
    
    return stats, latencies

if __name__ == "__main__":
    main()
