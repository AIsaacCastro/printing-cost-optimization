# Printing Cost Optimization

A Python-based optimization system for allocating books to printing suppliers while minimizing costs and respecting complex constraints.

## Problem Overview

This system solves a **constrained generalized assignment problem** for printing operations with **printing method optimization**. The solver simultaneously optimizes:

1. **Supplier Selection**: Which supplier should print each book
2. **Method Selection**: Which printing method to use (offset, digital, etc.)

Subject to these constraints:
- **Kit Cohesion**: Books in the same kit must be printed by the same supplier (but can use different methods)
- **Brand Diversification**: Maximum 4 volumes per brand per supplier
- **Capacity Constraints**: Supplier capacity varies by printing method
- **Cost Minimization**: Find the optimal (supplier, method) allocation that minimizes total printing costs

## Features

- ✅ **Printing method optimization**: Automatically selects the best printing method for each book
- ✅ **Multi-method support**: Books can support multiple printing methods with different costs
- ✅ CP-SAT solver using Google OR-Tools (free, high-performance)
- ✅ JSON/CSV data configuration
- ✅ Symmetry breaking for identical suppliers
- ✅ Detailed result reporting and export with method information
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

4. **Try it now!** Run the optimizer with example data:
```bash
# Linux/Mac
python -m src.optimizer.cli solve --books data/example_books.json --kits data/example_kits.json --suppliers data/example_suppliers.json --costs data/example_costs.csv --output results/solution.json --verbose

# Windows (same command, one line)
python -m src.optimizer.cli solve --books data/example_books.json --kits data/example_kits.json --suppliers data/example_suppliers.json --costs data/example_costs.csv --output results/solution.json --verbose
```

## Usage

### Quick Start with Example Data

Run the optimizer with the provided example data:

**Linux/Mac:**
```bash
python -m src.optimizer.cli solve \
    --books data/example_books.json \
    --kits data/example_kits.json \
    --suppliers data/example_suppliers.json \
    --costs data/example_costs.csv \
    --output results/solution.json \
    --verbose
```

**Windows:**
```bash
python -m src.optimizer.cli solve --books data/example_books.json --kits data/example_kits.json --suppliers data/example_suppliers.json --costs data/example_costs.csv --output results/solution.json --verbose
```

This will:
- Load the 15 example books with their available printing methods
- Optimize supplier and printing method selection
- Display detailed results with method choices
- Save the solution to `results/solution.json`
- Show expected savings of ~$300 compared to non-optimized method selection

**Expected Output:**
```
Printing Cost Optimization Solver

Loading data...
[OK] Loaded data successfully
  • Books: 15
  • Kits: 3
  • Suppliers: 4
  • Cost entries: 100

Building optimization model...
[OK] Model built successfully

Solving...
[Solver output...]

Results:
  • Status: OPTIMAL
  • Solve time: 0.10 seconds
  • Total cost: $140,960.00
  • Books assigned: 15
  • Total volume: 54,000

Assignments by Supplier:
[Detailed supplier assignments with printing methods...]

[OK] Results saved to results\solution.json
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
# Linux/Mac
python -m src.optimizer.cli validate \
    --books data/example_books.json \
    --kits data/example_kits.json \
    --suppliers data/example_suppliers.json \
    --costs data/example_costs.csv

# Windows
python -m src.optimizer.cli validate --books data/example_books.json --kits data/example_kits.json --suppliers data/example_suppliers.json --costs data/example_costs.csv
```

**Export CSV reports:**

After solving, export detailed CSV reports:
```bash
python export_results.py
```

This generates three CSV files in the `results/` directory:
- `assignments.csv` - Detailed book assignments with printing methods
- `supplier_summary.csv` - Supplier utilization and cost summary
- `brand_distribution.csv` - Brand distribution across suppliers

## Data Format

### Books (JSON)
```json
[
  {
    "id": "B001",
    "title": "Book Title",
    "brand": "BrandName",
    "production_volume": 5000,
    "available_printing_methods": ["offset", "digital"],
    "kit_id": "K001"
  }
]
```

**Note**: Books can support multiple printing methods. The optimizer will choose the best method for each book.

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
book_id,supplier_id,printing_method,unit_cost
B001,S001,offset,2.50
B001,S001,digital,3.20
B001,S002,offset,2.75
B001,S002,digital,3.00
```

**Note**: Each (book, supplier, printing_method) combination has its own cost. This allows the optimizer to choose the most cost-effective method.

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

1. **Volume Uniformity**: Each book assigned to exactly one (supplier, method) combination
2. **Kit Cohesion**: All books in a kit go to the same supplier (can use different methods)
3. **Brand Diversification**: Max 4 volumes per brand per supplier (regardless of method)
4. **Capacity by Method**: Supplier capacity respected per printing method
5. **Symmetry Breaking**: Optimization for suppliers with identical characteristics

## Key Design Features

### Printing Method Optimization

The optimizer makes **two decisions** for each book:
1. Which supplier to use
2. Which printing method to use

This is critical because:
- **Different methods have different costs**: Offset is typically cheaper for large volumes, digital for small volumes
- **Books may support multiple methods**: The same book can be printed offset or digital
- **Capacity varies by method**: Suppliers have different capacities for offset vs digital
- **Method selection impacts total cost**: Choosing the wrong method can significantly increase costs

### Example Optimization

Consider a book with 5,000 copies:
- **S001 Offset**: $2.50/unit = $12,500
- **S001 Digital**: $3.20/unit = $16,000
- **S002 Offset**: $2.75/unit = $13,750
- **S002 Digital**: $3.00/unit = $15,000

The optimizer will choose **S001 with Offset method** ($12,500) as the optimal solution.

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
