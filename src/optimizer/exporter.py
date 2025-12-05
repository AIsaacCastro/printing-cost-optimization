"""Result export and reporting utilities"""

import csv
from pathlib import Path
from typing import List, Dict

from .models import OptimizationResult, Assignment, ProblemData


class ResultExporter:
    """Export optimization results in various formats"""

    @staticmethod
    def export_assignments_csv(
        assignments: List[Assignment],
        output_file: Path,
        data: ProblemData
    ) -> None:
        """
        Export assignments to CSV file

        Args:
            assignments: List of book-to-supplier assignments
            output_file: Path to output CSV file
            data: Problem data for enrichment
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create book and supplier maps for enrichment
        book_map = {book.id: book for book in data.books}
        supplier_map = {supplier.id: supplier for supplier in data.suppliers}

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'book_id',
                'book_title',
                'brand',
                'kit_id',
                'supplier_id',
                'supplier_name',
                'production_volume',
                'printing_method',
                'unit_cost',
                'total_cost'
            ])
            writer.writeheader()

            for assignment in sorted(assignments, key=lambda a: (a.supplier_id, a.book_id)):
                book = book_map[assignment.book_id]
                supplier = supplier_map[assignment.supplier_id]

                writer.writerow({
                    'book_id': assignment.book_id,
                    'book_title': book.title,
                    'brand': book.brand,
                    'kit_id': book.kit_id or '',
                    'supplier_id': assignment.supplier_id,
                    'supplier_name': supplier.name,
                    'production_volume': assignment.production_volume,
                    'printing_method': assignment.printing_method,
                    'unit_cost': f"{assignment.unit_cost:.2f}",
                    'total_cost': f"{assignment.total_cost:.2f}"
                })

    @staticmethod
    def export_supplier_summary_csv(
        result: OptimizationResult,
        output_file: Path,
        data: ProblemData
    ) -> None:
        """
        Export supplier utilization summary to CSV

        Args:
            result: Optimization result
            output_file: Path to output CSV file
            data: Problem data
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        supplier_map = {supplier.id: supplier for supplier in data.suppliers}

        # Aggregate by supplier
        supplier_stats: Dict[str, Dict] = {}

        for assignment in result.assignments:
            supplier_id = assignment.supplier_id

            if supplier_id not in supplier_stats:
                supplier_stats[supplier_id] = {
                    'supplier_name': supplier_map[supplier_id].name,
                    'book_count': 0,
                    'total_volume': 0,
                    'total_cost': 0.0
                }

            supplier_stats[supplier_id]['book_count'] += 1
            supplier_stats[supplier_id]['total_volume'] += assignment.production_volume
            supplier_stats[supplier_id]['total_cost'] += assignment.total_cost

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'supplier_id',
                'supplier_name',
                'books_assigned',
                'total_volume',
                'total_cost',
                'avg_cost_per_unit'
            ])
            writer.writeheader()

            for supplier_id, stats in sorted(supplier_stats.items()):
                avg_cost = stats['total_cost'] / stats['total_volume'] if stats['total_volume'] > 0 else 0

                writer.writerow({
                    'supplier_id': supplier_id,
                    'supplier_name': stats['supplier_name'],
                    'books_assigned': stats['book_count'],
                    'total_volume': stats['total_volume'],
                    'total_cost': f"{stats['total_cost']:.2f}",
                    'avg_cost_per_unit': f"{avg_cost:.2f}"
                })

    @staticmethod
    def export_brand_distribution_csv(
        result: OptimizationResult,
        output_file: Path,
        data: ProblemData
    ) -> None:
        """
        Export brand distribution across suppliers to CSV

        Args:
            result: Optimization result
            output_file: Path to output CSV file
            data: Problem data
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        book_map = {book.id: book for book in data.books}
        supplier_map = {supplier.id: supplier for supplier in data.suppliers}

        # Track brand distribution: brand -> supplier -> count
        distribution: Dict[str, Dict[str, int]] = {}

        for assignment in result.assignments:
            book = book_map[assignment.book_id]
            brand = book.brand
            supplier_id = assignment.supplier_id

            if brand not in distribution:
                distribution[brand] = {}

            if supplier_id not in distribution[brand]:
                distribution[brand][supplier_id] = 0

            distribution[brand][supplier_id] += 1

        # Get all supplier IDs for columns
        all_supplier_ids = sorted({s.id for s in data.suppliers})
        fieldnames = ['brand'] + all_supplier_ids + ['total']

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for brand in sorted(distribution.keys()):
                row = {'brand': brand}
                total = 0

                for supplier_id in all_supplier_ids:
                    count = distribution[brand].get(supplier_id, 0)
                    row[supplier_id] = count if count > 0 else ''
                    total += count

                row['total'] = total
                writer.writerow(row)

    @staticmethod
    def generate_report(
        result: OptimizationResult,
        data: ProblemData,
        output_dir: Path
    ) -> None:
        """
        Generate comprehensive report with multiple CSV files

        Args:
            result: Optimization result
            data: Problem data
            output_dir: Directory to save report files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if result.assignments:
            # Export assignments
            ResultExporter.export_assignments_csv(
                result.assignments,
                output_dir / "assignments.csv",
                data
            )

            # Export supplier summary
            ResultExporter.export_supplier_summary_csv(
                result,
                output_dir / "supplier_summary.csv",
                data
            )

            # Export brand distribution
            ResultExporter.export_brand_distribution_csv(
                result,
                output_dir / "brand_distribution.csv",
                data
            )
