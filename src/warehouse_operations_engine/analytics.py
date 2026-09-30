"""
Reporting and analytical operations for warehouse inventory.

This module transforms warehouse inventory records into summaries that
support operational reporting and management decision-making. Analytics
functions operate on the inventory index without modifying the underlying
inventory records or dictionary structure.
"""

from __future__ import annotations

from math import fsum

from warehouse_operations_engine.exceptions import (
    InvalidLocationCapacityError,
)
from warehouse_operations_engine.models import (
    InventoryIndex,
    InventoryItem,
    InventoryReport,
    LocationCapacityIndex,
)


def get_low_stock_items(
    inventory_index: InventoryIndex,
) -> list[InventoryItem]:
    """Return inventory items that require replenishment.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A new list containing every inventory item whose recorded quantity
        is at or below its configured reorder level.

    Design Note:
        This function centralizes the warehouse's low-stock business rule.
        Other analytics functions should call this helper rather than
        duplicating the reorder comparison logic.
    """
    return [
        item
        for item in inventory_index.values()
        if item.quantity <= item.reorder_level
    ]


def get_out_of_stock_items(
        inventory_index: InventoryIndex,
) -> list[InventoryItem]:
    """Return inventory items with no available recorded stock.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A new list containing every inventory item whose recorded quantity
        is zero or negative.

    Design Note:
        Negative quantities represent unresolved inventory discrepancies,
        but they still indicate that no reliable stock is available for
        order fulfillment. Therefore, both zero and negative quantities are
        classified as out of stock.
    """
    return [
        item
        for item in inventory_index.values()
        if item.quantity <= 0
    ]


def generate_inventory_report(
    inventory_index: InventoryIndex,
) -> InventoryReport:
    """Generate a summary of the current warehouse inventory.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A report containing the number of unique inventory records, the
        total quantity in stock, and all items requiring reorder.

    Design Note:
        The inventory index remains optimized for direct SKU-based access,
        while this function iterates through its values to produce a
        sequential analytics summary. The source inventory is not modified.
    """
    inventory_items = list(inventory_index.values())

    return InventoryReport(
        total_items=len(inventory_items),
        total_quantity=sum(
            item.quantity
            for item in inventory_items
        ),
        items_to_reorder=get_low_stock_items(
            inventory_index,
        ),
    )


def calculate_total_inventory_volume(
    inventory_index: InventoryIndex,
) -> float:
    """Calculate the total storage volume occupied by inventory.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        The combined storage volume occupied by all inventory with a
        positive recorded quantity.

    Design Note:
        Inventory quantities may become negative when warehouse records
        indicate a stock discrepancy. A negative quantity represents the
        need for physical verification rather than negative physical stock.
        Therefore, negative quantities contribute zero to occupied storage
        volume instead of reducing the volume of other inventory.
    """
    return fsum(
        max(item.quantity, 0) * item.unit_volume
        for item in inventory_index.values()
    )

def get_inventory_sorted_by_sku(
    inventory_index: InventoryIndex,
) -> list[InventoryItem]:
    """Return inventory items ordered by SKU.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A new list containing inventory items in ascending SKU order.

    Design Note:
        The inventory index remains a dictionary for efficient key-based
        access. A separate sorted list is created only when ordered reporting
        is required, preserving the performance characteristics of the
        underlying inventory structure.
    """
    return sorted(
        inventory_index.values(),
        key=lambda item: item.sku,
    )


def get_inventory_sorted_by_quantity(
    inventory_index: InventoryIndex,
) -> list[InventoryItem]:
    """Return inventory items ordered by quantity from lowest to highest.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A new list containing inventory items in ascending quantity order.

    Design Note:
        Sorting by quantity places shortages, stock discrepancies, and
        low-stock items near the beginning of operational reports while
        preserving the dictionary used for direct SKU access.
    """
    return sorted(
        inventory_index.values(),
        key=lambda item: (item.quantity, item.sku),
    )


