"""Warehouse routing operations backed by a weighted graph.

This module models physical warehouse locations and the walkable
connections between them. Locations may represent storage bins or
operational areas such as receiving, packing, and shipping.

The graph is intentionally separate from inventory storage assignments.
A single SKU may exist in multiple bins, while this module only describes
how warehouse workers can travel between physical locations.
"""

import networkx as nx

from warehouse_operations_engine.exceptions import (
    DuplicateWarehouseLocationError,
    RouteNotFoundError,
)
from warehouse_operations_engine.models import PickRoute


WarehouseGraph = nx.Graph
"""NetworkX graph representing warehouse locations and weighted paths."""


def _validate_existing_locations(
    warehouse_graph: WarehouseGraph,
    *location_ids: str,
) -> None: 
    """Validate that each warehouse location exists in the graph.
    
    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        *location_ids: Warehouse location identifiers to validate.

    Raises:
        RouteNotFoundError: If one or more warehouse locations do not exist.
    """
    missing_locations = [
        location_id
        for location_id in location_ids
        if location_id not in warehouse_graph
    ]

    if missing_locations:
        missing_location_list = ", ".join(missing_locations)
        raise RouteNotFoundError(
            f"Warehouse location does not exist: {missing_location_list}."
        )

def create_warehouse_graph() -> WarehouseGraph:
    """Create an empty warehouse routing graph.
    
    Returns:
        An empty undirected graph for warehouse locations and connections.
    """
    return nx.Graph()


def add_location(
    warehouse_graph: WarehouseGraph,
    location_id: str,
) -> None:
    """Add a physical warehouse location to the routing graph.
    
    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        location_id: Unique identifier for the warehouse location.

    Raises:
        ValueError: If the location identifier is blank.
        DuplicateWarehouseLocationError: If the location already exists.

    Design Note:
    Location identifiers may represent dynamically assigned storage
    bins, such as ``A-01-01``, or operational locations, such as
    ``RECEIVING``, ``PACKING``, and ``SHIPPING``. Products are not 
    permanently assigned to one aisle because the inventory system 
    may  store the same SKU in multiple available bins.
    """
    normalized_location_id = location_id.strip()

    if not normalized_location_id:
        raise ValueError("Warehouse location ID cannot be blank.")

    if normalized_location_id in warehouse_graph:
        raise DuplicateWarehouseLocationError(
            f"Warehouse location '{normalized_location_id}' already exists."
        )
    warehouse_graph.add_node(normalized_location_id)


def connect_locations(
    warehouse_graph: WarehouseGraph,
    first_location_id: str,
    second_location_id: str,
    distance: float,
) -> None:
    """Connect two warehouse locations with a weighted walking path.

    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        first_location_id: Identifier for the first warehouse location.
        second_location_id: Identifier for the second warehouse location.
        distance: Walking distance between the two locations.

    Raises:
        ValueError: If either location identifier is blank.
        ValueError: If the two location identifiers are the same.
        ValueError: If the distance is not greater than zero.
        RouteNotFoundError: If either warehouse location does not exist.

    Design Note:
        Connections use NetworkX's ``weight`` edge attribute so shortest-path
        calculations can minimize actual walking distance rather than merely
        counting how many locations a worker passes through.

        Reconnecting two existing locations updates the stored distance. This
        allows corrected warehouse measurements without creating duplicate
        paths in the undirected graph.
    """
    normalized_first_location_id = first_location_id.strip()
    normalized_second_location_id = second_location_id.strip()

    if not normalized_first_location_id or not normalized_second_location_id:
        raise ValueError("Warehouse location IDs cannot be blank.")

    if normalized_first_location_id == normalized_second_location_id:
        raise ValueError("A warehouse location cannot connect to itself.")

    if distance <= 0:
        raise ValueError("Connection distance must be greater than zero.")

    _validate_existing_locations(
        warehouse_graph,
        normalized_first_location_id,
        normalized_second_location_id,
    )

    warehouse_graph.add_edge(
        normalized_first_location_id,
        normalized_second_location_id,
        weight=distance,
    )


