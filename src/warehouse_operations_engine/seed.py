"""Seed data for the Warehouse Operations Engine demonstration environment.

This module creates representative warehouse data for demonstrations,
documentation examples, testing, and future interface development.

Inventory is distributed across storage bins independently of product
category, reflecting a location-based fulfillment model in which unrelated
products may be stored near one another based on available capacity rather
than traditional department-based shelving.

Seed functions return new data structures on every call so warehouse state
can be modified without affecting later runs.
"""

from warehouse_operations_engine.inventory import generate_inventory_index
from warehouse_operations_engine.models import (
    DemoWarehouse,
    InventoryIndex,
    InventoryItem,
    LocationCapacityIndex,
    Order,
    OrderLine,
    OrderQueue,
    WarehouseGraph,
)
from warehouse_operations_engine.orders import (
    create_order_queue,
    enqueue_order,
)
from warehouse_operations_engine.routing import (
    add_location,
    connect_locations,
    create_warehouse_graph,
)


def seed_inventory() -> InventoryIndex:
    """Create a representative demonstration inventory index.

    Returns:
        A newly generated inventory index containing products distributed
        across multiple warehouse storage locations.

    Design Note:
        Storage locations are intentionally independent of product category.
        Unrelated products may occupy neighboring bins, reflecting a dynamic
        fulfillment model where inventory placement is based on available
        storage rather than department-based shelving.

        The dataset also includes healthy stock, low stock, reorder-boundary,
        and out-of-stock records so reporting and analytics functions can
        demonstrate a range of inventory conditions.
    """
    inventory_items = [
        InventoryItem(
            sku="CLEAN-1001",
            name="Multipurpose Cleaner",
            location="C-01-02",
            quantity=48,
            reorder_level=12,
            unit_volume=0.8,
        ),
        InventoryItem(
            sku="PAPER-2001",
            name="Paper Towels",
            location="A-01-01",
            quantity=60,
            reorder_level=20,
            unit_volume=1.4,
        ),
        InventoryItem(
            sku="OFFICE-3001",
            name="Printer Paper",
            location="D-01-03",
            quantity=35,
            reorder_level=10,
            unit_volume=0.6,
        ),
        InventoryItem(
            sku="PACK-4001",
            name="Small Shipping Boxes",
            location="B-01-02",
            quantity=80,
            reorder_level=25,
            unit_volume=1.2,
        ),
        InventoryItem(
            sku="CLEAN-1002",
            name="Disinfecting Wipes",
            location="D-01-01",
            quantity=8,
            reorder_level=10,
            unit_volume=0.45,
        ),
        InventoryItem(
            sku="OFFICE-3002",
            name="Permanent Markers",
            location="A-01-03",
            quantity=6,
            reorder_level=8,
            unit_volume=0.08,
        ),
        InventoryItem(
            sku="PAPER-2002",
            name="Toilet Paper",
            location="C-01-01",
            quantity=0,
            reorder_level=24,
            unit_volume=1.8,
        ),
        InventoryItem(
            sku="PACK-4002",
            name="Medium Shipping Boxes",
            location="A-01-02",
            quantity=30,
            reorder_level=20,
            unit_volume=2.0,
        ),
        InventoryItem(
            sku="CLEAN-1003",
            name="Glass Cleaner",
            location="B-01-03",
            quantity=15,
            reorder_level=15,
            unit_volume=0.7,
        ),
        InventoryItem(
            sku="PAPER-2003",
            name="Facial Tissues",
            location="D-01-02",
            quantity=18,
            reorder_level=12,
            unit_volume=0.9,
        ),
        InventoryItem(
            sku="OFFICE-3003",
            name="Packing Labels",
            location="B-01-01",
            quantity=22,
            reorder_level=12,
            unit_volume=0.05,
        ),
        InventoryItem(
            sku="PACK-4003",
            name="Large Shipping Boxes",
            location="C-01-03",
            quantity=12,
            reorder_level=15,
            unit_volume=3.2,
        ),
    ]

    return generate_inventory_index(inventory_items)


