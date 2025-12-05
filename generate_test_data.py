"""
Generate large-scale test data for performance testing

This script generates realistic printing optimization data with:
- 5000+ books with varying production volumes
- 20+ suppliers with multiple printing methods
- Realistic cost structures (offset cheaper for large volumes, digital for small)
- Multiple kits (bundles of books)
- Brand distribution across books
"""

import json
import random
import csv
from pathlib import Path
from typing import List, Dict

# Configuration
NUM_BOOKS = 1500
NUM_SUPPLIERS = 20
NUM_BRANDS = 15
NUM_KITS = 225
BOOKS_PER_KIT_MIN = 2
BOOKS_PER_KIT_MAX = 15
PRINTING_METHODS = ["offset", "digital", "hybrid"]

# Random seed for reproducibility
random.seed(42)

# Brand names
BRAND_PREFIXES = [
    "Tech", "Data", "Cloud", "Web", "Cyber", "Digital", "Smart", "Quantum",
    "Neural", "Blockchain", "AI", "Meta", "Nano", "Bio", "Eco", "Global",
    "Innovation", "Future", "Elite", "Prime", "Ultra", "Mega", "Hyper"
]
BRAND_SUFFIXES = [
    "Books", "Press", "Publishing", "Media", "Learning", "Education",
    "Academy", "Institute", "Group", "Solutions", "Systems", "Labs"
]

# Book title components
TITLE_PREFIXES = [
    "Introduction to", "Advanced", "Mastering", "Complete Guide to",
    "Practical", "Essential", "Modern", "Fundamentals of", "Deep Dive into",
    "Professional", "Comprehensive", "Beginner's Guide to", "Expert"
]
TITLE_TOPICS = [
    "Python Programming", "Data Science", "Machine Learning", "Web Development",
    "Cloud Computing", "DevOps", "Cybersecurity", "AI", "Blockchain",
    "IoT", "Mobile Development", "Database Design", "API Design",
    "System Architecture", "Network Engineering", "Software Testing",
    "Agile Methodology", "Project Management", "UX Design", "Digital Marketing"
]

# Supplier names
SUPPLIER_PREFIXES = [
    "Global", "Premium", "Express", "Quality", "Elite", "Pro", "Eco",
    "Fast", "Digital", "Precision", "Master", "Supreme", "Quick", "Reliable"
]
SUPPLIER_SUFFIXES = [
    "Print", "Press", "Publishing", "Solutions", "Services", "Graphics",
    "Media", "Productions", "Works", "Studio", "Group", "Partners"
]


