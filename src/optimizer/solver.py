"""CP-SAT solver for the supplier allocation problem with printing method optimization"""

import time
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from ortools.sat.python import cp_model

from .models import Book, ProblemData, OptimizationResult, Assignment


class SupplierAllocationSolver:
    """Solves the constrained supplier allocation problem using CP-SAT with method optimization"""

    def __init__(self, data: ProblemData):
        """
        Initialize solver with problem data

        Args:
            data: Complete problem data including books, kits, suppliers, costs
        """
        self.data = data
        self.model = cp_model.CpModel()

        # Decision variables: x[book_id, supplier_id, method] = 1 if book assigned to supplier using method
        self.x: Dict[Tuple[str, str, str], cp_model.IntVar] = {}

        # Cost matrix: (book_id, supplier_id, method) -> unit_cost
        self.cost_matrix: Dict[Tuple[str, str, str], float] = {
            (cost.book_id, cost.supplier_id, cost.printing_method): cost.unit_cost
            for cost in data.costs
        }

        # Helper dictionaries
        self.book_map = {book.id: book for book in data.books}
        self.supplier_map = {supplier.id: supplier for supplier in data.suppliers}
        self.kit_map = {kit.id: kit for kit in data.kits}

        # Books by kit
        self.books_by_kit: Dict[str, List[str]] = {
            kit.id: kit.book_ids for kit in data.kits
        }

        # Books by brand
        self.books_by_brand: Dict[str, List[str]] = defaultdict(list)
        for book in data.books:
            self.books_by_brand[book.brand].append(book.id)

    def build_model(self) -> None:
        """Build the complete CP-SAT model with all constraints"""
        self._create_variables()
        self._add_assignment_constraints()
        self._add_kit_cohesion_constraints()
        self._add_brand_diversification_constraints()
        self._add_capacity_constraints()
        self._add_objective()

        if self.data.config.enable_symmetry_breaking:
            self._add_symmetry_breaking_constraints()

    def _create_variables(self) -> None:
        """Create decision variables for book-to-supplier-method assignments"""
        for book in self.data.books:
            for supplier in self.data.suppliers:
                for method in book.available_printing_methods:
                    # Only create variable if there's a cost defined for this combination
                    if (book.id, supplier.id, method) in self.cost_matrix:
                        var_name = f"x_{book.id}_{supplier.id}_{method}"
                        self.x[book.id, supplier.id, method] = self.model.NewBoolVar(var_name)

    def _add_assignment_constraints(self) -> None:
        """Each book must be assigned to exactly one (supplier, method) combination"""
        for book in self.data.books:
            # Get all valid (supplier, method) combinations for this book
            valid_assignments = [
                self.x[book.id, supplier.id, method]
                for supplier in self.data.suppliers
                for method in book.available_printing_methods
                if (book.id, supplier.id, method) in self.x
            ]

            if not valid_assignments:
                raise ValueError(
                    f"Book {book.id} has no valid (supplier, method) assignments"
                )

            # Exactly one (supplier, method) pair per book
            self.model.Add(sum(valid_assignments) == 1)

    def _add_kit_cohesion_constraints(self) -> None:
        """All books in a kit must be assigned to the same supplier (but can use different methods)"""
        for kit in self.data.kits:
            if len(kit.book_ids) < 2:
                continue  # Single-book kits don't need cohesion constraints

            # Reference book (first book in kit)
            ref_book_id = kit.book_ids[0]

            # For each supplier, create a variable indicating if the kit is assigned to that supplier
            kit_supplier_vars = {}
            for supplier in self.data.suppliers:
                kit_supplier_vars[supplier.id] = self.model.NewBoolVar(
                    f"kit_{kit.id}_supplier_{supplier.id}"
                )

                # Kit is assigned to supplier if ref_book is assigned to supplier (any method)
                ref_book_to_supplier = [
                    self.x[ref_book_id, supplier.id, method]
                    for method in self.book_map[ref_book_id].available_printing_methods
                    if (ref_book_id, supplier.id, method) in self.x
                ]

                if ref_book_to_supplier:
                    # kit_supplier_var == 1 iff any method of ref_book is assigned to this supplier
                    self.model.Add(
                        sum(ref_book_to_supplier) == kit_supplier_vars[supplier.id]
                    )

            # All other books must be assigned to the same supplier as the reference book
            for book_id in kit.book_ids[1:]:
                for supplier in self.data.suppliers:
                    # If kit is assigned to this supplier, this book must also be assigned to this supplier
                    book_to_supplier = [
                        self.x[book_id, supplier.id, method]
                        for method in self.book_map[book_id].available_printing_methods
                        if (book_id, supplier.id, method) in self.x
                    ]

                    if book_to_supplier and supplier.id in kit_supplier_vars:
                        # sum(book_to_supplier) == kit_supplier_var[supplier]
                        self.model.Add(
                            sum(book_to_supplier) == kit_supplier_vars[supplier.id]
                        )

    def _add_brand_diversification_constraints(self) -> None:
        """Maximum volumes per brand per supplier constraint (regardless of method)"""
        max_volumes = self.data.config.max_volumes_per_brand_per_supplier

        for brand, book_ids in self.books_by_brand.items():
            for supplier in self.data.suppliers:
                # Count how many books of this brand are assigned to this supplier (any method)
                brand_books_to_supplier = []

                for book_id in book_ids:
                    book = self.book_map[book_id]
                    # For each book, create a binary indicator: is it assigned to this supplier?
                    book_to_supplier_indicator = self.model.NewBoolVar(
                        f"brand_{brand}_book_{book_id}_supplier_{supplier.id}"
                    )

                    # Get all methods for this book-supplier combination
                    methods_for_book_supplier = [
                        self.x[book_id, supplier.id, method]
                        for method in book.available_printing_methods
                        if (book_id, supplier.id, method) in self.x
                    ]

                    if methods_for_book_supplier:
                        # Indicator is 1 if book is assigned to supplier with any method
                        self.model.Add(
                            sum(methods_for_book_supplier) == book_to_supplier_indicator
                        )
                        brand_books_to_supplier.append(book_to_supplier_indicator)
                    else:
                        # No valid assignments, indicator must be 0
                        self.model.Add(book_to_supplier_indicator == 0)

                if brand_books_to_supplier:
                    self.model.Add(sum(brand_books_to_supplier) <= max_volumes)

    def _add_capacity_constraints(self) -> None:
        """Supplier capacity constraints by printing method"""
        for supplier in self.data.suppliers:
            # Group by printing method
            books_by_method: Dict[str, List[Tuple[str, str, int]]] = defaultdict(list)

            for book in self.data.books:
                for method in book.available_printing_methods:
                    if (book.id, supplier.id, method) in self.x:
                        books_by_method[method].append(
                            (book.id, method, book.production_volume)
                        )

            # Add capacity constraint for each printing method
            for method, capacity in supplier.capacities.items():
                if method in books_by_method:
                    # Sum of (production_volume * assignment_var) <= capacity
                    total_volume_expr = sum(
                        volume * self.x[book_id, supplier.id, book_method]
                        for book_id, book_method, volume in books_by_method[method]
                    )
                    self.model.Add(total_volume_expr <= capacity)

    def _add_symmetry_breaking_constraints(self) -> None:
        """
        Add symmetry breaking constraints for suppliers with identical characteristics

        If two suppliers have the same costs and capacities, we can arbitrarily
        prefer one over the other to reduce the search space
        """
        # Group suppliers by their characteristics (capacities)
        supplier_groups: Dict[tuple, List[str]] = defaultdict(list)

        for supplier in self.data.suppliers:
            # Create a hashable signature of the supplier's capacities
            capacity_signature = tuple(sorted(supplier.capacities.items()))
            supplier_groups[capacity_signature].append(supplier.id)

        # For each group with multiple suppliers, add ordering constraints
        for signature, supplier_ids in supplier_groups.items():
            if len(supplier_ids) < 2:
                continue

            # Check if these suppliers also have identical costs for all (book, method) combinations
            identical_costs = True
            for book in self.data.books:
                for method in book.available_printing_methods:
                    costs = []
                    for supplier_id in supplier_ids:
                        if (book.id, supplier_id, method) in self.cost_matrix:
                            costs.append(self.cost_matrix[book.id, supplier_id, method])

                    if len(set(costs)) > 1:  # Costs differ
                        identical_costs = False
                        break
                if not identical_costs:
                    break

            if identical_costs:
                # Add ordering constraint: total volume of s1 >= total volume of s2
                for i in range(len(supplier_ids) - 1):
                    s1_id = supplier_ids[i]
                    s2_id = supplier_ids[i + 1]

                    # Calculate total volume assigned to each supplier
                    s1_volumes = []
                    s2_volumes = []

                    for book in self.data.books:
                        for method in book.available_printing_methods:
                            if (book.id, s1_id, method) in self.x:
                                s1_volumes.append(
                                    book.production_volume * self.x[book.id, s1_id, method]
                                )
                            if (book.id, s2_id, method) in self.x:
                                s2_volumes.append(
                                    book.production_volume * self.x[book.id, s2_id, method]
                                )

                    if s1_volumes and s2_volumes:
                        self.model.Add(sum(s1_volumes) >= sum(s2_volumes))

    def _add_objective(self) -> None:
        """Minimize total printing cost"""
        total_cost_expr = sum(
            int(self.cost_matrix[book.id, supplier.id, method] * book.production_volume * 1000) *
            self.x[book.id, supplier.id, method]
            for book in self.data.books
            for supplier in self.data.suppliers
            for method in book.available_printing_methods
            if (book.id, supplier.id, method) in self.x
        )

        self.model.Minimize(total_cost_expr)

    def solve(self) -> OptimizationResult:
        """
        Solve the optimization problem

        Returns:
            OptimizationResult containing solution status, assignments, and statistics
        """
        solver = cp_model.CpSolver()

        # Configure solver parameters
        solver.parameters.max_time_in_seconds = self.data.config.solver_time_limit_seconds
        solver.parameters.num_search_workers = self.data.config.num_search_workers
        solver.parameters.log_search_progress = True

        # Solve
        start_time = time.time()
        status = solver.Solve(self.model)
        solve_time = time.time() - start_time

        # Extract results
        status_name = solver.StatusName(status)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignments = self._extract_assignments(solver)
            objective_value = solver.ObjectiveValue() / 1000.0  # Convert back from scaled integer
            total_books = len(assignments)
            total_volume = sum(a.production_volume for a in assignments)
            supplier_utilization = self._calculate_utilization(assignments)

            return OptimizationResult(
                status=status_name,
                objective_value=objective_value,
                solve_time_seconds=solve_time,
                assignments=assignments,
                total_books=total_books,
                total_volume=total_volume,
                supplier_utilization=supplier_utilization
            )
        else:
            # No solution found
            return OptimizationResult(
                status=status_name,
                objective_value=None,
                solve_time_seconds=solve_time,
                assignments=[],
                total_books=0,
                total_volume=0,
                supplier_utilization={}
            )

    def _extract_assignments(self, solver: cp_model.CpSolver) -> List[Assignment]:
        """Extract book-to-supplier-method assignments from solved model"""
        assignments = []

        for book in self.data.books:
            for supplier in self.data.suppliers:
                for method in book.available_printing_methods:
                    if (book.id, supplier.id, method) in self.x:
                        if solver.Value(self.x[book.id, supplier.id, method]) == 1:
                            unit_cost = self.cost_matrix[book.id, supplier.id, method]
                            total_cost = unit_cost * book.production_volume

                            assignments.append(Assignment(
                                book_id=book.id,
                                supplier_id=supplier.id,
                                printing_method=method,
                                production_volume=book.production_volume,
                                unit_cost=unit_cost,
                                total_cost=total_cost
                            ))
                            break  # Book assigned, move to next book

        return assignments

    def _calculate_utilization(
        self, assignments: List[Assignment]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate supplier utilization by printing method

        Returns:
            Dict mapping supplier_id -> {method -> utilization_percentage}
        """
        utilization: Dict[str, Dict[str, float]] = {}

        # Calculate volume used per supplier per method
        volume_used: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for assignment in assignments:
            method = assignment.printing_method
            volume_used[assignment.supplier_id][method] += assignment.production_volume

        # Calculate utilization percentages
        for supplier in self.data.suppliers:
            utilization[supplier.id] = {}
            for method, capacity in supplier.capacities.items():
                used = volume_used[supplier.id].get(method, 0)
                utilization[supplier.id][method] = (used / capacity * 100) if capacity > 0 else 0.0

        return utilization