def remove_connection(
    warehouse_graph: WarehouseGraph,
    first_location_id: str,
    second_location_id: str,
) -> None:
    """Remove an existing path between two warehouse locations.
    
    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        first_location_id: Identifier for the first warehouse location.
        second_location_id: Identifier for the second warehouse location.

    Raises:
        ValueError: If either location identifier is blank.
        ValueError: If both identifiers refer to the same location.
        RouteNotFoundError: If either warehouse location does not exist.
        RouteNotFoundError: If no connection exists between the location.

    Design Note:
        Removing a missing connection raises an explicit error rather than
        silently succeeding. This makes configuration mistakes visible and
        keeps graph mutations consistent with the package's other operations.
    """
    normalized_first_location_id = first_location_id.strip()
    normalized_second_location_id = second_location_id.strip()

    if not normalized_first_location_id or not normalized_second_location_id:
        raise ValueError("Warehouse location IDs cannot be blank.")

    if normalized_first_location_id == normalized_second_location_id:
        raise ValueError(
            "A warehouse location cannot disconnect from itself."
        )
    
    _validate_existing_locations(
        warehouse_graph,
        normalized_first_location_id,
        normalized_second_location_id,
    )

    if not warehouse_graph.has_edge(
        normalized_first_location_id,
        normalized_second_location_id,
    ):
        raise RouteNotFoundError(
            "No connection exists between "
            f"'{normalized_first_location_id}' and "
            f"'{normalized_second_location_id}'."
        )
    
    warehouse_graph.remove_edge(
        normalized_first_location_id,
        normalized_second_location_id,
    )


def find_shortest_pick_path(
    warehouse_graph: WarehouseGraph,
    start_location_id: str,
    end_location_id: str,
) -> PickRoute:
    """Find the shortest weighted path between two warehouse locations.
    
    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        start_location_id: Identifier for the route's starting location.
        end_location_id: Identifier for the route's destination.

    Returns: 
        A pick route containing the ordered locations and total distance.

    Raises:
        ValueError: If either location identifier is blank.
        RouteNotFoundError: If either location does not exist.
        RouteNotFoundError: If no connected route exists between them.

    Design Note:
        Routing uses weighted shortest-path calculations so the selected
        route minimizes total walking distance rather than simply choosing
        the route with the fewest intermediate locations.
    """
    normalized_start_location_id = start_location_id.strip()
    normalized_end_location_id = end_location_id.strip()

    if not normalized_start_location_id or not normalized_end_location_id:
        raise ValueError("Warehouse location IDs cannot be blank.")

    _validate_existing_locations(
        warehouse_graph,
        normalized_start_location_id,
        normalized_end_location_id,
    )
    
    try:
        locations = nx.shortest_path(
            warehouse_graph,
            source=normalized_start_location_id,
            target=normalized_end_location_id,
            weight="weight",
        )
        total_distance = nx.shortest_path_length(
            warehouse_graph,
            source=normalized_start_location_id,
            target=normalized_end_location_id,
            weight="weight",
        )
    except nx.NetworkXNoPath as error:
        raise RouteNotFoundError(
            "No route exists between "
            f"'{normalized_start_location_id}' and "
            f"'{normalized_end_location_id}'."
        ) from error
    
    return PickRoute(
        locations=locations,
        total_distance=float(total_distance),
    )


def remove_location(
    warehouse_graph: WarehouseGraph,
    location_id: str,
) -> None:
    """Remove a warehouse location from the routing graph.
    
    Args:
        warehouse_graph: Graph containing warehouse locations and paths.
        location_id: Identifier for the warehouse location.

    Raises:
        ValueError: If the location identifier is blank.
        RouteNotFoundError: If the warehouse location does not exist.

    Design Note:
        Removing a warehouse location also removes every connected walking 
        path. This mirrors physical warehouse changes where removing an 
        aisle, bin, or operational area necessarily eliminates the routes
        leading to it.
    """
    normalized_location_id = location_id.strip()

    if not normalized_location_id:
        raise ValueError(
            "Warehouse location ID cannot be blank."
        )
    
    _validate_existing_locations(
        warehouse_graph,
        normalized_location_id,
    )

    warehouse_graph.remove_node(normalized_location_id)