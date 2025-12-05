"""
Utility script to export optimization results to CSV files

This demonstrates the use of the ResultExporter class
"""

import json
from pathlib import Path

from src.optimizer.data_loader import DataLoader
from src.optimizer.exporter import ResultExporter
from src.optimizer.models import OptimizationResult

# Load the problem data
data = DataLoader.load_problem_data(
    books_file="data/example_books.json",
    kits_file="data/example_kits.json",
    suppliers_file="data/example_suppliers.json",
    costs_file="data/example_costs.csv"
)

# Load the optimization results
with open("results/solution.json", "r") as f:
    result_dict = json.load(f)

result = OptimizationResult(**result_dict)

# Export to CSV files
output_dir = Path("results")
ResultExporter.generate_report(result, data, output_dir)

print(f"CSV reports generated successfully in {output_dir}/:")
print("  - assignments.csv")
print("  - supplier_summary.csv")
print("  - brand_distribution.csv")
