"""Data models for the optimization problem"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Book(BaseModel):
    """Represents a book to be printed"""

    id: str = Field(..., description="Unique book identifier")
    title: str = Field(..., description="Book title")
    brand: str = Field(..., description="Brand/series the book belongs to")
    production_volume: int = Field(..., gt=0, description="Number of copies to print")
    available_printing_methods: List[str] = Field(
        ...,
        min_length=1,
        description="List of printing methods that can be used for this book (e.g., ['offset', 'digital'])"
    )
    kit_id: Optional[str] = Field(None, description="Kit this book belongs to (if any)")

    @field_validator('available_printing_methods')
    @classmethod
    def validate_printing_methods(cls, v: List[str]) -> List[str]:
        """Validate and normalize printing methods"""
        normalized = [method.lower().strip() for method in v]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Duplicate printing methods found")
        return normalized


class Kit(BaseModel):
    """Represents a kit (bundle of books that must be allocated together)"""

    id: str = Field(..., description="Unique kit identifier")
    name: str = Field(..., description="Kit name")
    book_ids: List[str] = Field(..., min_length=1, description="Books in this kit")

    @field_validator('book_ids')
    @classmethod
    def validate_book_ids(cls, v: List[str]) -> List[str]:
        """Ensure no duplicate books in kit"""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate book IDs in kit")
        return v


class Supplier(BaseModel):
    """Represents a printing supplier"""

    id: str = Field(..., description="Unique supplier identifier")
    name: str = Field(..., description="Supplier name")
    capacities: Dict[str, int] = Field(
        ...,
        description="Production capacity by printing method (method -> max volumes)"
    )

    @field_validator('capacities')
    @classmethod
    def validate_capacities(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Normalize printing method keys and validate positive capacities"""
        normalized = {}
        for method, capacity in v.items():
            if capacity <= 0:
                raise ValueError(f"Capacity must be positive, got {capacity} for {method}")
            normalized[method.lower().strip()] = capacity
        return normalized


class Cost(BaseModel):
    """Represents the cost of printing a book at a supplier using a specific method"""

    book_id: str = Field(..., description="Book identifier")
    supplier_id: str = Field(..., description="Supplier identifier")
    printing_method: str = Field(..., description="Printing method (e.g., offset, digital)")
    unit_cost: float = Field(..., gt=0, description="Cost per unit")

    @field_validator('printing_method')
    @classmethod
    def validate_printing_method(cls, v: str) -> str:
        """Validate and normalize printing method"""
        return v.lower().strip()


class OptimizationConfig(BaseModel):
    """Configuration for the optimization problem"""

    max_volumes_per_brand_per_supplier: int = Field(
        4,
        gt=0,
        description="Maximum volumes of the same brand per supplier"
    )
    solver_time_limit_seconds: int = Field(
        300,
        gt=0,
        description="Maximum solver time in seconds"
    )
    num_search_workers: int = Field(
        8,
        gt=0,
        description="Number of parallel search workers"
    )
    enable_symmetry_breaking: bool = Field(
        True,
        description="Enable symmetry breaking constraints"
    )


class ProblemData(BaseModel):
    """Complete problem data"""

    books: List[Book]
    kits: List[Kit]
    suppliers: List[Supplier]
    costs: List[Cost]
    config: OptimizationConfig = Field(default_factory=OptimizationConfig)

    @field_validator('books')
    @classmethod
    def validate_unique_books(cls, v: List[Book]) -> List[Book]:
        """Ensure unique book IDs"""
        book_ids = [book.id for book in v]
        if len(book_ids) != len(set(book_ids)):
            raise ValueError("Duplicate book IDs found")
        return v

    @field_validator('kits')
    @classmethod
    def validate_unique_kits(cls, v: List[Kit]) -> List[Kit]:
        """Ensure unique kit IDs"""
        kit_ids = [kit.id for kit in v]
        if len(kit_ids) != len(set(kit_ids)):
            raise ValueError("Duplicate kit IDs found")
        return v

    @field_validator('suppliers')
    @classmethod
    def validate_unique_suppliers(cls, v: List[Supplier]) -> List[Supplier]:
        """Ensure unique supplier IDs"""
        supplier_ids = [supplier.id for supplier in v]
        if len(supplier_ids) != len(set(supplier_ids)):
            raise ValueError("Duplicate supplier IDs found")
        return v


class Assignment(BaseModel):
    """Represents an assignment of a book to a supplier using a specific printing method"""

    book_id: str
    supplier_id: str
    printing_method: str
    production_volume: int
    unit_cost: float
    total_cost: float


class OptimizationResult(BaseModel):
    """Results from the optimization"""

    status: str = Field(..., description="Solver status (OPTIMAL, FEASIBLE, INFEASIBLE, etc.)")
    objective_value: Optional[float] = Field(None, description="Total cost (if solution found)")
    solve_time_seconds: float = Field(..., description="Time taken to solve")
    assignments: List[Assignment] = Field(default_factory=list, description="Book-to-supplier assignments")

    # Statistics
    total_books: int = Field(0, description="Total number of books assigned")
    total_volume: int = Field(0, description="Total production volume")
    supplier_utilization: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Supplier utilization by printing method (percentage)"
    )
