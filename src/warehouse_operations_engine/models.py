"""
Domain models for the Warehouse Operations Engine.

This module defines the core business objects shared throughout the
warehouse management system. These models represent inventory records,
customer orders, routing results, and reporting data without containing
business logic.

Keeping the domain models separate from the application logic promotes
consistency, maintainability, and type safety throughout the project.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from warehouse_operations_engine.exceptions import (
    EmptyOrderError,
    InvalidInventoryItemError,
    InvalidOrderError,
)


class OrderStatus(str, Enum):
    """Represent the lifecycle states of a customer order."""

    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


@dataclass(slots=True)
class InventoryItem:
    """Represent one product record in warehouse inventory.

    Each instance stores the information required to identify a product,
    track its available quantity, and support warehouse operations such as
    inventory adjustments, reporting, and order fulfillment.

    The SKU serves as the item's stable identifier and should not be
    reassigned after the record is created.

    Attributes:
        sku: Unique stock-keeping unit used to index the item.
        name: Human-readable product name.
        quantity: Current number of units in stock.
        reorder_level: Quantity at or below which restocking is recommended.
        location: Warehouse location where the product is stored.
        unit_volume: Storage volume occupied by one unit of the product.
        requires_stock_count: Whether the recorded quantity requires physical
            inventory verification. See design note.
    """

    sku: str
    name: str
    location: str
    quantity: int
    reorder_level: int
    unit_volume: float
    # ----------------------------------------------------------------------
    # Design Note
    #
    # Negative inventory is allowed because it represents a discrepancy between
    # recorded inventory and physical inventory rather than an impossible state.
    # 
    # Preventing the quantity from becoming negative could hide inventory
    # inaccuracies caused by missed scans, receiving errors, or delayed audits.
    # Instead, the inventory is updated and the item is flagged for a stock count.
    # 
    # In a production warehouse management system, this responsibility would likely
    # belong to a dedicated inventory reconciliation or audit service. It is
    # implemented here to keep the project self-contained while demonstrating the
    # underlying business rule.
    # ----------------------------------------------------------------------
    requires_stock_count: bool = field(
        default=False,
        init=False,
    )

    def __post_init__(self) -> None:
        """Validate the inventory item after initialization.
        
        Raises:
            InvalidInventoryItemError: If any required value is invalid.
        """

        if not self.sku.strip():
            raise InvalidInventoryItemError(
                "SKU cannot be blank."
            )

        if not self.name.strip():
            raise InvalidInventoryItemError(
                "Item name cannot be blank."
            )

        if not self.location.strip():
            raise InvalidInventoryItemError(
                "Location cannot be blank."
            )

        if self.quantity < 0:
            raise InvalidInventoryItemError(
                "Initial inventory quantity cannot be negative."
            )

        if self.reorder_level < 0:
            raise InvalidInventoryItemError(
                "Reorder level cannot be negative."
            )

        if self.unit_volume <= 0:
            raise InvalidInventoryItemError(
                "Unit volume must be greater than zero."
            )


@dataclass(slots=True)
class OrderLine:
    """Represent a single item requested within a customer order.
    
    Attributes:
        sku: SKU identifying the requested inventory item.
        quantity: Number of units requested.
    """

    sku: str
    quantity: int

    def __post_init__(self) -> None:
        """Validate the order line after initialization.
        
        Raises:
            InvalidOrderError: If the SKU or requested quantity is invalid.
        """

        if not self.sku.strip():
            raise InvalidOrderError(
                "Order line SKU cannot be blank."
            )
        
        if self.quantity <= 0:
            raise InvalidOrderError(
                "Order line quantity must be greater than zero."
            )


@dataclass(slots=True)
class Order:
    """Represent a customer order awaiting warehouse fulfillment.
    
    Attributes:
        order_id: Unique identifier assigned to the order.
        customer_name: Name of the customer who placed the order.
        lines: Collection of items requested by the customer.
        status: Current stage in the order fulfillment process.
    """

    order_id: str
    customer_name: str
    lines: list[OrderLine]
    status: OrderStatus = OrderStatus.PENDING

    def __post_init__(self) -> None:
        """Validate the order after initialization.
        
        Raises:
            InvalidOrderError: If the order identifier is invalid.
            EmptyOrderError: If the order contains no order lines.
        """

        if not self.order_id.strip():
            raise InvalidOrderError(
                "Order ID cannot be blank."
            )
        
        if not self.customer_name.strip():
            raise InvalidOrderError(
                "Customer name cannot be blank."
            )
        
        if not self.lines:
            raise EmptyOrderError(
                "Orders must contain at least one order line."
            )


@dataclass(slots=True)
class PickRoute:
    """Represent an optimized route through warehouse locations.
    
    Attributes:
        locations: Ordered warehouse locations included in the route.
        total_distance: Total weighted walking distance for the route.

    Design Note:
        The route is represented as domain model rather than a raw tuple
        so additional routing details, such as estimated walking time or
        stops counts, can be added later without changing the function's
        return structure
    """

    locations: list[str]
    total_distance: float


@dataclass(slots=True)
class InventoryReport:
    """Summarize the current state of warehouse inventory.
    
    Attributes: 
        total_items: Number of unique inventory records.
        total_quantity: Total quantity of all units in stock.
        items_to_reorder: Inventory items at or below their reorder level.
    """

    total_items: int
    total_quantity: int
    items_to_reorder: list[InventoryItem]


# -------------------------------------------------------
# Shared Type Aliases
# -------------------------------------------------------

InventoryIndex: TypeAlias = dict[str, InventoryItem]
"""Dictionary mapping SKUs to inventory records."""

OrderQueue: TypeAlias = deque[Order]
"""Queue of customer orders awaiting fulfillment."""

WarehouseGraph: TypeAlias = dict[str, dict[str, float]]
"""Weighted graph representing warehouse locations and travel distances."""

LocationCapacityIndex: TypeAlias = dict[str, float]
"""Dictionary mapping warehouse locations to maximum storage volume."""


@dataclass(slots=True)
class DemoWarehouse:
    """Represent a fully initialized demonstration warehouse.

    Attributes:
        inventory: Inventory records keyed by SKU.
        order_queue: FIFO queue of customer orders.
        warehouse_graph: Warehouse routing graph.
        location_capacities: Storage capacities keyed by location.
    """

    inventory: InventoryIndex
    order_queue: OrderQueue
    warehouse_graph: WarehouseGraph
    location_capacities: LocationCapacityIndex