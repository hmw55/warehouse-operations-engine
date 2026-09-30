import pytest

from warehouse_operations_engine.analytics import (
    calculate_inventory_volume_by_location,
    calculate_location_utilization,
    calculate_total_inventory_volume,
    generate_inventory_report,
    get_inventory_sorted_by_quantity,
    get_inventory_sorted_by_sku,
    get_low_stock_items,
    get_out_of_stock_items,
    suggest_space_optimizations,
)
from warehouse_operations_engine.exceptions import InvalidLocationCapacityError
from warehouse_operations_engine.inventory import adjust_inventory
from warehouse_operations_engine.models import InventoryItem


def make_item(
    sku: str = "SKU-100",
    name: str = "USB-C Charging Cable",
    location: str = "A-01-01",
    quantity: int = 20,
    reorder_level: int = 10,
    unit_volume: float = 0.25,
) -> InventoryItem:
    """Create an inventory item for analytics tests."""
    return InventoryItem(
        sku=sku,
        name=name,
        location=location,
        quantity=quantity,
        reorder_level=reorder_level,
        unit_volume=unit_volume,
    )


def make_inventory(*items: InventoryItem) -> dict[str, InventoryItem]:
    """Create an inventory index from the supplied items."""
    return {item.sku: item for item in items}


def test_generate_inventory_report_summarizes_inventory() -> None:
    first_item = make_item(
        sku="SKU-100",
        quantity=40,
        reorder_level=10,
    )
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="C-01-02",
        quantity=15,
        reorder_level=5,
        unit_volume=1.5,
    )

    report = generate_inventory_report(
        make_inventory(first_item, second_item)
    )

    assert report.total_items == 2
    assert report.total_quantity == 55
    assert report.items_to_reorder == []


def test_generate_inventory_report_identifies_items_at_or_below_reorder_level() -> None:
    below_level = make_item(
        sku="SKU-100",
        quantity=4,
        reorder_level=10,
    )
    at_level = make_item(
        sku="SKU-200",
        name="Permanent Markers",
        location="D-01-01",
        quantity=5,
        reorder_level=5,
    )
    healthy_item = make_item(
        sku="SKU-300",
        name="Ceramic Coffee Mug",
        location="B-01-03",
        quantity=20,
        reorder_level=5,
    )

    report = generate_inventory_report(
        make_inventory(below_level, at_level, healthy_item)
    )

    assert report.items_to_reorder == [
        below_level,
        at_level,
    ]


def test_generate_inventory_report_handles_empty_inventory() -> None:
    report = generate_inventory_report({})

    assert report.total_items == 0
    assert report.total_quantity == 0
    assert report.items_to_reorder == []


def test_calculate_total_inventory_volume_sums_positive_inventory() -> None:
    first_item = make_item(
        sku="SKU-100",
        quantity=40,
        unit_volume=0.25,
    )
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="C-01-02",
        quantity=15,
        unit_volume=1.5,
    )

    total_volume = calculate_total_inventory_volume(
        make_inventory(first_item, second_item)
    )

    assert total_volume == 32.5


def test_calculate_total_inventory_volume_returns_zero_for_empty_inventory() -> None:
    assert calculate_total_inventory_volume({}) == 0.0


def test_calculate_total_inventory_volume_ignores_zero_quantity() -> None:
    item = make_item(quantity=0)

    assert calculate_total_inventory_volume(
        make_inventory(item)
    ) == 0.0


def test_calculate_total_inventory_volume_ignores_negative_quantity() -> None:
    negative_item = make_item(
        sku="SKU-100",
        quantity=5,
    )
    positive_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="C-01-02",
        quantity=10,
        unit_volume=1.5,
    )
    inventory = make_inventory(negative_item, positive_item)

    adjust_inventory(
        inventory,
        negative_item.sku,
        -10,
    )

    total_volume = calculate_total_inventory_volume(inventory)

    assert negative_item.quantity == -5
    assert negative_item.requires_stock_count is True
    assert total_volume == 15.0


def test_get_low_stock_items_returns_items_at_or_below_reorder_level() -> None:
    below_level = make_item(
        sku="SKU-100",
        quantity=5,
        reorder_level=10,
    )
    healthy_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="C-01-02",
        quantity=20,
        reorder_level=5,
    )
    at_level = make_item(
        sku="SKU-300",
        name="Permanent Markers",
        location="D-01-01",
        quantity=8,
        reorder_level=8,
    )

    result = get_low_stock_items(
        make_inventory(below_level, healthy_item, at_level)
    )

    assert result == [
        below_level,
        at_level,
    ]


def test_get_low_stock_items_returns_empty_list_when_stock_is_sufficient() -> None:
    item = make_item(
        quantity=20,
        reorder_level=10,
    )

    assert get_low_stock_items(make_inventory(item)) == []


def test_get_low_stock_items_returns_new_list() -> None:
    item = make_item(
        quantity=5,
        reorder_level=10,
    )
    inventory = make_inventory(item)

    first_result = get_low_stock_items(inventory)
    second_result = get_low_stock_items(inventory)

    assert first_result == second_result
    assert first_result is not second_result


