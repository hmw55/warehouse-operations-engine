from warehouse_operations_engine.models import OrderStatus
from warehouse_operations_engine.seed import (
    seed_demo_warehouse,
    seed_inventory,
    seed_location_capacities,
    seed_order_queue,
    seed_warehouse_graph,
)


def test_seed_inventory_creates_representative_inventory() -> None:
    inventory = seed_inventory()

    assert len(inventory) == 12
    assert len({item.location for item in inventory.values()}) > 1
    assert any(
        item.quantity <= item.reorder_level
        for item in inventory.values()
    )
    assert any(
        item.quantity == 0
        for item in inventory.values()
    )


def test_seed_inventory_returns_independent_state() -> None:
    first_inventory = seed_inventory()
    second_inventory = seed_inventory()

    first_inventory["CLEAN-1001"].quantity = 0

    assert second_inventory["CLEAN-1001"].quantity == 48


def test_seed_order_queue_creates_pending_orders() -> None:
    order_queue = seed_order_queue()

    assert len(order_queue) == 3
    assert all(
        order.status == OrderStatus.PENDING
        for order in order_queue
    )


def test_seed_order_queue_returns_independent_state() -> None:
    first_queue = seed_order_queue()
    second_queue = seed_order_queue()

    first_queue.popleft()

    assert len(first_queue) == 2
    assert len(second_queue) == 3


def test_seed_warehouse_graph_creates_connected_layout() -> None:
    warehouse_graph = seed_warehouse_graph()

    assert warehouse_graph.number_of_nodes() == 15
    assert warehouse_graph.number_of_edges() == 20
    assert "RECEIVING" in warehouse_graph
    assert "PACKING" in warehouse_graph
    assert "SHIPPING" in warehouse_graph


def test_seed_location_capacities_configures_storage_locations() -> None:
    capacities = seed_location_capacities()

    assert len(capacities) == 12
    assert all(
        capacity > 0
        for capacity in capacities.values()
    )


def test_seed_demo_warehouse_combines_demo_components() -> None:
    warehouse = seed_demo_warehouse()

    assert len(warehouse.inventory) == 12
    assert len(warehouse.order_queue) == 3
    assert warehouse.warehouse_graph.number_of_nodes() == 15
    assert warehouse.warehouse_graph.number_of_edges() == 20
    assert len(warehouse.location_capacities) == 12


def test_seed_demo_warehouse_returns_independent_state() -> None:
    first_warehouse = seed_demo_warehouse()
    second_warehouse = seed_demo_warehouse()

    first_warehouse.inventory["CLEAN-1001"].quantity = 0
    first_warehouse.order_queue.popleft()
    first_warehouse.warehouse_graph.remove_node("RECEIVING")
    first_warehouse.location_capacities["A-01-01"] = 0

    assert second_warehouse.inventory["CLEAN-1001"].quantity == 48
    assert len(second_warehouse.order_queue) == 3
    assert "RECEIVING" in second_warehouse.warehouse_graph
    assert second_warehouse.location_capacities["A-01-01"] > 0