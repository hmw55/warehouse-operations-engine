import networkx as nx
import pytest

from warehouse_operations_engine.exceptions import (
    DuplicateWarehouseLocationError,
    RouteNotFoundError,
)
from warehouse_operations_engine.routing import (
    add_location,
    connect_locations,
    create_warehouse_graph,
    find_shortest_pick_path,
    remove_connection,
    remove_location,
)


def create_graph_with_locations(
    *location_ids: str,
) -> nx.Graph:
    """Create a warehouse graph containing the requested locations."""
    warehouse_graph = create_warehouse_graph()

    for location_id in location_ids:
        add_location(warehouse_graph, location_id)

    return warehouse_graph


def test_create_warehouse_graph_returns_empty_graph() -> None:
    warehouse_graph = create_warehouse_graph()

    assert isinstance(warehouse_graph, nx.Graph)
    assert warehouse_graph.number_of_nodes() == 0
    assert warehouse_graph.number_of_edges() == 0


@pytest.mark.parametrize(
    "location_id",
    [
        "A-01-01",
        "PACKING",
    ],
)
def test_add_location_adds_location_to_graph(location_id: str) -> None:
    warehouse_graph = create_warehouse_graph()

    add_location(warehouse_graph, location_id)

    assert location_id in warehouse_graph
    assert warehouse_graph.number_of_nodes() == 1


def test_add_location_strips_surrounding_whitespace() -> None:
    warehouse_graph = create_warehouse_graph()

    add_location(warehouse_graph, "  C-03-02  ")

    assert "C-03-02" in warehouse_graph
    assert "  C-03-02  " not in warehouse_graph


def test_add_location_rejects_blank_location_id() -> None:
    warehouse_graph = create_warehouse_graph()

    with pytest.raises(
        ValueError,
        match="Warehouse location ID cannot be blank.",
    ):
        add_location(warehouse_graph, "   ")


def test_add_location_rejects_duplicate_location_id() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    with pytest.raises(
        DuplicateWarehouseLocationError,
        match="Warehouse location 'A-01-01' already exists.",
    ):
        add_location(warehouse_graph, "A-01-01")

    assert list(warehouse_graph.nodes) == ["A-01-01"]


def test_connect_locations_adds_weighted_connection() -> None:
    warehouse_graph = create_graph_with_locations(
        "RECEIVING",
        "A-01-01",
    )

    connect_locations(
        warehouse_graph,
        "RECEIVING",
        "A-01-01",
        25.0,
    )

    assert warehouse_graph.has_edge("RECEIVING", "A-01-01")
    assert warehouse_graph["RECEIVING"]["A-01-01"]["weight"] == 25.0


def test_connect_locations_strips_surrounding_whitespace() -> None:
    warehouse_graph = create_graph_with_locations(
        "A-01-01",
        "A-01-02",
    )

    connect_locations(
        warehouse_graph,
        "  A-01-01  ",
        "  A-01-02  ",
        8.0,
    )

    assert warehouse_graph.has_edge("A-01-01", "A-01-02")


def test_connect_locations_updates_existing_connection_distance() -> None:
    warehouse_graph = create_graph_with_locations(
        "A-01-01",
        "A-01-02",
    )
    connect_locations(
        warehouse_graph,
        "A-01-01",
        "A-01-02",
        8.0,
    )

    connect_locations(
        warehouse_graph,
        "A-01-01",
        "A-01-02",
        6.5,
    )

    assert warehouse_graph.number_of_edges() == 1
    assert warehouse_graph["A-01-01"]["A-01-02"]["weight"] == 6.5


def test_connect_locations_rejects_blank_location_id() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    with pytest.raises(
        ValueError,
        match="Warehouse location IDs cannot be blank.",
    ):
        connect_locations(
            warehouse_graph,
            "A-01-01",
            "   ",
            5.0,
        )


def test_connect_locations_rejects_self_connection() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    with pytest.raises(
        ValueError,
        match="A warehouse location cannot connect to itself.",
    ):
        connect_locations(
            warehouse_graph,
            "A-01-01",
            "A-01-01",
            5.0,
        )


