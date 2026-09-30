# Warehouse Operations Engine

A Python-based warehouse operations engine for inventory management, order fulfillment, warehouse analytics, capacity planning, and weighted route optimization.

The project models core fulfillment-center operations using purpose-built data structures, including hash-based inventory indexing, FIFO order queues, and weighted warehouse graphs. Storage locations are independent of product category, supporting a dynamic fulfillment model where unrelated products can occupy nearby bins based on available capacity rather than traditional department-based shelving.

## Features

### Inventory Management

- Index inventory by SKU for direct product lookup
- Add and remove inventory records
- Process positive and negative quantity adjustments
- Detect low-stock and out-of-stock inventory
- Flag negative inventory for physical stock reconciliation
- Prevent duplicate inventory records

### Order Processing

- Maintain pending orders using a FIFO queue
- Prevent duplicate order IDs
- Process orders against current inventory
- Validate inventory availability before fulfillment
- Preserve order and inventory state when fulfillment cannot be completed
- Track order status through the fulfillment workflow

### Warehouse Routing

- Model warehouse locations as a weighted graph
- Represent storage bins and operational areas within the same routing network
- Configure weighted connections using travel distance
- Calculate shortest pick paths between warehouse locations
- Optimize routes by total travel distance rather than number of connections
- Dynamically add and remove locations and connections

### Analytics and Capacity Planning

- Generate inventory summary reports
- Identify low-stock and out-of-stock products
- Calculate total inventory volume
- Aggregate inventory volume by storage location
- Calculate storage-location utilization against configured capacity
- Identify over-capacity and high-utilization locations
- Surface unused capacity for potential inventory consolidation
- Sort inventory by SKU or quantity for operational reporting

## Warehouse Model

The demonstration environment represents a fulfillment-style warehouse where product category does not determine storage location.

For example, neighboring bins may contain completely unrelated products such as electronics, cleaning supplies, office products, or packaging materials. This reflects a location-based storage strategy in which inventory can be placed according to available warehouse capacity while the system maintains the relationship between each SKU and its current location.

The included demonstration warehouse contains receiving, storage, packing, and shipping locations connected through weighted paths:

```text
                 RECEIVING
                     |
        A-01-01 -- A-01-02 -- A-01-03
           |          |          |
        B-01-01 -- B-01-02 -- B-01-03
           |          |          |
        C-01-01 -- C-01-02 -- C-01-03
           |          |          |
        D-01-01 -- D-01-02 -- D-01-03
                      |
                   PACKING
                      |
                   SHIPPING
```

Connection weights represent travel distance, allowing the routing engine to select the lowest-cost path through the warehouse.

## Data Structures

Several data structures are used to model different warehouse operations.

| Component | Data Structure | Purpose |
| --- | --- | --- |
| Inventory | Hash-based dictionary | Provides direct SKU-based inventory lookup and updates |
| Orders | FIFO deque | Preserves fulfillment order while supporting efficient enqueue and dequeue operations |
| Warehouse layout | Weighted undirected graph | Represents locations and travel distances for route optimization |
| Routes | Ordered location sequence | Represents the resulting path through the warehouse |
| Capacity data | Hash-based dictionary | Associates storage locations with available volume |

The structures are intentionally matched to their operational responsibilities rather than forcing unrelated warehouse behavior into a single representation.

## Route Optimization

Warehouse navigation is modeled using a weighted NetworkX graph.

Locations are represented as nodes and traversable paths as weighted edges. The routing engine calculates the shortest path according to total edge weight, meaning a route containing more intermediate locations may still be selected when its overall travel distance is shorter.

For example:

```text
RECEIVING -------- 50 -------- SHIPPING

RECEIVING -- 10 -- A -- 10 -- B -- 10 -- C -- 10 -- SHIPPING
```

Although the direct connection requires only one hop, its total distance is `50`. The multi-location route has a total distance of `40`, so the routing engine selects the longer sequence with the shorter physical travel distance.

## Demo

The repository includes an interactive command-line demonstration using representative warehouse data.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the package:

```bash
python -m pip install -e .
```

Run the demo:

```bash
python demo.py
```

The demonstration interface supports:

```text
Warehouse Operations Engine
---------------------------
1. Inventory summary
2. Low/out-of-stock items
3. Process next order
4. Find shortest route
5. Exit
```

The route interface also displays the warehouse layout before requesting start and destination locations.

## Development Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/hmw55/warehouse-operations-engine.git
cd warehouse-operations-engine
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the complete test suite:

```bash
python -m pytest
```

## Testing

The project includes a pytest suite covering domain validation, inventory operations, order processing, weighted routing, analytics, capacity planning, and demonstration-data integrity.

Current test suite:

```text
120 passed
```

Coverage includes:

- Domain-model validation and invalid-state prevention
- Duplicate inventory and order handling
- Inventory adjustments and stock reconciliation flags
- FIFO order behavior
- Successful order fulfillment
- Atomic failure behavior during unsuccessful fulfillment
- Weighted shortest-path selection
- Warehouse graph mutation
- Invalid and unreachable routing scenarios
- Inventory reporting and sorting
- Storage-volume calculations
- Capacity-utilization validation
- Space-optimization recommendations
- Independent demonstration-state generation

## Project Structure

```text
warehouse-operations-engine/
├── demo.py
├── pyproject.toml
├── src/
│   └── warehouse_operations_engine/
│       ├── __init__.py
│       ├── analytics.py
│       ├── exceptions.py
│       ├── inventory.py
│       ├── models.py
│       ├── orders.py
│       ├── routing.py
│       └── seed.py
└── tests/
    ├── test_analytics.py
    ├── test_inventory.py
    ├── test_models.py
    ├── test_orders.py
    ├── test_routing.py
    └── test_seed.py
```

## Technology

- Python 3.11+
- NetworkX
- pytest
- setuptools
- `src`-based Python package layout

## Project Background

This project originated from an implementation developed for graduate coursework focused on real-world applications of data structures.

The implementation was subsequently migrated to this standalone repository and refactored for continued development and portfolio use. The standalone version includes revised domain modeling and naming, expanded validation and automated testing, representative demonstration data, an interactive CLI demonstration, updated documentation, and removal of course-specific scenario materials.

Course instructions, assessment materials, and proprietary scenario resources are intentionally not included in this repository.

## License

No license has currently been assigned to this project.