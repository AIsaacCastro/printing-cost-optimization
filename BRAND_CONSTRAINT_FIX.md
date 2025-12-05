# Brand Constraint Fix Summary

## Problem

The original brand diversification constraint was counting **individual books** instead of **kits**. This meant that a kit with 3 books from the same brand would count as 3 items toward the limit, rather than 1 item.

## The Requirement

**Constraint**: Maximum 4 **items** (kits or standalone books) per brand per supplier

**Key Rule**: A kit with N books counts as **1 item**, not N items.

### Example

If a brand has:
- Kit K1 with 3 books (B1, B2, B3)
- Kit K2 with 2 books (B4, B5)
- Standalone book B6

And all are assigned to Supplier S1, this counts as **3 items** (2 kits + 1 standalone book), NOT 6 books.

## Solution

### Code Changes

**File**: `src/optimizer/solver.py`
**Function**: `_add_brand_diversification_constraints()`

The constraint was completely rewritten to:

1. **Identify kits by brand**: For each brand-supplier combination, find all kits that contain books from that brand
2. **Create kit indicators**: One boolean variable per kit that's set to 1 if the kit is assigned to the supplier
3. **Create book indicators**: One boolean variable per standalone book that's set to 1 if assigned to the supplier
4. **Apply constraint**: `sum(kit_indicators) + sum(standalone_book_indicators) ≤ max_kits`

### Key Implementation Details

```python
# For each brand-supplier combination
for brand, book_ids in self.books_by_brand.items():
    for supplier in self.data.suppliers:
        # Separate kits from standalone books
        kits_with_brand = set()
        standalone_books = []

        for book_id in book_ids:
            book = self.book_map[book_id]
            if book.kit_id:
                kits_with_brand.add(book.kit_id)  # Track kit, not individual books
            else:
                standalone_books.append(book_id)

        items_to_count = []

        # Each kit counts as 1 item (regardless of number of books)
        for kit_id in kits_with_brand:
            kit_to_supplier = self.model.NewBoolVar(...)
            # Link to first book in kit (representative)
            items_to_count.append(kit_to_supplier)

        # Each standalone book counts as 1 item
        for book_id in standalone_books:
            book_to_supplier = self.model.NewBoolVar(...)
            items_to_count.append(book_to_supplier)

        # Constraint: total items ≤ max_kits
        if items_to_count:
            self.model.Add(sum(items_to_count) <= max_kits)
```

## Documentation Updates

Updated the following files to reflect the correct constraint:

1. **src/optimizer/models.py** - `OptimizationConfig` description
2. **README.md** - Constraint descriptions
3. **CLAUDE.md** - Constraint formulation
4. **data/example_config.json** - Added explanatory comment

## Verification

### Verification Script

Created `verify_brand_constraint.py` to validate the constraint is satisfied in solutions.

### Verification Results (Example Data)

```
CloudTech:
  S004: 1 items (1 kits + 0 standalone books) [OK]
    - Kit K003: 3 books (B009, B010, B011)

DataScience:
  S003: 3 items (0 kits + 3 standalone books) [OK]
    - Book B006, B007, B008

TechBooks:
  S003: 1 items (1 kits + 0 standalone books) [OK]
    - Kit K001: 3 books (B001, B002, B003)

WebDev:
  S001: 2 items (0 kits + 2 standalone books) [OK]
  S002: 1 items (1 kits + 0 standalone books) [OK]
```

**Key Observations**:
- TechBooks Kit K001 with **3 books** counts as **1 item** ✓
- CloudTech Kit K003 with **3 books** counts as **1 item** ✓
- DataScience has **3 standalone books** = **3 items** ✓
- All constraints satisfied (≤ 4 items per brand per supplier) ✓

## Testing

Run verification on any solution:
```bash
python verify_brand_constraint.py
```

This script:
- Loads books, kits, and solution data
- Counts items (kits + standalone books) per brand per supplier
- Verifies no brand exceeds the configured limit
- Provides detailed breakdown of assignments

## Status

✅ **COMPLETE** - The brand constraint now correctly counts kits as single items, regardless of the number of books they contain.
