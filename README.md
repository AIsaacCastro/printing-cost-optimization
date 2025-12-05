# Printing Cost Optimization

A Python-based optimization system for allocating books to printing suppliers while minimizing costs and respecting complex constraints.

## Problem Overview

This system solves a **constrained generalized assignment problem** for printing operations with:

- **Kit Cohesion**: Books in the same kit must be printed by the same supplier
- **Brand Diversification**: Maximum 4 volumes per brand per supplier
- **Capacity Constraints**: Supplier capacity varies by printing method (offset, digital, etc.)
- **Cost Minimization**: Find the optimal allocation that minimizes total printing costs

## Features

- ✅ CP-SAT solver using Google OR-Tools (free, high-performance)
- ✅ JSON/CSV data configuration
- ✅ Symmetry breaking for identical suppliers
- ✅ Detailed result reporting and export
- ✅ CLI with rich output formatting
- ✅ Data validation with Pydantic models

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd printing-cost-optimization
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start with Example Data

Run the optimizer with the provided example data:

```bash
python -m src.optimizer.cli solve \
    --books data/example_books.json \
    --kits data/example_kits.json \
    --suppliers data/example_suppliers.json \
    --costs data/example_costs.csv \
    --output results/solution.json
```

### Command Options

**Solve command:**
```bash
python -m src.optimizer.cli solve [OPTIONS]
```

Options:
- `--books, -b`: Path to books JSON file (required)
- `--kits, -k`: Path to kits JSON file (required)
- `--suppliers, -s`: Path to suppliers JSON file (required)
- `--costs, -c`: Path to costs CSV file (required)
- `--config`: Path to config JSON file (optional)
- `--output, -o`: Path to save results JSON (optional)
- `--verbose, -v`: Show detailed output (optional)

**Validate command:**

Validate data files without solving:
```bash
python -m src.optimizer.cli validate \
    --books data/example_books.json \
    --kits data/example_kits.json \
    --suppliers data/example_suppliers.json \
    --costs data/example_costs.csv
```

## Data Format

### Books (JSON)
```json
[
  {
    "id": "B001",
    "title": "Book Title",
    "brand": "BrandName",
    "production_volume": 5000,
    "printing_method": "offset",
    "kit_id": "K001"
  }
]
```

### Kits (JSON)
```json
[
  {
    "id": "K001",
    "name": "Kit Name",
    "book_ids": ["B001", "B002", "B003"]
  }
]
```

### Suppliers (JSON)
```json
[
  {
    "id": "S001",
    "name": "Supplier Name",
    "capacities": {
      "offset": 25000,
      "digital": 10000
    }
  }
]
```

### Costs (CSV)
```csv
book_id,supplier_id,unit_cost
B001,S001,2.50
B001,S002,2.75
```

### Configuration (JSON, optional)
```json
{
  "max_volumes_per_brand_per_supplier": 4,
  "solver_time_limit_seconds": 300,
  "num_search_workers": 8,
  "enable_symmetry_breaking": true
}
```

## Output

The solver produces:
- **Console output**: Summary statistics and assignment details
- **JSON results** (if `--output` specified): Complete solution data
- **CSV exports** (via exporter module): Detailed breakdowns

## Architecture

```
src/optimizer/
├── models.py         # Pydantic data models
├── data_loader.py    # Data loading and validation
├── solver.py         # CP-SAT optimization model
├── exporter.py       # Result export utilities
├── cli.py            # Command-line interface
└── __main__.py       # Module entry point
```

See [CLAUDE.md](CLAUDE.md) for detailed architectural guidance.

## Constraints Implemented

1. **Volume Uniformity**: Each book assigned to exactly one supplier
2. **Kit Cohesion**: All books in a kit go to the same supplier
3. **Brand Diversification**: Max 4 volumes per brand per supplier
4. **Capacity by Method**: Supplier capacity respected per printing method
5. **Symmetry Breaking**: Optimization for suppliers with identical characteristics

## Performance

Expected solution quality by problem scale:

| Problem Scale | Method | Expected Quality |
|---------------|--------|------------------|
| <200 books | CP-SAT | Optimal |
| 200-2000 books | CP-SAT | Optimal or gap <1% |
| 2000-10000 books | CP-SAT + LNS | Gap 1-5% |

## Development

### Running Tests
```bash
pytest tests/
```

### Project Structure
```
printing-cost-optimization/
├── data/               # Input data files
├── results/            # Output results
├── src/
│   └── optimizer/      # Main optimization package
├── tests/              # Unit tests
├── requirements.txt    # Python dependencies
├── CLAUDE.md          # AI assistant guidance
└── README.md          # This file
```

## License

See LICENSE file for details.

## References

- Google OR-Tools: https://developers.google.com/optimization
- CP-SAT Solver: https://developers.google.com/optimization/cp/cp_solver