def test_get_out_of_stock_items_returns_zero_quantity_items() -> None:
    out_of_stock = make_item(
        sku="SKU-100",
        quantity=0,
    )
    available = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="C-01-02",
        quantity=15,
    )

    result = get_out_of_stock_items(
        make_inventory(out_of_stock, available)
    )

    assert result == [out_of_stock]


def test_get_out_of_stock_items_returns_negative_quantity_items() -> None:
    item = make_item(quantity=5)
    inventory = make_inventory(item)

    adjust_inventory(
        inventory,
        item.sku,
        -10,
    )

    result = get_out_of_stock_items(inventory)

    assert item.quantity == -5
    assert item.requires_stock_count is True
    assert result == [item]


def test_get_out_of_stock_items_excludes_positive_low_stock_items() -> None:
    item = make_item(
        quantity=3,
        reorder_level=10,
    )

    assert get_out_of_stock_items(
        make_inventory(item)
    ) == []


def test_get_out_of_stock_items_returns_empty_list_for_empty_inventory() -> None:
    assert get_out_of_stock_items({}) == []


def test_get_inventory_sorted_by_sku_returns_ascending_sku_order() -> None:
    third_item = make_item(
        sku="SKU-300",
        name="Laptop Stand",
        location="A-01-03",
    )
    first_item = make_item(
        sku="SKU-100",
        name="USB-C Charging Cable",
        location="C-01-01",
    )
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="B-01-02",
    )
    inventory = make_inventory(
        third_item,
        first_item,
        second_item,
    )

    result = get_inventory_sorted_by_sku(inventory)

    assert [item.sku for item in result] == [
        "SKU-100",
        "SKU-200",
        "SKU-300",
    ]


def test_get_inventory_sorted_by_sku_returns_empty_list_for_empty_inventory() -> None:
    assert get_inventory_sorted_by_sku({}) == []


def test_get_inventory_sorted_by_sku_returns_new_list() -> None:
    item = make_item()
    inventory = make_inventory(item)

    first_result = get_inventory_sorted_by_sku(inventory)
    second_result = get_inventory_sorted_by_sku(inventory)

    assert first_result == second_result
    assert first_result is not second_result


def test_get_inventory_sorted_by_sku_does_not_modify_inventory_index() -> None:
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
    )
    first_item = make_item(
        sku="SKU-100",
        name="USB-C Charging Cable",
    )
    inventory = make_inventory(second_item, first_item)
    original_keys = list(inventory)

    get_inventory_sorted_by_sku(inventory)

    assert list(inventory) == original_keys


def test_get_inventory_sorted_by_quantity_returns_lowest_quantity_first() -> None:
    high_stock = make_item(
        sku="SKU-100",
        quantity=20,
    )
    negative_stock = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="B-01-02",
        quantity=2,
    )
    zero_stock = make_item(
        sku="SKU-300",
        name="Laptop Stand",
        location="D-01-03",
        quantity=0,
    )
    inventory = make_inventory(
        high_stock,
        negative_stock,
        zero_stock,
    )

    adjust_inventory(
        inventory,
        negative_stock.sku,
        -4,
    )

    result = get_inventory_sorted_by_quantity(inventory)

    assert [item.quantity for item in result] == [
        -2,
        0,
        20,
    ]


def test_get_inventory_sorted_by_quantity_uses_sku_as_tiebreaker() -> None:
    second_item = make_item(
        sku="SKU-200",
        quantity=10,
    )
    first_item = make_item(
        sku="SKU-100",
        quantity=10,
    )

    result = get_inventory_sorted_by_quantity(
        make_inventory(second_item, first_item)
    )

    assert [item.sku for item in result] == [
        "SKU-100",
        "SKU-200",
    ]


def test_get_inventory_sorted_by_quantity_returns_empty_list_for_empty_inventory() -> None:
    assert get_inventory_sorted_by_quantity({}) == []


def test_get_inventory_sorted_by_quantity_does_not_modify_inventory_index() -> None:
    low_stock = make_item(
        sku="SKU-200",
        quantity=5,
    )
    high_stock = make_item(
        sku="SKU-100",
        quantity=20,
    )
    inventory = make_inventory(low_stock, high_stock)
    original_keys = list(inventory)

    get_inventory_sorted_by_quantity(inventory)

    assert list(inventory) == original_keys


def test_calculate_inventory_volume_by_location_groups_items_by_location() -> None:
    first_item = make_item(
        sku="SKU-100",
        location="A-01-01",
        quantity=20,
        unit_volume=0.25,
    )
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="A-01-01",
        quantity=10,
        unit_volume=0.75,
    )
    third_item = make_item(
        sku="SKU-300",
        name="Laptop Stand",
        location="B-01-01",
        quantity=4,
        unit_volume=1.5,
    )

    result = calculate_inventory_volume_by_location(
        make_inventory(first_item, second_item, third_item)
    )

    assert result == {
        "A-01-01": 12.5,
        "B-01-01": 6.0,
    }