def seed_location_capacities() -> LocationCapacityIndex:
    """Create storage-capacity limits for warehouse inventory locations.

    Returns:
        A mapping of storage location identifiers to maximum volume capacity.

    Design Note:
        Capacity belongs to the physical storage location rather than to any
        product category. Inventory placement can therefore change over time
        while the capacity constraint for each location remains constant.
    """
    return {
        "A-01-01": 120.0,
        "A-01-02": 100.0,
        "A-01-03": 80.0,
        "B-01-01": 90.0,
        "B-01-02": 125.0,
        "B-01-03": 85.0,
        "C-01-01": 110.0,
        "C-01-02": 95.0,
        "C-01-03": 100.0,
        "D-01-01": 75.0,
        "D-01-02": 90.0,
        "D-01-03": 105.0,
    }


def seed_warehouse_graph() -> WarehouseGraph:
    """Create the demonstration warehouse routing graph.

    Returns:
        A weighted graph representing warehouse storage and operational
        locations connected by traversable paths.

    Design Note:
        Edge weights represent relative travel distance between locations.
        Storage locations are modeled independently of the inventory assigned
        to them, allowing product placement to change without modifying the
        warehouse's physical routing structure.
    """
    warehouse_graph = create_warehouse_graph()

    locations = [
        "RECEIVING",
        "A-01-01",
        "A-01-02",
        "A-01-03",
        "B-01-01",
        "B-01-02",
        "B-01-03",
        "C-01-01",
        "C-01-02",
        "C-01-03",
        "D-01-01",
        "D-01-02",
        "D-01-03",
        "PACKING",
        "SHIPPING",
    ]

    for location in locations:
        add_location(warehouse_graph, location)

    connections = [
        ("RECEIVING", "A-01-01", 2.0),
        ("A-01-01", "A-01-02", 1.0),
        ("A-01-02", "A-01-03", 1.0),
        ("A-01-01", "B-01-01", 2.0),
        ("A-01-02", "B-01-02", 2.0),
        ("A-01-03", "B-01-03", 2.0),
        ("B-01-01", "B-01-02", 1.0),
        ("B-01-02", "B-01-03", 1.0),
        ("B-01-01", "C-01-01", 2.0),
        ("B-01-02", "C-01-02", 2.0),
        ("B-01-03", "C-01-03", 2.0),
        ("C-01-01", "C-01-02", 1.0),
        ("C-01-02", "C-01-03", 1.0),
        ("C-01-01", "D-01-01", 2.0),
        ("C-01-02", "D-01-02", 2.0),
        ("C-01-03", "D-01-03", 2.0),
        ("D-01-01", "D-01-02", 1.0),
        ("D-01-02", "D-01-03", 1.0),
        ("D-01-02", "PACKING", 2.0),
        ("PACKING", "SHIPPING", 1.0),
    ]

    for start, end, distance in connections:
        connect_locations(
            warehouse_graph,
            start,
            end,
            distance=distance,
        )

    return warehouse_graph


def seed_order_queue() -> OrderQueue:
    """Create a demonstration queue of customer orders awaiting fulfillment.

    Returns:
        A FIFO order queue containing representative customer orders.

    Design Note:
        Orders contain products stored across different warehouse locations,
        demonstrating how fulfillment may require travel through multiple
        storage areas rather than picking from a single product-specific aisle.
    """
    order_queue = create_order_queue()

    orders = [
        Order(
            order_id="ORD-1001",
            customer_name="Jordan Lee",
            lines=[
                OrderLine(sku="CLEAN-1001", quantity=2),
                OrderLine(sku="OFFICE-3002", quantity=3),
                OrderLine(sku="PACK-4001", quantity=4),
            ],
        ),
        Order(
            order_id="ORD-1002",
            customer_name="Morgan Patel",
            lines=[
                OrderLine(sku="PAPER-2001", quantity=6),
                OrderLine(sku="OFFICE-3001", quantity=2),
            ],
        ),
        Order(
            order_id="ORD-1003",
            customer_name="Casey Nguyen",
            lines=[
                OrderLine(sku="PAPER-2003", quantity=3),
                OrderLine(sku="OFFICE-3003", quantity=5),
                OrderLine(sku="PACK-4002", quantity=2),
            ],
        ),
    ]

    for order in orders:
        enqueue_order(order_queue, order)

    return order_queue


def seed_demo_warehouse() -> DemoWarehouse:
    """Create a complete demonstration warehouse environment.

    Returns:
        A newly initialized warehouse containing inventory, queued orders,
        location capacities, and the warehouse routing graph.
    """
    return DemoWarehouse(
        inventory=seed_inventory(),
        order_queue=seed_order_queue(),
        warehouse_graph=seed_warehouse_graph(),
        location_capacities=seed_location_capacities(),
    )