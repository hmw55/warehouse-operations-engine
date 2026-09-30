import pytest

from warehouse_operations_engine.exceptions import (
    EmptyOrderError,
    InvalidInventoryItemError,
    InvalidOrderError,
)
from warehouse_operations_engine.models import (
    InventoryItem,
    Order,
    OrderLine,
    OrderStatus,
    PickRoute,
)

def test_inventory_item_stores_valid_inventory_data() -> None:
    item = InventoryItem(
        sku="SKU-1001",
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=25,
        reorder_level=5,
        unit_volume=0.15,
    )

    assert item.sku == "SKU-1001"
    assert item.name == "USB-C Charging Cable"
    assert item.location == "A-01-01"
    assert item.quantity == 25
    assert item.reorder_level == 5
    assert item.unit_volume == 0.15
    assert item.requires_stock_count is False


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("sku", ""),
        ("name", ""),
        ("location", ""),
    ],
)
def test_inventory_item_rejects_blank_required_fields(
    field_name: str,
    value: str,
) -> None:
    item_data = {
        "sku": "SKU-1001",
        "name": "USB-C Charging Cable",
        "location": "A-01-01",
        "quantity": 25,
        "reorder_level": 5,
        "unit_volume": 0.15,
    }
    item_data[field_name] = value

    with pytest.raises(InvalidInventoryItemError):
        InventoryItem(**item_data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("reorder_level", -1),
        ("unit_volume", 0),
        ("unit_volume", -0.1),
    ],
)
def test_inventory_item_rejects_invalid_numeric_values(
    field_name: str,
    value: int | float,
) -> None:
    item_data = {
        "sku": "SKU-1001",
        "name": "USB-C Charging Cable",
        "location": "A-01-01",
        "quantity": 25,
        "reorder_level": 5,
        "unit_volume": 0.15,
    }
    item_data[field_name] = value

    with pytest.raises(InvalidInventoryItemError):
        InventoryItem(**item_data)


def test_order_line_stores_valid_order_data() -> None:
    line = OrderLine(
        sku="SKU-1001",
        quantity=3,
    )

    assert line.sku == "SKU-1001"
    assert line.quantity == 3


@pytest.mark.parametrize("sku", ["", "   "])
def test_order_line_rejects_blank_sku(sku: str) -> None:
    with pytest.raises(InvalidOrderError):
        OrderLine(
            sku=sku,
            quantity=1,
        )


@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_order_line_rejects_nonpositive_quantity(quantity: int) -> None:
    with pytest.raises(InvalidOrderError):
        OrderLine(
            sku="SKU-1001",
            quantity=quantity,
        )


def test_order_stores_valid_order_data() -> None:
    order = Order(
        order_id="ORD-1001",
        customer_name="Jordan Lee",
        lines=[
            OrderLine(
                sku="SKU-1001",
                quantity=2,
            ),
        ],
    )

    assert order.order_id == "ORD-1001"
    assert order.customer_name == "Jordan Lee"
    assert len(order.lines) == 1
    assert order.status == OrderStatus.PENDING


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("order_id", ""),
        ("order_id", "   "),
        ("customer_name", ""),
        ("customer_name", "   "),
    ],
)
def test_order_rejects_blank_required_fields(
    field_name: str,
    value: str,
) -> None:
    order_data = {
        "order_id": "ORD-1001",
        "customer_name": "Jordan Lee",
        "lines": [
            OrderLine(
                sku="SKU-1001",
                quantity=2,
            ),
        ],
    }
    order_data[field_name] = value

    with pytest.raises(InvalidOrderError):
        Order(**order_data)


def test_order_rejects_empty_order_lines() -> None:
    with pytest.raises(EmptyOrderError):
        Order(
            order_id="ORD-1001",
            customer_name="Jordan Lee",
            lines=[],
        )


def test_pick_route_stores_route_data() -> None:
    route = PickRoute(
        locations=[
            "RECEIVING",
            "A-01-01",
            "PACKING",
        ],
        total_distance=32.5,
    )

    assert route.locations == [
        "RECEIVING",
        "A-01-01",
        "PACKING",
    ]
    assert route.total_distance == 32.5