@pytest.mark.parametrize("distance", [0, -1, -10.5])
def test_connect_locations_rejects_nonpositive_distance(
    distance: float,
) -> None:
    warehouse_graph = create_graph_with_locations(
        "A-01-01",
        "A-01-02",
    )

    with pytest.raises(
        ValueError,
        match="Connection distance must be greater than zero.",
    ):
        connect_locations(
            warehouse_graph,
            "A-01-01",
            "A-01-02",
            distance,
        )


def test_connect_locations_raises_error_for_unknown_location() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    with pytest.raises(
        RouteNotFoundError,
        match="Warehouse location does not exist: C-03-02.",
    ):
        connect_locations(
            warehouse_graph,
            "A-01-01",
            "C-03-02",
            20.0,
        )


def test_find_shortest_pick_path_returns_weighted_shortest_route() -> None:
    warehouse_graph = create_graph_with_locations(
        "RECEIVING",
        "A-01-01",
        "B-01-01",
        "C-01-01",
        "PACKING",
    )

    connect_locations(warehouse_graph, "RECEIVING", "A-01-01", 10.0)
    connect_locations(warehouse_graph, "A-01-01", "PACKING", 30.0)
    connect_locations(warehouse_graph, "RECEIVING", "B-01-01", 8.0)
    connect_locations(warehouse_graph, "B-01-01", "C-01-01", 7.0)
    connect_locations(warehouse_graph, "C-01-01", "PACKING", 9.0)

    route = find_shortest_pick_path(
        warehouse_graph,
        "RECEIVING",
        "PACKING",
    )

    assert route.locations == [
        "RECEIVING",
        "B-01-01",
        "C-01-01",
        "PACKING",
    ]
    assert route.total_distance == 24.0


def test_find_shortest_pick_path_optimizes_distance_not_hop_count() -> None:
    warehouse_graph = create_graph_with_locations(
        "RECEIVING",
        "A-01-01",
        "B-01-01",
        "C-01-01",
        "SHIPPING",
    )

    connect_locations(warehouse_graph, "RECEIVING", "SHIPPING", 50.0)
    connect_locations(warehouse_graph, "RECEIVING", "A-01-01", 10.0)
    connect_locations(warehouse_graph, "A-01-01", "B-01-01", 10.0)
    connect_locations(warehouse_graph, "B-01-01", "C-01-01", 10.0)
    connect_locations(warehouse_graph, "C-01-01", "SHIPPING", 10.0)

    route = find_shortest_pick_path(
        warehouse_graph,
        "RECEIVING",
        "SHIPPING",
    )

    assert route.locations == [
        "RECEIVING",
        "A-01-01",
        "B-01-01",
        "C-01-01",
        "SHIPPING",
    ]
    assert route.total_distance == 40.0


def test_find_shortest_pick_path_strips_surrounding_whitespace() -> None:
    warehouse_graph = create_graph_with_locations(
        "PACKING",
        "SHIPPING",
    )
    connect_locations(
        warehouse_graph,
        "PACKING",
        "SHIPPING",
        12.0,
    )

    route = find_shortest_pick_path(
        warehouse_graph,
        "  PACKING  ",
        "  SHIPPING  ",
    )

    assert route.locations == ["PACKING", "SHIPPING"]
    assert route.total_distance == 12.0


def test_find_shortest_pick_path_returns_zero_for_same_location() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    route = find_shortest_pick_path(
        warehouse_graph,
        "A-01-01",
        "A-01-01",
    )

    assert route.locations == ["A-01-01"]
    assert route.total_distance == 0.0


def test_find_shortest_pick_path_rejects_blank_location_id() -> None:
    warehouse_graph = create_warehouse_graph()

    with pytest.raises(
        ValueError,
        match="Warehouse location IDs cannot be blank.",
    ):
        find_shortest_pick_path(
            warehouse_graph,
            "   ",
            "SHIPPING",
        )


def test_find_shortest_pick_path_raises_error_for_unknown_location() -> None:
    warehouse_graph = create_graph_with_locations("RECEIVING")

    with pytest.raises(
        RouteNotFoundError,
        match="Warehouse location does not exist: SHIPPING.",
    ):
        find_shortest_pick_path(
            warehouse_graph,
            "RECEIVING",
            "SHIPPING",
        )


