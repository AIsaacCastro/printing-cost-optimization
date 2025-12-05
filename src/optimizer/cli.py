"""Command-line interface for the optimization solver"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .data_loader import DataLoader
from .solver import SupplierAllocationSolver
from .models import OptimizationResult

app = typer.Typer(
    name="print-optimizer",
    help="Optimize book-to-supplier allocation for printing cost minimization"
)
console = Console()


@app.command()
def solve(
    books_file: Path = typer.Option(
        ...,
        "--books",
        "-b",
        help="Path to books JSON file",
        exists=True
    ),
    kits_file: Path = typer.Option(
        ...,
        "--kits",
        "-k",
        help="Path to kits JSON file",
        exists=True
    ),
    suppliers_file: Path = typer.Option(
        ...,
        "--suppliers",
        "-s",
        help="Path to suppliers JSON file",
        exists=True
    ),
    costs_file: Path = typer.Option(
        ...,
        "--costs",
        "-c",
        help="Path to costs CSV file",
        exists=True
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config JSON file (optional)"
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to save results JSON file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output"
    )
):
    """
    Solve the supplier allocation optimization problem

    Example:
        python -m src.optimizer.cli solve \\
            --books data/example_books.json \\
            --kits data/example_kits.json \\
            --suppliers data/example_suppliers.json \\
            --costs data/example_costs.csv \\
            --output results/solution.json
    """
    console.print("\n[bold cyan]Printing Cost Optimization Solver[/bold cyan]\n")

    try:
        # Load data
        console.print("Loading data...")
        data = DataLoader.load_problem_data(
            books_file=books_file,
            kits_file=kits_file,
            suppliers_file=suppliers_file,
            costs_file=costs_file,
            config_file=config_file
        )

        # Display problem summary
        console.print(f"[green][OK][/green] Loaded data successfully")
        console.print(f"  • Books: {len(data.books)}")
        console.print(f"  • Kits: {len(data.kits)}")
        console.print(f"  • Suppliers: {len(data.suppliers)}")
        console.print(f"  • Cost entries: {len(data.costs)}\n")

        # Build and solve model
        console.print("[bold]Building optimization model...[/bold]")
        solver = SupplierAllocationSolver(data)
        solver.build_model()
        console.print("[green][OK][/green] Model built successfully\n")

        console.print("[bold]Solving...[/bold]")
        result = solver.solve()

        # Display results
        _display_results(result, data, verbose)

        # Save results if output file specified
        if output_file:
            _save_results(result, output_file, solver)
            console.print(f"\n[green][OK][/green] Results saved to {output_file}")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


def _display_results(result: OptimizationResult, data, verbose: bool):
    """Display optimization results in a formatted table"""
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  • Status: [cyan]{result.status}[/cyan]")
    console.print(f"  • Solve time: {result.solve_time_seconds:.2f} seconds")

    if result.objective_value is not None:
        console.print(f"  • Total cost: [green]${result.objective_value:,.2f}[/green]")
        console.print(f"  • Books assigned: {result.total_books}")
        console.print(f"  • Total volume: {result.total_volume:,}")

        # Assignments by supplier
        console.print(f"\n[bold]Assignments by Supplier:[/bold]\n")

        assignments_by_supplier = {}
        for assignment in result.assignments:
            if assignment.supplier_id not in assignments_by_supplier:
                assignments_by_supplier[assignment.supplier_id] = []
            assignments_by_supplier[assignment.supplier_id].append(assignment)

        for supplier_id, assignments in sorted(assignments_by_supplier.items()):
            supplier = next(s for s in data.suppliers if s.id == supplier_id)
            total_cost = sum(a.total_cost for a in assignments)
            total_volume = sum(a.production_volume for a in assignments)

            console.print(f"[bold cyan]{supplier.name}[/bold cyan] ({supplier_id})")
            console.print(f"  Books: {len(assignments)} | Volume: {total_volume:,} | Cost: ${total_cost:,.2f}")

            if verbose:
                # Show individual book assignments
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Book ID", style="cyan")
                table.add_column("Volume", justify="right")
                table.add_column("Unit Cost", justify="right")
                table.add_column("Total Cost", justify="right")

                for assignment in sorted(assignments, key=lambda a: a.book_id):
                    table.add_row(
                        assignment.book_id,
                        f"{assignment.production_volume:,}",
                        f"${assignment.unit_cost:.2f}",
                        f"${assignment.total_cost:,.2f}"
                    )

                console.print(table)

            # Show utilization
            if supplier_id in result.supplier_utilization:
                console.print("  Utilization:")
                for method, util_pct in result.supplier_utilization[supplier_id].items():
                    console.print(f"    • {method}: {util_pct:.1f}%")

            console.print()

    else:
        console.print("[yellow]No solution found[/yellow]")


def _save_results(result: OptimizationResult, output_file: Path, solver: SupplierAllocationSolver):
    """Save results to JSON file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepare detailed results
    results_dict = {
        "status": result.status,
        "objective_value": result.objective_value,
        "solve_time_seconds": result.solve_time_seconds,
        "total_books": result.total_books,
        "total_volume": result.total_volume,
        "assignments": [
            {
                "book_id": a.book_id,
                "supplier_id": a.supplier_id,
                "production_volume": a.production_volume,
                "unit_cost": a.unit_cost,
                "total_cost": a.total_cost
            }
            for a in result.assignments
        ],
        "supplier_utilization": result.supplier_utilization
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2)


@app.command()
def validate(
    books_file: Path = typer.Option(..., "--books", "-b", exists=True),
    kits_file: Path = typer.Option(..., "--kits", "-k", exists=True),
    suppliers_file: Path = typer.Option(..., "--suppliers", "-s", exists=True),
    costs_file: Path = typer.Option(..., "--costs", "-c", exists=True),
    config_file: Optional[Path] = typer.Option(None, "--config")
):
    """Validate input data files without solving"""
    console.print("\n[bold cyan]Validating data files...[/bold cyan]\n")

    try:
        data = DataLoader.load_problem_data(
            books_file=books_file,
            kits_file=kits_file,
            suppliers_file=suppliers_file,
            costs_file=costs_file,
            config_file=config_file
        )

        console.print("[green][OK][/green] All data files are valid!")
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  • Books: {len(data.books)}")
        console.print(f"  • Kits: {len(data.kits)}")
        console.print(f"  • Suppliers: {len(data.suppliers)}")
        console.print(f"  • Cost entries: {len(data.costs)}")

        # Brand distribution
        brands = {}
        for book in data.books:
            brands[book.brand] = brands.get(book.brand, 0) + 1

        console.print(f"\n[bold]Books by Brand:[/bold]")
        for brand, count in sorted(brands.items()):
            console.print(f"  • {brand}: {count}")

        # Printing methods
        methods = {}
        for book in data.books:
            methods[book.printing_method] = methods.get(book.printing_method, 0) + 1

        console.print(f"\n[bold]Books by Printing Method:[/bold]")
        for method, count in sorted(methods.items()):
            console.print(f"  • {method}: {count}")

    except Exception as e:
        console.print(f"\n[bold red]Validation Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
