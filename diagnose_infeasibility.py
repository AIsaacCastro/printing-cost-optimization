"""
Diagnose why the optimization problem is infeasible
"""

import json
import csv
from collections import defaultdict

# Load data
print("="*80)
print("INFEASIBILITY DIAGNOSIS")
print("="*80)

with open('data/test_large/books.json', 'r') as f:
    books = json.load(f)

with open('data/test_large/kits.json', 'r') as f:
    kits = json.load(f)

with open('data/test_large/suppliers.json', 'r') as f:
    suppliers = json.load(f)

with open('data/test_large/config.json', 'r') as f:
    config = json.load(f)

print(f"\nData Summary:")
print(f"  Books: {len(books)}")
print(f"  Kits: {len(kits)}")
print(f"  Suppliers: {len(suppliers)}")
print(f"  Max items per brand per supplier: {config['max_volumes_per_brand_per_supplier']}")

# Build maps
book_map = {book['id']: book for book in books}
kit_map = {kit['id']: kit for kit in kits}

# 1. CHECK CAPACITY
print("\n" + "="*80)
print("1. CAPACITY ANALYSIS")
print("="*80)

# Calculate total production volume by method
total_volume_by_method = defaultdict(int)
for book in books:
    # For this analysis, assume each book could use any of its available methods
    for method in book['available_printing_methods']:
        total_volume_by_method[method] += book['production_volume']

# Calculate total supplier capacity by method
total_capacity_by_method = defaultdict(int)
for supplier in suppliers:
    for method, capacity in supplier['capacities'].items():
        total_capacity_by_method[method] += capacity

print("\nIf all books used the same method:")
for method in sorted(total_volume_by_method.keys()):
    demand = total_volume_by_method[method]
    capacity = total_capacity_by_method[method]
    ratio = demand / capacity if capacity > 0 else float('inf')
    status = "[OK]" if demand <= capacity else "[VIOLATION]"
    print(f"  {method:12s}: Demand={demand:,} vs Capacity={capacity:,} (ratio={ratio:.2f}) {status}")

# Calculate actual minimum volume needed
min_volume_needed = sum(book['production_volume'] for book in books)
max_capacity = max(total_capacity_by_method.values())
print(f"\nMinimum volume needed: {min_volume_needed:,}")
print(f"Maximum capacity (any single method): {max_capacity:,}")
print(f"Capacity sufficient: {'Yes' if min_volume_needed <= max_capacity else 'No'}")

# 2. CHECK BRAND DISTRIBUTION
print("\n" + "="*80)
print("2. BRAND DISTRIBUTION ANALYSIS")
print("="*80)

# Count brands
books_by_brand = defaultdict(list)
for book in books:
    books_by_brand[book['brand']].append(book['id'])

# Count kits and standalone books per brand
brand_items = {}
for brand, book_ids in books_by_brand.items():
    kits_with_brand = set()
    standalone_books = []

    for book_id in book_ids:
        book = book_map[book_id]
        if book.get('kit_id'):
            kits_with_brand.add(book['kit_id'])
        else:
            standalone_books.append(book_id)

    brand_items[brand] = {
        'kits': len(kits_with_brand),
        'standalone': len(standalone_books),
        'total_items': len(kits_with_brand) + len(standalone_books),
        'total_books': len(book_ids)
    }

print(f"\nBrands: {len(books_by_brand)}")
print(f"Suppliers: {len(suppliers)}")
print(f"Max items per brand per supplier: {config['max_volumes_per_brand_per_supplier']}")

# Check if any brand has more items than can be distributed
max_items_per_supplier = config['max_volumes_per_brand_per_supplier']
total_slots_available_per_brand = max_items_per_supplier * len(suppliers)

print(f"\nSlots available per brand across all suppliers: {total_slots_available_per_brand}")
print("  (= {max_items} items/supplier × {num_suppliers} suppliers)".format(
    max_items=max_items_per_supplier,
    num_suppliers=len(suppliers)
))

violations = []
for brand in sorted(brand_items.keys()):
    items = brand_items[brand]
    if items['total_items'] > total_slots_available_per_brand:
        violations.append(brand)
        status = "[VIOLATION]"
    else:
        status = "[OK]"

    print(f"\n  {brand}:")
    print(f"    Items (kits + standalone): {items['total_items']} (needs {items['total_items']} slots, {total_slots_available_per_brand} available) {status}")
    print(f"    Breakdown: {items['kits']} kits + {items['standalone']} standalone books")
    print(f"    Total books in this brand: {items['total_books']}")

if violations:
    print("\n" + "="*80)
    print("BRAND CONSTRAINT VIOLATIONS DETECTED")
    print("="*80)
    print(f"\nThe following brands have MORE items than available slots:")
    for brand in violations:
        items = brand_items[brand]
        print(f"  {brand}: {items['total_items']} items > {total_slots_available_per_brand} slots")
    print(f"\nThis makes the problem INFEASIBLE!")
    print(f"\nPossible solutions:")
    print(f"  1. Increase max_volumes_per_brand_per_supplier (currently {max_items_per_supplier})")
    print(f"  2. Add more suppliers (currently {len(suppliers)})")
    print(f"  3. Reduce the number of items per brand")
    print(f"  4. Combine more books into kits (since kits count as 1 item)")

# 3. CHECK COST COVERAGE
print("\n" + "="*80)
print("3. COST COVERAGE ANALYSIS")
print("="*80)

# Load costs
costs = {}
with open('data/test_large/costs.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['book_id'], row['supplier_id'], row['printing_method'])
        costs[key] = float(row['unit_cost'])

print(f"Total cost entries: {len(costs)}")

# Check if every book has at least one valid (supplier, method) combination
books_without_costs = []
for book in books:
    has_valid_combo = False
    for supplier in suppliers:
        for method in book['available_printing_methods']:
            if (book['id'], supplier['id'], method) in costs:
                # Also check if supplier has capacity for this method
                if method in supplier['capacities']:
                    has_valid_combo = True
                    break
        if has_valid_combo:
            break

    if not has_valid_combo:
        books_without_costs.append(book['id'])

if books_without_costs:
    print(f"\n[VIOLATION] Books without valid (supplier, method) combinations: {len(books_without_costs)}")
    print(f"  Examples: {', '.join(books_without_costs[:10])}")
else:
    print("\n[OK] All books have at least one valid (supplier, method) combination")

# 4. SUMMARY
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if violations:
    print("\nPROBLEM IS INFEASIBLE DUE TO BRAND CONSTRAINT")
    print(f"\n{len(violations)} brand(s) have more items than can be distributed across suppliers.")
    print(f"\nRecommended fix: Increase 'max_volumes_per_brand_per_supplier' from {max_items_per_supplier} to at least {max(brand_items[b]['total_items'] for b in violations) // len(suppliers) + 1}")
elif books_without_costs:
    print("\nPROBLEM MAY BE INFEASIBLE DUE TO MISSING COSTS")
    print(f"\n{len(books_without_costs)} book(s) don't have valid (supplier, method) combinations")
else:
    print("\nNo obvious infeasibility detected in capacity or brand constraints.")
    print("The problem may be infeasible due to a complex interaction of constraints.")
    print("\nTry:")
    print("  1. Relaxing the brand constraint")
    print("  2. Adding more supplier capacity")
    print("  3. Checking kit cohesion constraints with available methods")

print()