def calculate_inventory_volume_by_location(
    inventory_index: InventoryIndex,
) -> dict[str, float]:
    """Calculate occupied inventory volume for each warehouse location.

    Args:
        inventory_index: Inventory records keyed by SKU.

    Returns:
        A dictionary mapping each warehouse location to the combined volume
        occupied by inventory stored at that location.

    Design Note:
        Negative inventory quantities represent unresolved discrepancies,
        not negative physical stock. They therefore contribute zero occupied
        volume while the item's location remains represented in the result.

        This function summarizes recorded inventory placement rather than
        total location capacity. Capacity-based utilization percentages would
        require a separate model containing each location's maximum volume.
    """
    volume_by_location: dict[str, list[float]] = {}

    for item in inventory_index.values():
        item_volume = max(item.quantity, 0) * item.unit_volume

        volume_by_location.setdefault(
            item.location,
            [],
        ).append(item_volume)

    return {
        location: fsum(volumes)
        for location, volumes in volume_by_location.items()
    }


def calculate_location_utilization(
    inventory_index: InventoryIndex,
    location_capacities: LocationCapacityIndex,
) -> dict[str, float]:
    """Calculate storage utilization percentages by warehouse location.

    Args:
        inventory_index: Inventory records keyed by SKU.
        location_capacities: Maximum storage volume keyed by location.

    Returns:
        A dictionary mapping each configured location to its utilization
        percentage.

    Raises:
        InvalidLocationCapacityError: If a capacity is zero or negative.
        InvalidLocationCapacityError: If inventory references a location
            without configured capacity.

    Design Note:
        Utilization requires both occupied volume and maximum capacity.
        Keeping capacity separate from inventory records allows multiple
        products stored in the same location to share one physical limit.
    """
    invalid_locations = [
        location
        for location, capacity in location_capacities.items()
        if capacity <= 0
    ]

    if invalid_locations:
        invalid_location_list = ", ".join(invalid_locations)
        raise InvalidLocationCapacityError(
            "Location capacity must be greater than zero for: "
            f"{invalid_location_list}."
        )

    volume_by_location = calculate_inventory_volume_by_location(
        inventory_index,
    )

    missing_capacity_locations = [
        location
        for location in volume_by_location
        if location not in location_capacities
    ]

    if missing_capacity_locations:
        missing_location_list = ", ".join(
            missing_capacity_locations,
        )
        raise InvalidLocationCapacityError(
            "Location capacity is not configured for: "
            f"{missing_location_list}."
        )

    return {
        location: (
            volume_by_location.get(location, 0.0)
            / capacity
            * 100.0
        )
        for location, capacity in location_capacities.items()
    }


def suggest_space_optimizations(
    inventory_index: InventoryIndex,
    location_capacities: LocationCapacityIndex,
) -> dict[str, str]:
    """Suggest actions for warehouse locations needing space review.

    Args:
        inventory_index: Inventory records keyed by SKU.
        location_capacities: Maximum storage volume keyed by location.

    Returns:
        A dictionary mapping locations requiring attention to suggested
        warehouse actions.

    Raises:
        InvalidLocationCapacityError: If location capacity data is invalid.

    Design Note:
        Recommendations are intentionally rule-based and explainable. Only
        locations requiring attention are returned so operational reports
        remain focused rather than listing healthy locations unnecessarily.
    """
    utilization_by_location = calculate_location_utilization(
        inventory_index,
        location_capacities,
    )

    suggestions: dict[str, str] = {}

    for location, utilization in utilization_by_location.items():
        if utilization > 100:
            suggestions[location] = (
                "Relocate inventory because this location exceeds capacity."
            )
        elif utilization >= 90:
            suggestions[location] = (
                "Review this location because utilization is at least 90%."
            )
        elif utilization == 0:
            suggestions[location] = (
                "Consider consolidating inventory into this unused location."
            )

    return suggestions