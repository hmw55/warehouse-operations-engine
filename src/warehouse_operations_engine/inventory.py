"""
Inventory management operations for the Warehouse Operations Engine.

This module contains the business logic responsible for creating,
retrieving, updating, and removing inventory records while maintaining
inventory integrity throughout the warehouse system.
"""

from __future__ import annotations

from warehouse_operations_engine.exceptions import (
    DuplicateInventoryItemError,
    InventoryNotFoundError,
)
from warehouse_operations_engine.models import (
    InventoryIndex,
    InventoryItem,
)


# -------------------------------------------------
# Inventory Index Operations
# -------------------------------------------------

def generate_inventory_index(
    inventory_items: list[InventoryItem],
) -> InventoryIndex:
    """
    Build an inventory index keyed by each item's SKU.

    Args:
        inventory_items: Inventory records to include in the index.

    Returns:
        A dictionary mapping each SKU to its inventory item.

    Raises:
        DuplicateInventoryItemError:
            If more than one inventory item has the same SKU.
    """

    inventory: InventoryIndex = {}

    for item in inventory_items:
        if item.sku in inventory:
            raise DuplicateInventoryItemError(
                f"Inventory item with SKU '{item.sku}' already exists."
            )
        
        inventory[item.sku] = item

    return inventory


def get_inventory_item(
    inventory: InventoryIndex,
    sku: str,
) -> InventoryItem:
    """
    Retrieve an inventory item by SKU.

    Args:
        inventory: Inventory records keyed by SKU.
        sku: SKU of the inventory item to retrieve.

    Returns:
        The inventory item associated with the SKU.

    Raises:
        InventoryNotFoundError:
            If no inventory item exists with the provided SKU.
    """

    try:
        return inventory[sku]
    except KeyError as error:
        raise InventoryNotFoundError(
            f"Inventory item with SKU '{sku}' was not found."
        ) from error
    

def add_inventory_item(
        inventory: InventoryIndex,
        item: InventoryItem,
) -> None:
    """
    Add an inventory item to the inventory index.

    Args: 
        inventory: Inventory records keyed by SKU.
        item: Inventory item to add. 

    Raises: 
        DuplicateInventoryItemError: 
            If an inventory item with the same SKU already exists.
    """

    if item.sku in inventory: 
        raise DuplicateInventoryItemError(
            f"Inventory item with SKU '{item.sku}' already exists."
        )
    
    inventory[item.sku] = item


def remove_inventory_item(
        inventory: InventoryIndex,
        sku: str,
) -> InventoryItem:
    """
    Remove an inventory item from the inventory index.

    Args:
        inventory: Inventory records keyed by SKU.
        sku: SKU of the inventory item to remove.

    Returns:
        The inventory item that was removed.

    Raises:
        InventoryNotFoundError:
            If no inventory item exists with the provided SKU.
    """

    try:
        return inventory.pop(sku)
    except KeyError as error:
        raise InventoryNotFoundError(
            f"Inventory item with SKU '{sku}' was not found."
        ) from error
    

def adjust_inventory(
    inventory: InventoryIndex,
    sku: str,
    quantity_change: int,
) -> InventoryItem:
    """
    Adjust the recorded quantity of an inventory item.

    Positive values represent incoming inventory, such as restocking.
    Negative values represent outgoing inventory, such as shipping,
    damage, or inventory corrections.

    A resulting negative quantity is preserved because it may reveal a
    discrepancy between recorded and physical inventory. The item is then
    flagged as requiring a physical stock count.

    Args:
        inventory: Inventory records keyed by SKU.
        sku: SKU of the inventory item to adjust.
        quantity_change: Number of units to add or subtract.

    Returns:
        The updated inventory item.

    Raises:
        InventoryNotFoundError:
            If no inventory item exists with the provided SKU.
    """

    item = get_inventory_item(
        inventory,
        sku,
    )

    item.quantity += quantity_change
    item.requires_stock_count = item.quantity < 0

    return item
