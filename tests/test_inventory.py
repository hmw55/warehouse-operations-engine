import pytest

from warehouse_operations_engine.exceptions import (
    DuplicateInventoryItemError,
    InventoryNotFoundError,
)
from warehouse_operations_engine.inventory import (
    add_inventory_item,
    adjust_inventory,
    generate_inventory_index,
    get_inventory_item,
    remove_inventory_item,
)
from warehouse_operations_engine.models import InventoryItem


def test_generate_inventory_index_keys_items_by_sku() -> None:
    first_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    second_item = InventoryItem(
        sku="SKU-2001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )

    inventory = generate_inventory_index([first_item, second_item])

    assert inventory == {
        "SKU-1001": first_item,
        "SKU-2001": second_item,
    }


def test_generate_inventory_index_rejects_duplicate_skus() -> None:
    first_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    duplicate_item = InventoryItem(
        sku="SKU-1001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )

    with pytest.raises(
        DuplicateInventoryItemError,
        match="Inventory item with SKU 'SKU-1001' already exists.",
    ):
        generate_inventory_index([first_item, duplicate_item])


def test_get_inventory_item_returns_matching_item() -> None:
    first_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    second_item = InventoryItem(
        sku="SKU-2001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )
    inventory = generate_inventory_index([first_item, second_item])

    result = get_inventory_item(inventory, "SKU-2001")

    assert result is second_item


def test_get_inventory_item_raises_error_for_unknown_sku() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    with pytest.raises(
        InventoryNotFoundError,
        match="Inventory item with SKU 'SKU-9999' was not found.",
    ):
        get_inventory_item(inventory, "SKU-9999")


def test_add_inventory_item_adds_item_to_index() -> None:
    existing_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    new_item = InventoryItem(
        sku="SKU-2001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )
    inventory = generate_inventory_index([existing_item])

    add_inventory_item(inventory, new_item)

    assert inventory["SKU-2001"] is new_item
    assert len(inventory) == 2


def test_add_inventory_item_rejects_duplicate_sku() -> None:
    existing_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    duplicate_item = InventoryItem(
        sku="SKU-1001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )
    inventory = generate_inventory_index([existing_item])

    with pytest.raises(
        DuplicateInventoryItemError,
        match="Inventory item with SKU 'SKU-1001' already exists.",
    ):
        add_inventory_item(inventory, duplicate_item)

    assert inventory == {"SKU-1001": existing_item}


def test_remove_inventory_item_removes_and_returns_item() -> None:
    first_item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    second_item = InventoryItem(
        sku="SKU-2001",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=75,
        reorder_level=20,
        unit_volume=0.8,
    )
    inventory = generate_inventory_index([first_item, second_item])

    removed_item = remove_inventory_item(inventory, "SKU-2001")

    assert removed_item is second_item
    assert "SKU-2001" not in inventory
    assert inventory == {"SKU-1001": first_item}


def test_remove_inventory_item_raises_error_for_unknown_sku() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    with pytest.raises(
        InventoryNotFoundError,
        match="Inventory item with SKU 'SKU-9999' was not found.",
    ):
        remove_inventory_item(inventory, "SKU-9999")

    assert inventory == {"SKU-1001": item}


def test_adjust_inventory_increases_quantity_for_restocking() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    updated_item = adjust_inventory(
        inventory,
        "SKU-1001",
        50,
    )

    assert updated_item is item
    assert item.quantity == 200
    assert item.requires_stock_count is False


def test_adjust_inventory_decreases_quantity_for_shipping() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    updated_item = adjust_inventory(
        inventory,
        "SKU-1001",
        -40,
    )

    assert updated_item is item
    assert item.quantity == 110
    assert item.requires_stock_count is False


def test_adjust_inventory_flags_negative_quantity_for_stock_count() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=10,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    updated_item = adjust_inventory(
        inventory,
        "SKU-1001",
        -15,
    )

    assert updated_item is item
    assert item.quantity == -5
    assert item.requires_stock_count is True


def test_adjust_inventory_raises_error_for_unknown_sku() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=150,
        reorder_level=25,
        unit_volume=0.1,
    )
    inventory = generate_inventory_index([item])

    with pytest.raises(
        InventoryNotFoundError,
        match="Inventory item with SKU 'SKU-9999' was not found.",
    ):
        adjust_inventory(
            inventory,
            "SKU-9999",
            -10,
        )

    assert item.quantity == 150
    assert item.requires_stock_count is False