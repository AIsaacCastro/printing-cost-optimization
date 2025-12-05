"""
Verify brand constraint in optimization solution

Validates that no brand has more than max_volumes_per_brand_per_supplier
items (kits or standalone books) per supplier.
"""

import json
from collections import defaultdict
from pathlib import Path


def verify_brand_constraint(
    books_path: str,
    kits_path: str,
    solution_path: str,
    max_items_per_brand: int = 4
):
    """
    Verify the brand diversification constraint

    Args:
        books_path: Path to books JSON file
        kits_path: Path to kits JSON file
        solution_path: Path to solution JSON file
        max_items_per_brand: Maximum items (kits or standalone books) per brand per supplier
    """
    # Load data
    with open(books_path, 'r') as f:
        books = json.load(f)

    with open(kits_path, 'r') as f:
        kits = json.load(f)

    with open(solution_path, 'r') as f:
        solution = json.load(f)

    # Build book and kit maps
    book_map = {book['id']: book for book in books}
    kit_map = {kit['id']: kit for kit in kits}

    # Build assignment map: book_id -> supplier_id
    assignments = {
        assignment['book_id']: assignment['supplier_id']
        for assignment in solution['assignments']
    }

    # Count items (kits + standalone books) per brand per supplier
    brand_supplier_items = defaultdict(lambda: defaultdict(set))

    # Track which kits have been processed
    processed_kits = set()

    for book in books:
        book_id = book['id']
        brand = book['brand']
        supplier = assignments.get(book_id)

        if supplier:
            if book['kit_id']:
                # This book is in a kit
                kit_id = book['kit_id']
                if kit_id not in processed_kits:
                    # Add kit as one item (regardless of number of books)
                    brand_supplier_items[brand][supplier].add(('kit', kit_id))
                    processed_kits.add(kit_id)
            else:
                # Standalone book - each counts as one item
                brand_supplier_items[brand][supplier].add(('book', book_id))

    # Verify constraint and prepare report
    print("="*80)
    print("BRAND CONSTRAINT VERIFICATION")
    print("="*80)
    print(f"Maximum items per brand per supplier: {max_items_per_brand}")
    print(f"(Note: A kit with N books counts as 1 item, not N items)\n")

    violations = []

    for brand in sorted(brand_supplier_items.keys()):
        print(f"\n{brand}:")
        suppliers_data = brand_supplier_items[brand]

        for supplier in sorted(suppliers_data.keys()):
            items = suppliers_data[supplier]
            num_items = len(items)

            # Count kits and standalone books
            num_kits = sum(1 for item_type, _ in items if item_type == 'kit')
            num_books = sum(1 for item_type, _ in items if item_type == 'book')

            status = "[OK]" if num_items <= max_items_per_brand else "[VIOLATION]"

            print(f"  {supplier}: {num_items} items ({num_kits} kits + {num_books} standalone books) {status}")

            # Show details
            for item_type, item_id in sorted(items):
                if item_type == 'kit':
                    kit = kit_map[item_id]
                    num_books_in_kit = len(kit['book_ids'])
                    print(f"    - Kit {item_id}: {num_books_in_kit} books ({', '.join(kit['book_ids'])})")
                else:
                    book = book_map[item_id]
                    print(f"    - Book {item_id}: {book['title']}")

            if num_items > max_items_per_brand:
                violations.append({
                    'brand': brand,
                    'supplier': supplier,
                    'items': num_items,
                    'limit': max_items_per_brand
                })

    # Summary
    print("\n" + "="*80)
    if violations:
        print("CONSTRAINT VIOLATIONS DETECTED:")
        print("="*80)
        for v in violations:
            print(f"  {v['brand']} at {v['supplier']}: {v['items']} items (limit: {v['limit']})")
        print("\nVERIFICATION FAILED [X]")
    else:
        print("VERIFICATION SUCCESSFUL [OK]")
        print("="*80)
        print("All brand constraints are satisfied!")
        print("No brand has more than {} items (kits or standalone books) per supplier.".format(
            max_items_per_brand
        ))

    print()

    return len(violations) == 0


if __name__ == "__main__":
    # Verify example solution
    print("Verifying example solution...\n")
    success = verify_brand_constraint(
        books_path="data/example_books.json",
        kits_path="data/example_kits.json",
        solution_path="results/solution.json",
        max_items_per_brand=4
    )

    exit(0 if success else 1)
