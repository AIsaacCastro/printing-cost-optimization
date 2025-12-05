# Test Data Generator Documentation

## Overview

The `generate_test_data.py` script creates realistic large-scale test data for performance testing the printing cost optimization system.

## Quick Start

```bash
python generate_test_data.py
```

This generates data in `data/test_large/` with:
- 5,000 books
- 20 suppliers
- 200 kits
- 50 brands
- ~216,200 cost entries

## Generated Data Characteristics

### Books (5,000)

**Production Volumes** (realistic distribution):
- 70% medium runs: 1,000-5,000 copies
- 20% small runs: 100-1,000 copies
- 10% large runs: 5,000-10,000 copies

**Printing Methods** (volume-dependent):
- Small volumes (<1,000): Prefer digital
  - `["digital"]` or `["digital", "hybrid"]`
- Medium volumes (1,000-5,000): Both methods
  - `["offset", "digital"]` or `["offset", "digital", "hybrid"]`
- Large volumes (>5,000): Prefer offset
  - `["offset"]` or `["offset", "hybrid"]`

**Attributes**:
- Unique IDs: `B00001` to `B05000`
- Titles: Combination of prefix + topic (e.g., "Mastering Machine Learning")
- 50 brands distributed evenly
- ~14% of books assigned to kits (686 out of 5,000)

### Kits (200)

**Characteristics**:
- Each kit contains 2-5 books
- Books randomly selected (no overlaps between kits)
- Kit names based on brand + collection number
- IDs: `K0001` to `K0200`

**Purpose**: Tests kit cohesion constraint (all books in kit must go to same supplier)

### Suppliers (20)

**Capacities** (per printing method):
- **Offset**: 50,000-150,000 copies per supplier
  - Total capacity: ~2,000,000 copies
- **Digital**: 20,000-80,000 copies per supplier
  - Total capacity: ~950,000 copies
- **Hybrid**: 10,000-40,000 copies per supplier
  - Total capacity: ~567,000 copies

**Names**: Combination of prefix + suffix (e.g., "Premium Print Solutions")

**IDs**: `S001` to `S020`

### Costs (216,200 entries)

**Pricing Structure** (per unit):

**Offset Printing**:
- Small volumes (<1,000): $3.00-$4.50
- Medium volumes (1,000-5,000): $2.00-$3.00
- Large volumes (>5,000): $1.50-$2.50

**Digital Printing**:
- Consistent across volumes: $2.50-$3.50

**Hybrid Printing**:
- Small volumes (<2,000): $2.80-$3.80
- Large volumes (>2,000): $2.20-$3.20

**Supplier Variation**: ±15% cost variation per supplier (based on hash)

## Customization

Edit the configuration constants at the top of `generate_test_data.py`:

```python
# Configuration
NUM_BOOKS = 5000              # Number of books to generate
NUM_SUPPLIERS = 20            # Number of suppliers
NUM_BRANDS = 50               # Number of brands
NUM_KITS = 200                # Number of kits
BOOKS_PER_KIT_MIN = 2         # Minimum books per kit
BOOKS_PER_KIT_MAX = 5         # Maximum books per kit
PRINTING_METHODS = ["offset", "digital", "hybrid"]
```

### Example Customizations

**Extra Large Dataset** (10,000 books, 50 suppliers):
```python
NUM_BOOKS = 10000
NUM_SUPPLIERS = 50
NUM_BRANDS = 100
NUM_KITS = 500
```

**Small Test Set** (500 books, 5 suppliers):
```python
NUM_BOOKS = 500
NUM_SUPPLIERS = 5
NUM_BRANDS = 20
NUM_KITS = 20
```

**Two-Method Only** (offset and digital):
```python
PRINTING_METHODS = ["offset", "digital"]
```

## Data Validation

The generated data is validated during creation to ensure:
- All books have at least one valid printing method
- All cost entries reference existing books, suppliers, and methods
- Printing methods in costs match book's available methods
- Kit books all exist and no book appears in multiple kits
- Brand distribution is realistic

## Performance Characteristics

**Total Production Volume**: ~14.6 million copies
- Tests capacity constraint optimization
- Ensures realistic supplier utilization

**Method Distribution**:
- Offset: ~4,300 books (86% of total volume)
- Digital: ~4,700 books (but lower volume per book)
- Hybrid: ~1,800 books (specialty cases)

**Capacity Constraints**:
- Total volume (14.6M) significantly exceeds total capacity (~3.5M)
- Forces optimizer to make hard choices
- Tests infeasibility detection if capacity too low

## Expected Optimization Results

With this dataset:
- **Solve Time**: 1-5 minutes (varies by hardware)
- **Solution Quality**: Optimal or near-optimal (gap <1%)
- **Cost Savings**: 10-25% vs. naive assignment
- **Utilization**: High utilization of offset capacity (~90-100%)
- **Method Selection**: Majority of large volumes → offset, small → digital

## Troubleshooting

**Issue**: "Books without cost data" error
- **Cause**: Mismatch between available methods and cost entries
- **Fix**: Regenerate data (costs auto-generated for all valid combinations)

**Issue**: Solver reports INFEASIBLE
- **Cause**: Total capacity < total volume
- **Fix**: Increase supplier capacities or reduce production volumes

**Issue**: Very slow solve time (>30 minutes)
- **Cause**: Dataset too large or many symmetries
- **Fix**: Reduce NUM_BOOKS or enable symmetry_breaking in config

## Output Files

After running `generate_test_data.py`:

```
data/test_large/
├── books.json           # Book definitions
├── kits.json            # Kit definitions
├── suppliers.json       # Supplier capacities
├── costs.csv           # Cost matrix
└── config.json         # Solver configuration
```

## Running Optimization

```bash
# Linux/Mac
python -m src.optimizer.cli solve \
    --books data/test_large/books.json \
    --kits data/test_large/kits.json \
    --suppliers data/test_large/suppliers.json \
    --costs data/test_large/costs.csv \
    --config data/test_large/config.json \
    --output results/solution_large.json

# Windows
python -m src.optimizer.cli solve --books data/test_large/books.json --kits data/test_large/kits.json --suppliers data/test_large/suppliers.json --costs data/test_large/costs.csv --config data/test_large/config.json --output results/solution_large.json
```

## Reproducibility

The script uses a fixed random seed (`random.seed(42)`), ensuring:
- Same data generated on each run
- Reproducible performance benchmarks
- Consistent testing environment

To generate different data, change the seed:
```python
random.seed(12345)  # Different seed = different data
```
