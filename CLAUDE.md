# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a printing cost optimization project that solves a **constrained generalized assignment problem** for allocating books to printing suppliers. The problem involves:

- **Grouping constraints**: Kits (bundles of books) must be allocated together
- **Cardinality constraints**: Maximum 4 volumes per brand per supplier
- **Multi-resource capacity**: Supplier capacity varies by printing method
- **Cost minimization**: Find the optimal supplier assignment that minimizes total printing costs

## Problem Characteristics

The optimization problem is classified as a **Generalized Assignment Problem (GAP) with Side Constraints**, exhibiting:
- Bin packing aspects (assigning items to bins with capacity constraints)
- Set partitioning structure (each book must go to exactly one supplier)
- NP-hard complexity requiring sophisticated optimization techniques

## Recommended Technology Stack

Based on the research in PRODUCT_PLAN.txt, the recommended approach is:

### For Medium-Scale Problems (< 1000 books, < 20 suppliers)
- **Primary**: Python with Google OR-Tools CP-SAT solver
- **Alternative**: PuLP + HiGHS for pure MILP formulation
- CP-SAT is recommended because it handles constraint-heavy problems efficiently and is free/open-source

### For Large-Scale Problems (> 5000 books)
- Adaptive Large Neighborhood Search (ALNS) metaheuristic
- Column Generation with pattern-based formulation
- Consider commercial solvers (Gurobi, CPLEX) if budget allows (5-20x performance improvement)

## Key Constraints to Model

When implementing the optimization:

1. **Volume Uniformity (No Splitting)**: Each book assigned to exactly one supplier
   ```
   ∀ book b: Σ_s x[b,s] = 1
   ```

2. **Kit Cohesion**: All books in a kit share the same supplier assignment
   ```
   ∀ kit k, ∀ books b ∈ k, ∀ suppliers s: x[b,s] = y[k,s]
   ```

3. **Brand Diversification**: Max 4 volumes per brand per supplier
   ```
   ∀ brand br, ∀ supplier s: Σ_{b ∈ br} x[b,s] ≤ 4
   ```

4. **Supplier Capacity by Printing Method**: Separate capacity constraints per method
   ```
   ∀ supplier s, ∀ method m: Σ_b (production_volume[b] × x[b,s] × uses_method[b,m]) ≤ capacity[s,m]
   ```

## Critical Implementation Considerations

### Symmetry Breaking
The problem will have significant symmetry issues when suppliers have similar costs and capacities. Add symmetry-breaking constraints:
```
If suppliers s1 and s2 have identical characteristics:
   total_volume[s1] ≥ total_volume[s2]
```

### Kit-Level Variables
Instead of book-level assignment variables, use kit-level variables to reduce variable count and naturally enforce kit cohesion.

### Parallel Search
When using OR-Tools CP-SAT, enable parallel search for better performance:
```python
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 300
```

## Expected Solution Quality

| Problem Scale | Primary Method | Solver | Expected Quality |
|---------------|----------------|--------|------------------|
| Small (<200 books) | Pure MILP | HiGHS/OR-Tools | Optimal |
| Medium (200-2000) | CP-SAT or MILP | OR-Tools CP-SAT | Optimal or gap <1% |
| Large (2000-10000) | MILP + LNS | Gurobi or CP-SAT | Gap 1-5% |
| Very Large (>10000) | Column Generation or ALNS | Custom + HiGHS | Gap 3-10% |

## Development Approach

When implementing:
1. Start with OR-Tools CP-SAT prototype for the constraint structure
2. Implement symmetry-breaking constraints for similar suppliers
3. Benchmark on representative data subsets
4. If performance is insufficient, consider Gurobi (commercial) or implement ALNS with domain-specific operators
