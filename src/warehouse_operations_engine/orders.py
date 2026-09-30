"""
Order queue operations for the Warehouse Operations Engine.

This module manages customer orders awaiting warehouse fulfillment.
Orders are stored in a double-ended queue so they can be added at one end
and processed efficiently from the other in first-in, first-out order.
"""

from collections import deque

from warehouse_operations_engine.exceptions import (
    DuplicateOrderError,
    EmptyOrderError,
    InsufficientInventoryError,
)
from warehouse_operations_engine.inventory import get_inventory_item
from warehouse_operations_engine.models import (
    InventoryIndex,
    Order,
    OrderQueue,
    OrderStatus,
)


def create_order_queue() -> OrderQueue:
    """
    Create an empty first-in, first-out order queue.

    Returns:
        An empty queue for customer orders awaiting fulfillment.
    """

    return deque()


def enqueue_order(
        order_queue: OrderQueue,
        order: Order,
) -> None:
    """
    Add a customer order to the end of the fulfillment queue.

    Args:
        order_queue: Queue of orders awaiting fulfillment.
        order: Customer order to add.
    
    Raises:
        DuplicateOrderError:
            If an order with the same order ID already exists in the queue.
    """

    if any(
        queued_order.order_id == order.order_id
        for queued_order in order_queue
    ):
        raise DuplicateOrderError(
            f"Order '{order.order_id}' already exists in the queue."
        )

    order_queue.append(order)


def dequeue_order(
    order_queue: OrderQueue,
) -> Order:
    """
    Remove and return the next customer order awaiting fulfillment.

    Orders are processed in first-in, first-out (FIFO) order to ensure
    customers are served in the order their requests were received.

    Args:
        order_queue: Queue of orders awaiting fulfillment.

    Returns:
        The next customer order in the queue.

    Raises:
        EmptyOrderError:
            If the order queue is empty.
    """

    try:
        return order_queue.popleft()
    except IndexError as error:
        raise EmptyOrderError(
            "The order queue is empty."
        ) from error
    

def peek_next_order(
    order_queue: OrderQueue,
) -> Order:
    """
    Return the next customer order without removing it from the queue.

    Args:
        order_queue: Queue of orders awaiting fulfillment.

    Returns:
        The next customer order awaiting fulfillment.

    Raises:
        EmptyOrderError:
            If the order queue is empty.
    """

    try:
        return order_queue[0]
    except IndexError as error:
        raise EmptyOrderError(
            "The order queue is empty."
        ) from error
    

def process_order(
    order_queue: OrderQueue,
    inventory: InventoryIndex,
) -> Order: 
    """
    Fulfill the next customer order using available warehouse inventory.

    The order at the front of the queue is validated before any inventory
    quantities are changed. Successful fulfillment removes the order from
    the queue, deducts each requested quantity, and marks the order as
    completed.

    Args:
        order_queue: Queue of orders awaiting fulfillment.
        inventory: Inventory records indexed by SKU.

    Returns:
        The successfully completed customer order.

    Raises:
        EmptyOrderError:
            If the order queue is empty.
        InventoryNotFoundError:
            If an order line references an unknown SKU.
        InsufficientInventoryError:
            If available inventory cannot fulfill the entire order.
    """

    #-----------------------------------------------------------------
    # Design Note
    # 
    # Order fulfillment is treated as an atomic business operation.
    # 
    # Every order line is validated before any inventory quantity is
    # modified. If a requested item does not exist or lacks sufficient
    # stock, the entire operation fails and the order remains at the front
    # of the queue.
    # 
    # This prevents partial inventory updates and avoids the need for
    # rollback logic. Production warehouse systems may support backorders,
    # partial shipments, and database transactions. This implementation
    # intentionally focuses on demonstrating how queues, dictionaries, and 
    # lists work together to support a consistent fulfillment workflow.
    #------------------------------------------------------------------

    order = peek_next_order(order_queue)

    for order_line in order.lines:
        inventory_item = get_inventory_item(
            inventory,
            order_line.sku,
        )

        if inventory_item.quantity < order_line.quantity:
            raise InsufficientInventoryError(
                f"Insufficient inventory for SKU '{order_line.sku}'. "
                f"Requested: {order_line.quantity}; "
                f"available: {inventory_item.quantity}."
            )

    for order_line in order.lines:
        inventory_item = get_inventory_item(
            inventory,
            order_line.sku,
        )

        inventory_item.quantity -= order_line.quantity

    order.status = OrderStatus.COMPLETED

    dequeue_order(order_queue)

    return order
    