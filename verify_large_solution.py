"""
Verify brand constraint in large dataset solution
"""

import json
from collections import defaultdict

# Load data
with open('data/test_large/books.json', 'r') as f:
    books = json.load(f)

with open('data/test_large/kits.json', 'r') as f:
    kits = json.load(f)

with open('data/test_large/config.json', 'r') as f:
    config = json.load(f)

with open('results/solution_large.json', 'r') as f:
    solution = json.load(f)

# Build maps
book_map = {book['id']: book for book in books}
kit_map = {kit['id']: kit for kit in kits}

# Build assignment map
assignments = {
    assignment['book_id']: assignment['supplier_id']
    for assignment in solution['assignments']
}

# Build books by brand
books_by_brand = defaultdict(list)
for book in books:
    books_by_brand[book['brand']].append(book['id'])

# Count items per brand per supplier
brand_supplier_items = defaultdict(lambda: defaultdict(set))
processed_kits = set()

for book in books:
    book_id = book['id']
    brand = book['brand']
    supplier = assignments.get(book_id)

    if supplier:
        if book.get('kit_id'):
            kit_id = book['kit_id']
            if kit_id not in processed_kits:
                brand_supplier_items[brand][supplier].add(('kit', kit_id))
                processed_kits.add(kit_id)
        else:
            brand_supplier_items[brand][supplier].add(('book', book_id))

# Verify constraint
max_items = config['max_volumes_per_brand_per_supplier']
violations = []
max_usage = 0

print("="*80)
print(f"BRAND CONSTRAINT VERIFICATION (max={max_items} items per brand per supplier)")
print("="*80)

for brand in sorted(brand_supplier_items.keys()):
    print(f"\n{brand}:")
    suppliers_data = brand_supplier_items[brand]

    for supplier in sorted(suppliers_data.keys()):
        items = suppliers_data[supplier]
        num_items = len(items)
        max_usage = max(max_usage, num_items)

        num_kits = sum(1 for item_type, _ in items if item_type == 'kit')
        num_books = sum(1 for item_type, _ in items if item_type == 'book')

        status = "[OK]" if num_items <= max_items else "[VIOLATION]"
        print(f"  {supplier}: {num_items}/{max_items} items ({num_kits} kits + {num_books} standalone) {status}")

        if num_items > max_items:
            violations.append({
                'brand': brand,
                'supplier': supplier,
                'items': num_items,
                'limit': max_items
            })

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Max items allowed per brand per supplier: {max_items}")
print(f"Max items actually used: {max_usage}")
print(f"Constraint headroom: {max_items - max_usage} items")

if violations:
    print(f"\n[VIOLATION] Found {len(violations)} violation(s)!")
    for v in violations:
        print(f"  {v['brand']} at {v['supplier']}: {v['items']} > {v['limit']}")
else:
    print("\n[OK] All brand constraints satisfied!")
    print(f"All {len(brand_supplier_items)} brands comply with the constraint.")

print("="*80)