def generate_brands() -> List[str]:
    """Generate brand names"""
    brands = []
    for i in range(NUM_BRANDS):
        if i < len(BRAND_PREFIXES) * len(BRAND_SUFFIXES):
            prefix = BRAND_PREFIXES[i // len(BRAND_SUFFIXES)]
            suffix = BRAND_SUFFIXES[i % len(BRAND_SUFFIXES)]
            brands.append(f"{prefix}{suffix}")
        else:
            brands.append(f"Brand{i:03d}")
    return brands


def generate_books(brands: List[str]) -> List[Dict]:
    """Generate book data"""
    books = []

    for i in range(NUM_BOOKS):
        book_id = f"B{i+1:05d}"

        # Generate title
        prefix = random.choice(TITLE_PREFIXES)
        topic = random.choice(TITLE_TOPICS)
        title = f"{prefix} {topic}"
        if random.random() < 0.3:  # 30% chance of volume number
            title += f" Vol. {random.randint(1, 5)}"

        # Assign brand
        brand = random.choice(brands)

        # Production volume (realistic distribution)
        # Most books: 1000-5000, some small runs: 100-1000, few large: 5000-10000
        rand = random.random()
        if rand < 0.7:  # 70% medium runs
            production_volume = random.randint(500, 2000)
        elif rand < 0.9:  # 20% small runs
            production_volume = random.randint(100, 1000)
        else:  # 10% large runs
            production_volume = random.randint(100, 2000)

        # Available printing methods
        # Small volumes (<1000): prefer digital
        # Medium volumes (1000-5000): both offset and digital
        # Large volumes (>5000): prefer offset, maybe hybrid
        if production_volume < 1000:
            available_methods = random.choice([
                ["digital"],
                ["digital", "hybrid"],
                ["digital", "offset"]
            ])
        elif production_volume < 5000:
            available_methods = random.choice([
                ["offset", "digital"],
                ["offset", "digital", "hybrid"],
                ["offset", "digital"]
            ])
        else:
            available_methods = random.choice([
                ["offset"],
                ["offset", "hybrid"],
                ["offset", "digital", "hybrid"]
            ])

        books.append({
            "id": book_id,
            "title": title,
            "brand": brand,
            "production_volume": production_volume,
            "available_printing_methods": available_methods,
            "kit_id": None  # Will be assigned later
        })

    return books


def generate_kits(books: List[Dict]) -> List[Dict]:
    """Generate kits and assign books to them"""
    kits = []
    available_book_indices = list(range(len(books)))
    random.shuffle(available_book_indices)

    for i in range(NUM_KITS):
        kit_id = f"K{i+1:04d}"
        kit_size = random.randint(BOOKS_PER_KIT_MIN, BOOKS_PER_KIT_MAX)

        # Take books for this kit
        if len(available_book_indices) < kit_size:
            break

        book_indices = available_book_indices[:kit_size]
        available_book_indices = available_book_indices[kit_size:]

        book_ids = [books[idx]["id"] for idx in book_indices]

        # Assign kit_id to books
        for idx in book_indices:
            books[idx]["kit_id"] = kit_id

        # Generate kit name based on first book
        first_book = books[book_indices[0]]
        kit_name = f"{first_book['brand']} Collection {i+1}"

        kits.append({
            "id": kit_id,
            "name": kit_name,
            "book_ids": book_ids
        })

    return kits


def generate_suppliers() -> List[Dict]:
    """Generate supplier data"""
    suppliers = []

    for i in range(NUM_SUPPLIERS):
        supplier_id = f"S{i+1:03d}"

        # Generate name
        prefix = random.choice(SUPPLIER_PREFIXES)
        suffix = random.choice(SUPPLIER_SUFFIXES)
        name = f"{prefix} {suffix}"

        # Generate capacities for each printing method
        # Offset: higher capacity (50k-150k)
        # Digital: medium capacity (20k-80k)
        # Hybrid: lower capacity (10k-40k)
        capacities = {
            "offset": random.randint(1000000, 3000000),
            "digital": random.randint(1000000, 2000000),
            "hybrid": random.randint(1000000, 4000000)
        }

        suppliers.append({
            "id": supplier_id,
            "name": name,
            "capacities": capacities
        })

    return suppliers


def generate_costs(books: List[Dict], suppliers: List[Dict]) -> List[List]:
    """Generate cost data"""
    costs = []

    for book in books:
        for supplier in suppliers:
            for method in book["available_printing_methods"]:
                # Base cost depends on printing method and volume
                volume = book["production_volume"]

                # Base unit costs
                if method == "offset":
                    # Offset: cheaper for large volumes, setup cost amortized
                    if volume < 1000:
                        base_cost = random.uniform(3.0, 4.5)
                    elif volume < 5000:
                        base_cost = random.uniform(2.0, 3.0)
                    else:
                        base_cost = random.uniform(1.5, 2.5)
                elif method == "digital":
                    # Digital: consistent cost regardless of volume
                    base_cost = random.uniform(2.5, 3.5)
                else:  # hybrid
                    # Hybrid: between offset and digital
                    if volume < 2000:
                        base_cost = random.uniform(2.8, 3.8)
                    else:
                        base_cost = random.uniform(2.2, 3.2)

                # Add supplier-specific variation (+/- 15%)
                supplier_factor = 0.85 + (hash(supplier["id"]) % 30) / 100
                unit_cost = base_cost * supplier_factor

                # Round to 2 decimal places
                unit_cost = round(unit_cost, 2)

                costs.append([book["id"], supplier["id"], method, unit_cost])

    return costs


def save_data(books: List[Dict], kits: List[Dict], suppliers: List[Dict], costs: List[List]):
    """Save generated data to files"""
    output_dir = Path("data/test_large")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save books
    with open(output_dir / "books.json", 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=2)

    # Save kits
    with open(output_dir / "kits.json", 'w', encoding='utf-8') as f:
        json.dump(kits, f, indent=2)

    # Save suppliers
    with open(output_dir / "suppliers.json", 'w', encoding='utf-8') as f:
        json.dump(suppliers, f, indent=2)

    # Save costs as CSV
    with open(output_dir / "costs.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['book_id', 'supplier_id', 'printing_method', 'unit_cost'])
        writer.writerows(costs)

    # Save config
    config = {
        "max_volumes_per_brand_per_supplier": 4,
        "solver_time_limit_seconds": 600,  # 10 minutes for large problem
        "num_search_workers": 8,
        "enable_symmetry_breaking": True
    }
    with open(output_dir / "config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    print(f"\n{'='*60}")
    print("Test Data Generation Complete!")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print(f"\nStatistics:")
    print(f"  Books:              {len(books):,}")
    print(f"  Kits:               {len(kits):,}")
    print(f"  Books in kits:      {sum(1 for b in books if b['kit_id'] is not None):,}")
    print(f"  Suppliers:          {len(suppliers):,}")
    print(f"  Cost entries:       {len(costs):,}")
    print(f"  Brands:             {len(set(b['brand'] for b in books)):,}")

    # Volume statistics
    volumes = [b["production_volume"] for b in books]
    total_volume = sum(volumes)
    avg_volume = total_volume / len(volumes)

    print(f"\nProduction Volume:")
    print(f"  Total:              {total_volume:,}")
    print(f"  Average per book:   {avg_volume:,.0f}")
    print(f"  Min:                {min(volumes):,}")
    print(f"  Max:                {max(volumes):,}")

    # Method distribution
    method_counts = {}
    for book in books:
        for method in book["available_printing_methods"]:
            method_counts[method] = method_counts.get(method, 0) + 1

    print(f"\nPrinting Methods:")
    for method, count in sorted(method_counts.items()):
        print(f"  {method:12s}    {count:,} books can use this method")

    # Capacity analysis
    total_capacity = {method: sum(s["capacities"][method] for s in suppliers) for method in PRINTING_METHODS}
    print(f"\nTotal Supplier Capacity:")
    for method in PRINTING_METHODS:
        print(f"  {method:12s}    {total_capacity[method]:,}")

    print(f"\nTo run optimization:")
    print(f"  python -m src.optimizer.cli solve \\")
    print(f"      --books {output_dir}/books.json \\")
    print(f"      --kits {output_dir}/kits.json \\")
    print(f"      --suppliers {output_dir}/suppliers.json \\")
    print(f"      --costs {output_dir}/costs.csv \\")
    print(f"      --config {output_dir}/config.json \\")
    print(f"      --output results/solution_large.json")
    print(f"{'='*60}\n")


def main():
    """Main execution"""
    print("Generating large-scale test data...")
    print(f"  Target books: {NUM_BOOKS:,}")
    print(f"  Target suppliers: {NUM_SUPPLIERS}")
    print(f"  Target kits: {NUM_KITS}")
    print()

    # Generate data
    print("Generating brands...")
    brands = generate_brands()

    print("Generating books...")
    books = generate_books(brands)

    print("Generating kits...")
    kits = generate_kits(books)

    print("Generating suppliers...")
    suppliers = generate_suppliers()

    print("Generating costs...")
    costs = generate_costs(books, suppliers)

    print("Saving data...")
    save_data(books, kits, suppliers, costs)


if __name__ == "__main__":
    main()
