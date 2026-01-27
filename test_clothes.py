from convert_colors import _extract_function_region, load_upper_from_cpp, load_lower_from_cpp
from pathlib import Path

text = Path('ai.cpp').read_text(encoding='utf-8', errors='ignore')
upper_region = _extract_function_region(text, 'pickUpper')
lower_region = _extract_function_region(text, 'pickLower')

print('=== Checking for jeans ===')
print(f'jeans in pickUpper region: {"jeans" in upper_region.lower()}')
print(f'jeans in pickLower region: {"jeans" in lower_region.lower()}')

UPPER = load_upper_from_cpp()
LOWER = load_lower_from_cpp()

upper_jeans = [item for item in UPPER if 'jeans' in item.lower()]
lower_jeans = [item for item in LOWER if 'jeans' in item.lower()]

print(f'\nUPPER items with jeans: {upper_jeans}')
print(f'LOWER items with jeans: {lower_jeans}')

# Check for duplicates
upper_set = set(i.lower() for i in UPPER)
lower_set = set(i.lower() for i in LOWER)
duplicates = upper_set & lower_set
print(f'\nDuplicate items in both lists: {sorted(duplicates)}')
