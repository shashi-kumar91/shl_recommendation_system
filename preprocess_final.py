#!/usr/bin/env python3
"""
FIXED preprocessing - Corrects URL format and test type codes
"""
import argparse
import json
import re
from typing import Any, Dict, List, Optional


def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean and normalize text."""
    if not text:
        return None
    text = re.sub(r'we recommend upgrading.*?(?=key features|$)', '', text, flags=re.I | re.S)
    text = re.sub(r'\s+', ' ', text.strip())
    return text if text else None


def fix_url(url: str) -> str:
    """
    CRITICAL FIX: Convert URLs to match Train_file.csv format.
    
    Train format: https://www.shl.com/solutions/products/product-catalog/view/XXX/
    Scraper format: https://www.shl.com/products/product-catalog/view/XXX/
    
    Must add /solutions/ before /products/
    """
    url = url.strip().lower()
    
    # Case 1: Missing /solutions/products/ entirely
    if '/product-catalog/view/' in url and '/products/product-catalog/' not in url:
        url = url.replace('/product-catalog/', '/solutions/products/product-catalog/')
    
    # Case 2: Has /products/ but missing /solutions/
    elif '/products/product-catalog/' in url and '/solutions/products/' not in url:
        url = url.replace('/products/product-catalog/', '/solutions/products/product-catalog/')
    
    # Ensure trailing slash
    if not url.endswith('/'):
        url += '/'
    
    return url


def parse_duration_to_minutes(duration_str: Optional[str]) -> Optional[int]:
    """Convert duration string to minutes (integer)."""
    if not duration_str:
        return None
    
    duration_lower = duration_str.lower()
    
    # Try various patterns
    patterns = [
        (r'(\d+)\s*-\s*(\d+)\s*(?:min|minute)', 'range_min'),
        (r'(\d+)\s*(?:min|minute)', 'single_min'),
        (r'(\d+(?:\.\d+)?)\s*(?:hour|hr)', 'hour'),
    ]
    
    for pattern, type_ in patterns:
        match = re.search(pattern, duration_lower, re.I)
        if match:
            if type_ == 'range_min':
                # Take average of range
                lo, hi = int(match.group(1)), int(match.group(2))
                return (lo + hi) // 2
            elif type_ == 'single_min':
                return int(match.group(1))
            elif type_ == 'hour':
                hours = float(match.group(1))
                return int(hours * 60)
    
    return None


def normalize_test_types(test_types: Any) -> List[str]:
    """
    CRITICAL FIX: Return SHL test type CODES (A, B, C, D, E, K, P, S)
    NOT readable names like 'Technical', 'Cognitive'
    
    Per assignment PDF:
    - A: Ability & Aptitude
    - B: Biodata & Situational Judgement
    - C: Competencies (Cognitive)
    - D: Development
    - E: Exercise
    - K: Knowledge & Skills
    - P: Personality & Behavior
    - S: Simulation
    """
    if not test_types:
        return ['General']
    
    if isinstance(test_types, str):
        test_types = [test_types]
    
    if not isinstance(test_types, list):
        return ['General']
    
    # Keep codes as-is, convert readable names to codes
    code_mapping = {
        'technical': 'K',
        'knowledge': 'K',
        'skills': 'K',
        'cognitive': 'C',
        'ability': 'A',
        'aptitude': 'A',
        'personality': 'P',
        'behavior': 'P',
        'behavioural': 'P',
        'development': 'D',
        'exercise': 'E',
        'simulation': 'S',
        'biodata': 'B',
        'situational': 'B'
    }
    
    result_codes = set()
    
    for t in test_types:
        t_clean = str(t).strip().upper()
        
        # If already a valid code, keep it
        if t_clean in ['A', 'B', 'C', 'D', 'E', 'K', 'P', 'S']:
            result_codes.add(t_clean)
        else:
            # Try to map from readable name
            t_lower = t.lower()
            for keyword, code in code_mapping.items():
                if keyword in t_lower:
                    result_codes.add(code)
                    break
    
    return sorted(list(result_codes)) if result_codes else ['General']


def is_individual_test(record: Dict) -> bool:
    """Exclude Pre-packaged Job Solutions."""
    url = record.get('url', '').lower()
    name = record.get('name', '').lower()
    desc = record.get('description', '').lower()
    
    exclude_keywords = [
        'solution', 'job focused', 'package', 'bundle',
        'pre-packaged', 'prepackaged', 'job-focused'
    ]
    
    # Exclude if name/URL contains solution patterns
    if any(kw in name for kw in ['solution', 'job-focused', 'job focused']):
        return False
    
    if 'solution' in url and 'solution' not in desc[:200]:
        return False
    
    return True


def preprocess_assessment(record: Dict) -> Optional[Dict]:
    """Process one assessment record."""
    
    # Check if individual test
    if not is_individual_test(record):
        return None
    
    name = record.get('name')
    url = record.get('url')
    
    if not name or not url:
        return None
    
    # CRITICAL: Fix URL to match training data format
    fixed_url = fix_url(url)
    
    return {
        'name': name.strip(),
        'url': fixed_url,
        'description': clean_text(record.get('description')) or name,
        'duration': parse_duration_to_minutes(record.get('duration')),
        'adaptive_support': bool(record.get('adaptive_support', False)),
        'remote_support': bool(record.get('remote_support', True)),
        'test_type': normalize_test_types(record.get('test_type'))
    }


def main():
    parser = argparse.ArgumentParser(description="FIXED SHL preprocessing")
    parser.add_argument("--input", default="assessments_raw.json", help="Raw scraper output")
    parser.add_argument("--output", default="preprocessed_assessments.json", help="Clean output")
    args = parser.parse_args()
    
    print("="*80)
    print("FIXED PREPROCESSING - URL & Test Type Correction")
    print("="*80)
    
    print(f"\nLoading raw data from {args.input}...")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {args.input} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {args.input}!")
        return
    
    print(f"Processing {len(data)} raw records...")
    
    processed = []
    skipped = 0
    url_fixes = 0
    
    for record in data:
        result = preprocess_assessment(record)
        if result:
            # Check if URL was fixed
            if '/solutions/products/' in result['url'] and '/solutions/products/' not in record.get('url', ''):
                url_fixes += 1
            processed.append(result)
        else:
            skipped += 1
    
    print(f"\n✅ Preprocessing complete:")
    print(f"   Valid individual tests: {len(processed)}")
    print(f"   Skipped (packages/invalid): {skipped}")
    print(f"   URLs fixed: {url_fixes}")
    
    if not processed:
        print("\n❌ Error: No valid assessments!")
        return
    
    print(f"\nSaving {len(processed)} assessments to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("Sample preprocessed records:")
    print("="*80)
    
    for i, rec in enumerate(processed[:3], 1):
        print(f"\n{i}. {rec['name']}")
        print(f"   URL: {rec['url']}")
        print(f"   Duration: {rec['duration']} min" if rec['duration'] else "   Duration: N/A")
        print(f"   Types: {', '.join(rec['test_type'])}")
        print(f"   Description: {rec['description'][:80]}...")
    
    print("\n✅ Done! Now run recommendation engine.")


if __name__ == "__main__":
    main()