def test_calculate_inventory_volume_by_location_includes_zero_quantity_location() -> None:
    item = make_item(
        location="A-01-01",
        quantity=0,
    )

    result = calculate_inventory_volume_by_location(
        make_inventory(item)
    )

    assert result == {
        "A-01-01": 0.0,
    }


def test_calculate_inventory_volume_by_location_ignores_negative_quantity() -> None:
    negative_item = make_item(
        sku="SKU-100",
        location="A-01-01",
        quantity=5,
    )
    positive_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="B-01-01",
        quantity=4,
        unit_volume=1.5,
    )
    inventory = make_inventory(
        negative_item,
        positive_item,
    )

    adjust_inventory(
        inventory,
        negative_item.sku,
        -10,
    )

    result = calculate_inventory_volume_by_location(inventory)

    assert result == {
        "A-01-01": 0.0,
        "B-01-01": 6.0,
    }


def test_calculate_inventory_volume_by_location_returns_empty_dictionary() -> None:
    assert calculate_inventory_volume_by_location({}) == {}


def test_calculate_location_utilization_returns_percentage_by_location() -> None:
    first_item = make_item(
        sku="SKU-100",
        location="A-01-01",
        quantity=20,
        unit_volume=0.25,
    )
    second_item = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="B-01-01",
        quantity=10,
        unit_volume=1.5,
    )

    result = calculate_location_utilization(
        make_inventory(first_item, second_item),
        {
            "A-01-01": 10.0,
            "B-01-01": 20.0,
        },
    )

    assert result == {
        "A-01-01": 50.0,
        "B-01-01": 75.0,
    }


def test_calculate_location_utilization_includes_empty_configured_location() -> None:
    result = calculate_location_utilization(
        {},
        {
            "A-01-01": 10.0,
        },
    )

    assert result == {
        "A-01-01": 0.0,
    }


@pytest.mark.parametrize("capacity", [0, -1, -10.5])
def test_calculate_location_utilization_rejects_nonpositive_capacity(
    capacity: float,
) -> None:
    with pytest.raises(
        InvalidLocationCapacityError,
        match="Location capacity must be greater than zero for: A-01-01.",
    ):
        calculate_location_utilization(
            {},
            {
                "A-01-01": capacity,
            },
        )


def test_calculate_location_utilization_rejects_missing_capacity() -> None:
    item = make_item(
        location="A-01-01",
        quantity=20,
    )

    with pytest.raises(
        InvalidLocationCapacityError,
        match="Location capacity is not configured for: A-01-01.",
    ):
        calculate_location_utilization(
            make_inventory(item),
            {},
        )


def test_suggest_space_optimizations_identifies_over_capacity_location() -> None:
    item = make_item(
        location="A-01-01",
        quantity=10,
        unit_volume=1.5,
    )

    result = suggest_space_optimizations(
        make_inventory(item),
        {
            "A-01-01": 10.0,
        },
    )

    assert result == {
        "A-01-01": (
            "Relocate inventory because this location exceeds capacity."
        ),
    }


def test_suggest_space_optimizations_identifies_high_utilization_location() -> None:
    item = make_item(
        location="A-01-01",
        quantity=6,
        unit_volume=1.5,
    )

    result = suggest_space_optimizations(
        make_inventory(item),
        {
            "A-01-01": 10.0,
        },
    )

    assert result == {
        "A-01-01": (
            "Review this location because utilization is at least 90%."
        ),
    }


def test_suggest_space_optimizations_identifies_unused_location() -> None:
    result = suggest_space_optimizations(
        {},
        {
            "A-01-01": 10.0,
        },
    )

    assert result == {
        "A-01-01": (
            "Consider consolidating inventory into this unused location."
        ),
    }


def test_suggest_space_optimizations_excludes_healthy_location() -> None:
    item = make_item(
        location="A-01-01",
        quantity=20,
        unit_volume=0.25,
    )

    result = suggest_space_optimizations(
        make_inventory(item),
        {
            "A-01-01": 10.0,
        },
    )

    assert result == {}


def test_suggest_space_optimizations_returns_multiple_recommendations() -> None:
    over_capacity = make_item(
        sku="SKU-100",
        location="A-01-01",
        quantity=10,
        unit_volume=1.5,
    )
    healthy = make_item(
        sku="SKU-200",
        name="Ceramic Coffee Mug",
        location="B-01-01",
        quantity=20,
        unit_volume=0.25,
    )

    result = suggest_space_optimizations(
        make_inventory(over_capacity, healthy),
        {
            "A-01-01": 10.0,
            "B-01-01": 10.0,
            "C-01-01": 10.0,
        },
    )

    assert result == {
        "A-01-01": (
            "Relocate inventory because this location exceeds capacity."
        ),
        "C-01-01": (
            "Consider consolidating inventory into this unused location."
        ),
    }