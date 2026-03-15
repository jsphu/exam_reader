import json
import os
import logging

logger = logging.getLogger("exam_reader")

def load_previous_results(file_path):
    """Loads previous results from a JSON file."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load previous results: {e}")
    return {}

def save_current_results(file_path, results):
    """Saves current results to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Could not save current results: {e}")

def compare_results(current_results, previous_results):
    """
    Compares current results with previous results and identifies changes.
    Returns a list of change descriptions.
    """
    changes = []
    
    # previous_results is expected to be a dict mapping course_name to match_data
    # current_results is a list of dicts (matches)
    
    current_dict = {f"{m['course']} (Sem {m['semester']})": m for m in current_results if m.get('course')}
    
    # Check for changes in existing courses
    for course_id, current_match in current_dict.items():
        if course_id in previous_results:
            prev_match = previous_results[course_id]
            course_changes = []
            
            # Look for date, day and hour changes
            fields_to_check = ['date', 'day', 'time', 'date_makeup']
            for field in fields_to_check:
                curr_val = current_match.get(field, "")
                prev_val = prev_match.get(field, "")
                if curr_val != prev_val:
                    course_changes.append(f"{field}: {prev_val} -> {curr_val}")
            
            if course_changes:
                changes.append(f"CHANGED: {course_id}\n  " + "\n  ".join(course_changes))
        else:
            changes.append(f"NEW EXAM ADDED: {course_id}")
            
    # Check for removed courses
    for course_id in previous_results:
        if course_id not in current_dict:
            changes.append(f"REMOVED: {course_id}")
            
    return changes, current_dict
