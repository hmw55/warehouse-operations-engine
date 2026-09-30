from collections import deque

import pytest

from warehouse_operations_engine.exceptions import (
    DuplicateOrderError,
    EmptyOrderError,
    InsufficientInventoryError,
    InventoryNotFoundError,
)
from warehouse_operations_engine.inventory import generate_inventory_index
from warehouse_operations_engine.models import (
    InventoryItem,
    Order,
    OrderLine,
    OrderStatus,
)
from warehouse_operations_engine.orders import (
    create_order_queue,
    dequeue_order,
    enqueue_order,
    peek_next_order,
    process_order,
)


def make_order(
    order_id: str = "ORD-1001",
    customer_name: str = "Jordan Lee",
    sku: str = "SKU-1001",
    quantity: int = 1,
) -> Order:
    """Create an order with one line for use in order-operation tests."""
    return Order(
        order_id=order_id,
        customer_name=customer_name,
        lines=[
            OrderLine(
                sku=sku,
                quantity=quantity,
            ),
        ],
    )


def make_inventory_item(
    sku: str = "SKU-1001",
    quantity: int = 10,
) -> InventoryItem:
    """Create an inventory item for use in fulfillment tests."""
    return InventoryItem(
        sku=sku,
        name="USB-C Charging Cable",
        location="A-01-01",
        quantity=quantity,
        reorder_level=5,
        unit_volume=0.1,
    )


def test_create_order_queue_returns_empty_deque() -> None:
    order_queue = create_order_queue()

    assert isinstance(order_queue, deque)
    assert len(order_queue) == 0


def test_enqueue_order_adds_order_to_end_of_queue() -> None:
    order_queue = create_order_queue()
    order = make_order()

    enqueue_order(order_queue, order)

    assert list(order_queue) == [order]


def test_enqueue_order_rejects_duplicate_order_id() -> None:
    order_queue = create_order_queue()
    first_order = make_order(order_id="ORD-1001")
    duplicate_order = make_order(
        order_id="ORD-1001",
        customer_name="Morgan Patel",
    )

    enqueue_order(order_queue, first_order)

    with pytest.raises(
        DuplicateOrderError,
        match="Order 'ORD-1001' already exists in the queue.",
    ):
        enqueue_order(order_queue, duplicate_order)

    assert list(order_queue) == [first_order]


def test_dequeue_order_returns_oldest_order() -> None:
    order_queue = create_order_queue()
    first_order = make_order(order_id="ORD-1001")
    second_order = make_order(
        order_id="ORD-1002",
        customer_name="Morgan Patel",
    )

    enqueue_order(order_queue, first_order)
    enqueue_order(order_queue, second_order)

    result = dequeue_order(order_queue)

    assert result is first_order
    assert list(order_queue) == [second_order]


def test_dequeue_order_raises_error_when_queue_is_empty() -> None:
    order_queue = create_order_queue()

    with pytest.raises(
        EmptyOrderError,
        match="The order queue is empty.",
    ):
        dequeue_order(order_queue)


def test_peek_next_order_returns_oldest_order_without_removing_it() -> None:
    order_queue = create_order_queue()
    first_order = make_order(order_id="ORD-1001")
    second_order = make_order(
        order_id="ORD-1002",
        customer_name="Morgan Patel",
    )

    enqueue_order(order_queue, first_order)
    enqueue_order(order_queue, second_order)

    result = peek_next_order(order_queue)

    assert result is first_order
    assert list(order_queue) == [
        first_order,
        second_order,
    ]


def test_peek_next_order_raises_error_when_queue_is_empty() -> None:
    order_queue = create_order_queue()

    with pytest.raises(
        EmptyOrderError,
        match="The order queue is empty.",
    ):
        peek_next_order(order_queue)


def test_process_order_fulfills_order_and_updates_inventory() -> None:
    item = make_inventory_item(quantity=10)
    inventory = generate_inventory_index([item])
    order_queue = create_order_queue()
    order = make_order(quantity=3)

    enqueue_order(order_queue, order)

    completed_order = process_order(
        order_queue,
        inventory,
    )

    assert completed_order is order
    assert completed_order.status == OrderStatus.COMPLETED
    assert item.quantity == 7
    assert len(order_queue) == 0


def test_process_order_preserves_state_when_inventory_is_insufficient() -> None:
    item = make_inventory_item(quantity=2)
    inventory = generate_inventory_index([item])
    order_queue = create_order_queue()
    order = make_order(quantity=3)

    enqueue_order(order_queue, order)

    with pytest.raises(InsufficientInventoryError):
        process_order(
            order_queue,
            inventory,
        )

    assert item.quantity == 2
    assert order.status == OrderStatus.PENDING
    assert list(order_queue) == [order]


def test_process_order_preserves_state_when_inventory_item_is_missing() -> None:
    item = make_inventory_item(
        sku="SKU-1001",
        quantity=10,
    )
    inventory = generate_inventory_index([item])
    order_queue = create_order_queue()
    order = make_order(
        sku="SKU-9999",
        quantity=1,
    )

    enqueue_order(order_queue, order)

    with pytest.raises(
        InventoryNotFoundError,
        match="Inventory item with SKU 'SKU-9999' was not found.",
    ):
        process_order(
            order_queue,
            inventory,
        )

    assert item.quantity == 10
    assert order.status == OrderStatus.PENDING
    assert list(order_queue) == [order]


