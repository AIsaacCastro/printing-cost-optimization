"""Data loading and validation utilities"""

import json
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

from .models import Book, Kit, Supplier, Cost, OptimizationConfig, ProblemData


class DataLoader:
    """Loads and validates optimization problem data from files"""

    @staticmethod
    def load_books(file_path: str | Path) -> List[Book]:
        """Load books from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Book(**book_data) for book_data in data]

    @staticmethod
    def load_kits(file_path: str | Path) -> List[Kit]:
        """Load kits from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Kit(**kit_data) for kit_data in data]

    @staticmethod
    def load_suppliers(file_path: str | Path) -> List[Supplier]:
        """Load suppliers from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Supplier(**supplier_data) for supplier_data in data]

    @staticmethod
    def load_costs_from_csv(file_path: str | Path) -> List[Cost]:
        """Load costs from CSV file"""
        df = pd.read_csv(file_path)
        return [
            Cost(
                book_id=row['book_id'],
                supplier_id=row['supplier_id'],
                unit_cost=row['unit_cost']
            )
            for _, row in df.iterrows()
        ]

    @staticmethod
    def load_config(file_path: str | Path | None = None) -> OptimizationConfig:
        """Load configuration from JSON file or use defaults"""
        if file_path is None:
            return OptimizationConfig()

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return OptimizationConfig(**data)

    @classmethod
    def load_problem_data(
        cls,
        books_file: str | Path,
        kits_file: str | Path,
        suppliers_file: str | Path,
        costs_file: str | Path,
        config_file: str | Path | None = None
    ) -> ProblemData:
        """
        Load complete problem data from files

        Args:
            books_file: Path to books JSON file
            kits_file: Path to kits JSON file
            suppliers_file: Path to suppliers JSON file
            costs_file: Path to costs CSV file
            config_file: Optional path to config JSON file

        Returns:
            ProblemData object with all loaded and validated data

        Raises:
            ValueError: If data is invalid or inconsistent
        """
        books = cls.load_books(books_file)
        kits = cls.load_kits(kits_file)
        suppliers = cls.load_suppliers(suppliers_file)
        costs = cls.load_costs_from_csv(costs_file)
        config = cls.load_config(config_file)

        # Create ProblemData (Pydantic will validate)
        problem_data = ProblemData(
            books=books,
            kits=kits,
            suppliers=suppliers,
            costs=costs,
            config=config
        )

        # Additional cross-validation
        cls._validate_problem_data(problem_data)

        return problem_data

    @staticmethod
    def _validate_problem_data(data: ProblemData) -> None:
        """
        Perform cross-validation across different data entities

        Raises:
            ValueError: If data is inconsistent
        """
        book_ids = {book.id for book in data.books}
        supplier_ids = {supplier.id for supplier in data.suppliers}

        # Validate kit book references
        for kit in data.kits:
            for book_id in kit.book_ids:
                if book_id not in book_ids:
                    raise ValueError(
                        f"Kit {kit.id} references non-existent book {book_id}"
                    )

        # Validate cost references
        cost_book_ids = set()
        cost_supplier_ids = set()
        for cost in data.costs:
            if cost.book_id not in book_ids:
                raise ValueError(
                    f"Cost entry references non-existent book {cost.book_id}"
                )
            if cost.supplier_id not in supplier_ids:
                raise ValueError(
                    f"Cost entry references non-existent supplier {cost.supplier_id}"
                )
            cost_book_ids.add(cost.book_id)
            cost_supplier_ids.add(cost.supplier_id)

        # Check that all books have at least one cost entry
        books_without_costs = book_ids - cost_book_ids
        if books_without_costs:
            raise ValueError(
                f"Books without cost data: {', '.join(sorted(books_without_costs))}"
            )

        # Validate kit book assignments
        kit_book_assignments: Dict[str, str] = {}
        for kit in data.kits:
            for book_id in kit.book_ids:
                if book_id in kit_book_assignments:
                    raise ValueError(
                        f"Book {book_id} appears in multiple kits: "
                        f"{kit_book_assignments[book_id]} and {kit.id}"
                    )
                kit_book_assignments[book_id] = kit.id

        # Validate books' kit_id matches actual kit membership
        for book in data.books:
            if book.kit_id is not None:
                if book.id not in kit_book_assignments:
                    raise ValueError(
                        f"Book {book.id} claims to be in kit {book.kit_id}, "
                        "but is not listed in any kit"
                    )
                if kit_book_assignments[book.id] != book.kit_id:
                    raise ValueError(
                        f"Book {book.id} kit_id mismatch: "
                        f"claims {book.kit_id} but is in {kit_book_assignments[book.id]}"
                    )

        # Validate supplier capacities cover all required printing methods
        printing_methods = {book.printing_method for book in data.books}
        for supplier in data.suppliers:
            supplier_methods = set(supplier.capacities.keys())
            missing_methods = printing_methods - supplier_methods
            if missing_methods:
                # This is just a warning case - supplier might not support all methods
                pass

    @staticmethod
    def get_books_by_kit(data: ProblemData) -> Dict[str, List[Book]]:
        """Group books by kit ID"""
        books_by_kit: Dict[str, List[Book]] = {}
        book_map = {book.id: book for book in data.books}

        for kit in data.kits:
            books_by_kit[kit.id] = [book_map[book_id] for book_id in kit.book_ids]

        return books_by_kit

    @staticmethod
    def get_cost_matrix(data: ProblemData) -> Dict[tuple[str, str], float]:
        """
        Create a cost lookup dictionary

        Returns:
            Dict mapping (book_id, supplier_id) -> unit_cost
        """
        return {
            (cost.book_id, cost.supplier_id): cost.unit_cost
            for cost in data.costs
        }

    @staticmethod
    def get_books_by_brand(data: ProblemData) -> Dict[str, List[Book]]:
        """Group books by brand"""
        books_by_brand: Dict[str, List[Book]] = {}
        for book in data.books:
            if book.brand not in books_by_brand:
                books_by_brand[book.brand] = []
            books_by_brand[book.brand].append(book)
        return books_by_brand
