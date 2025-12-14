"""
Chart Utilities

Helper functions for processing chart data, especially Venn diagrams.
"""

from typing import List, Dict

# Map count words to numbers for "All N" patterns
COUNT_WORDS = {
    'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
    'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
}


def parse_set_name_to_sets(set_name: str) -> List[str]:
    """
    Parse a set_name like:
      - "UltraBook Pro 15"
      - "UltraBook Pro 15 & PowerStation Desktop"
      - "A & B & C"
      - "All Three" (fallback)
    Returns list of normalized set labels.
    """
    name = (set_name or "").strip()
    if not name:
        return []

    # Prefer explicit names joined by '&'
    if '&' in name:
        parts = [p.strip() for p in name.split('&')]
        return [p for p in parts if p]

    # Fallback: detect "All N" patterns. This is ambiguous without names,
    # so we return a synthetic label to avoid lying. Consumers can still render totals.
    lower = name.lower()
    if lower.startswith('all '):
        words = lower.split()
        if len(words) >= 2:
            nword = words[1]
            n = COUNT_WORDS.get(nword)
            if n:
                return [f'Set {i+1}' for i in range(n)]

    # Otherwise treat the whole string as a single set label
    return [name]


def venn_sets_from_rows(rows: List[Dict]) -> List[Dict]:
    """
    Convert rows with set_name/size into venn sets:
      [{ sets: [label,...], size: N, label?: original }]

    Args:
        rows: List of dicts with keys like 'set_name' and 'size'

    Returns:
        List of Venn set objects with 'sets' (list of labels) and 'size' (count)
    """
    results = []
    for row in rows or []:
        set_name = str(row.get('set_name', '') or '').strip()
        if not set_name:
            continue

        size_val = row.get('size', 0)
        try:
            size = int(size_val)
        except (ValueError, TypeError):
            # Handle numeric strings or None
            try:
                size = int(float(size_val))
            except (ValueError, TypeError):
                size = 0

        sets = parse_set_name_to_sets(set_name)
        if not sets:
            continue

        entry = {'sets': sets, 'size': size}

        # Preserve original label for display if needed
        # (when the parsed sets don't match the original name exactly)
        if len(sets) == 1 and sets[0] != set_name:
            entry['label'] = set_name
        elif len(sets) > 1:
            # For intersections, include the original label for clarity
            entry['label'] = set_name

        results.append(entry)

    return results