def test_find_shortest_pick_path_raises_error_when_no_route_exists() -> None:
    warehouse_graph = create_graph_with_locations(
        "RECEIVING",
        "SHIPPING",
    )

    with pytest.raises(
        RouteNotFoundError,
        match="No route exists between 'RECEIVING' and 'SHIPPING'.",
    ):
        find_shortest_pick_path(
            warehouse_graph,
            "RECEIVING",
            "SHIPPING",
        )


def test_remove_connection_removes_existing_connection() -> None:
    warehouse_graph = create_graph_with_locations(
        "A-01-01",
        "A-01-02",
    )
    connect_locations(
        warehouse_graph,
        "A-01-01",
        "A-01-02",
        8.0,
    )

    remove_connection(
        warehouse_graph,
        "A-01-01",
        "A-01-02",
    )

    assert not warehouse_graph.has_edge("A-01-01", "A-01-02")


def test_remove_connection_strips_surrounding_whitespace() -> None:
    warehouse_graph = create_graph_with_locations(
        "PACKING",
        "SHIPPING",
    )
    connect_locations(
        warehouse_graph,
        "PACKING",
        "SHIPPING",
        12.0,
    )

    remove_connection(
        warehouse_graph,
        "  PACKING  ",
        "  SHIPPING  ",
    )

    assert not warehouse_graph.has_edge("PACKING", "SHIPPING")


def test_remove_connection_rejects_blank_location_id() -> None:
    warehouse_graph = create_warehouse_graph()

    with pytest.raises(
        ValueError,
        match="Warehouse location IDs cannot be blank.",
    ):
        remove_connection(
            warehouse_graph,
            "",
            "SHIPPING",
        )


def test_remove_connection_rejects_self_disconnection() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    with pytest.raises(
        ValueError,
        match="A warehouse location cannot disconnect from itself.",
    ):
        remove_connection(
            warehouse_graph,
            "A-01-01",
            "A-01-01",
        )


def test_remove_connection_raises_error_for_unknown_location() -> None:
    warehouse_graph = create_graph_with_locations("PACKING")

    with pytest.raises(
        RouteNotFoundError,
        match="Warehouse location does not exist: SHIPPING.",
    ):
        remove_connection(
            warehouse_graph,
            "PACKING",
            "SHIPPING",
        )


def test_remove_connection_raises_error_when_connection_does_not_exist() -> None:
    warehouse_graph = create_graph_with_locations(
        "PACKING",
        "SHIPPING",
    )

    with pytest.raises(
        RouteNotFoundError,
        match="No connection exists between 'PACKING' and 'SHIPPING'.",
    ):
        remove_connection(
            warehouse_graph,
            "PACKING",
            "SHIPPING",
        )


def test_remove_location_removes_existing_location() -> None:
    warehouse_graph = create_graph_with_locations("A-01-01")

    remove_location(
        warehouse_graph,
        "A-01-01",
    )

    assert "A-01-01" not in warehouse_graph


def test_remove_location_removes_connected_paths() -> None:
    warehouse_graph = create_graph_with_locations(
        "RECEIVING",
        "A-01-01",
        "PACKING",
    )
    connect_locations(
        warehouse_graph,
        "RECEIVING",
        "A-01-01",
        10.0,
    )
    connect_locations(
        warehouse_graph,
        "A-01-01",
        "PACKING",
        15.0,
    )

    remove_location(
        warehouse_graph,
        "A-01-01",
    )

    assert "A-01-01" not in warehouse_graph
    assert not warehouse_graph.has_edge("RECEIVING", "A-01-01")
    assert not warehouse_graph.has_edge("A-01-01", "PACKING")


def test_remove_location_strips_surrounding_whitespace() -> None:
    warehouse_graph = create_graph_with_locations("PACKING")

    remove_location(
        warehouse_graph,
        "  PACKING  ",
    )

    assert "PACKING" not in warehouse_graph


def test_remove_location_rejects_blank_location_id() -> None:
    warehouse_graph = create_warehouse_graph()

    with pytest.raises(
        ValueError,
        match="Warehouse location ID cannot be blank.",
    ):
        remove_location(
            warehouse_graph,
            "   ",
        )


def test_remove_location_raises_error_for_unknown_location() -> None:
    warehouse_graph = create_warehouse_graph()

    with pytest.raises(
        RouteNotFoundError,
        match="Warehouse location does not exist: PACKING.",
    ):
        remove_location(
            warehouse_graph,
            "PACKING",
        )