import csv
import glob
import os
import statistics
import sys

# Define constants based on analysis goals
DATA_DIR = "data"  # Relative to where the script is run (joystick_control/)
STEERING_LEFT_THRESHOLD = -0.5
STEERING_RIGHT_THRESHOLD = 0.5
STEERING_STRAIGHT_THRESHOLD = 0.2
LOOKBACK_FRAMES = 5  # frames to look back to find the decision point

def load_data():
    # Find files in joystick_control/data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data")
    files = glob.glob(os.path.join(data_path, "record_data_*.csv"))
    
    if not files:
        print(f"No data files found in {data_path}")
        return []
        
    all_data = []
    print(f"Loading {len(files)} files...")
    for f in files:
        with open(f, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            file_data = []
            for row in reader:
                try:
                    # Convert to float
                    clean_row = {}
                    for k, v in row.items():
                        clean_row[k] = float(v)
                    file_data.append(clean_row)
                except ValueError:
                    continue # Skip header repetitions or bad data
            all_data.extend(file_data)
    
    print(f"Total rows loaded: {len(all_data)}")
    return all_data

def analyze_wall_following(data):
    """Analyze straight driving to find preferred wall distance"""
    left_distances = []
    
    for row in data:
        # If driving relatively straight and moving forward
        if abs(row['steering']) < STEERING_STRAIGHT_THRESHOLD and row['throttle'] > 0:
            # Filter out invalid sensor readings (max range or errors)
            if 0 < row['L2'] < 2000:
                left_distances.append(row['L2'])
                
    if not left_distances:
        return None
        
    return {
        'count': len(left_distances),
        'mean': statistics.mean(left_distances),
        'median': statistics.median(left_distances),
        'stdev': statistics.stdev(left_distances) if len(left_distances) > 1 else 0
    }

def analyze_turns(data, direction='left'):
    """Analyze what sensor values trigger a turn"""
    triggers = {
        'L2': [], 'L1': [], 'C': [], 'R1': [], 'R2': []
    }
    
    count = 0
    
    # We need to look at sequences
    for i in range(LOOKBACK_FRAMES, len(data)):
        current_steer = data[i]['steering']
        
        is_turn = False
        if direction == 'left' and current_steer < STEERING_LEFT_THRESHOLD:
            is_turn = True
        elif direction == 'right' and current_steer > STEERING_RIGHT_THRESHOLD:
            is_turn = True
            
        if is_turn:
            # Check if this is the START of a turn (previous few were not turning)
            # This helps identify the *trigger* condition
            prev_steer = [data[j]['steering'] for j in range(i-LOOKBACK_FRAMES, i)]
            if all(abs(s) < 0.4 for s in prev_steer): # Previous were not sharp turns
                # Capture sensor data from just before the turn (reaction time ~100-200ms)
                # Assuming 20Hz (50ms), 2-4 frames back is good.
                context = data[i-2] 
                
                # Filter noise
                if context['L2'] < 2000 and context['C'] < 2000:
                    triggers['L2'].append(context['L2'])
                    triggers['L1'].append(context['L1'])
                    triggers['C'].append(context['C'])
                    triggers['R1'].append(context['R1'])
                    triggers['R2'].append(context['R2'])
                    count += 1

    if count == 0:
        return None
        
    stats = {}
    for key in triggers:
        if triggers[key]:
            stats[key] = {
                'mean': statistics.mean(triggers[key]),
                'min': min(triggers[key]),
                'max': max(triggers[key])
            }
    stats['count'] = count
    return stats

def main():
    data = load_data()
    if not data:
        return

    print("\n--- Analysis Results ---")

    # 1. Wall Following (Target Distance)
    wf = analyze_wall_following(data)
    if wf:
        print(f"\n[Wall Following] (n={wf['count']})")
        print(f"  Preferred Left Wall Distance: {wf['mean']:.1f} mm (Median: {wf['median']:.1f})")
        print(f"  Standard Deviation: {wf['stdev']:.1f}")
        print("  -> Suggestion: Update TARGET_WALL_DISTANCE / TARGET_LEFT_DISTANCE")

    # 2. Left Turn Triggers
    lt = analyze_turns(data, 'left')
    if lt:
        print(f"\n[Left Turn Triggers] (n={lt['count']})")
        print(f"  Left (L2) Distance before turn: Mean={lt['L2']['mean']:.1f}, Max={lt['L2']['max']:.1f}")
        print(f"  FrontLeft (L1) Distance before turn: Mean={lt['L1']['mean']:.1f}, Max={lt['L1']['max']:.1f}")
        print(f"  Center (C) Distance before turn: Mean={lt['C']['mean']:.1f}")
        print("  -> Suggestion: Update CORNER_NO_WALL_DISTANCE / LEFT_CORNER_OPEN_THRESHOLD")
        print("     (Look for sudden increase in L/FL or open space)")

    # 3. Right Turn Triggers
    rt = analyze_turns(data, 'right')
    if rt:
        print(f"\n[Right Turn Triggers] (n={rt['count']})")
        print(f"  Center (C) Distance before turn: Mean={rt['C']['mean']:.1f}, Min={rt['C']['min']:.1f}")
        print(f"  FrontRight (R1) Distance before turn: Mean={rt['R1']['mean']:.1f}")
        print("  -> Suggestion: Update CORNER_FRONT_DISTANCE / FRONT_BLOCKED_THRESHOLD")
        print("     (Look for obstacles in C/FR)")

if __name__ == "__main__":
    main()
