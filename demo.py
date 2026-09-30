"""Interactive command-line demonstration of the Warehouse Operations Engine."""

from warehouse_operations_engine.analytics import (
    generate_inventory_report,
    get_low_stock_items,
    get_out_of_stock_items,
)
from warehouse_operations_engine.exceptions import (
    InventoryError,
    OrderError,
    RouteNotFoundError,
)
from warehouse_operations_engine.models import DemoWarehouse
from warehouse_operations_engine.orders import (
    peek_next_order,
    process_order,
)
from warehouse_operations_engine.routing import find_shortest_pick_path
from warehouse_operations_engine.seed import seed_demo_warehouse


def print_inventory_summary(
    warehouse: DemoWarehouse,
) -> None:
    """Display a high-level summary of warehouse inventory."""

    report = generate_inventory_report(warehouse.inventory)
    low_stock_items = get_low_stock_items(warehouse.inventory)
    out_of_stock_items = get_out_of_stock_items(warehouse.inventory)

    print("\nInventory Summary")
    print("-----------------")
    print(f"Unique SKUs: {report.total_items}")
    print(f"Total Quantity: {report.total_quantity}")
    print(f"Low Stock Items: {len(low_stock_items)}")
    print(f"Out of Stock Items: {len(out_of_stock_items)}")


def print_low_stock_items(
    warehouse: DemoWarehouse,
) -> None:
    """Display low-stock and out-of-stock inventory items."""

    low_stock_items = get_low_stock_items(warehouse.inventory)
    out_of_stock_items = get_out_of_stock_items(warehouse.inventory)

    print("\nLow Stock")
    print("---------")

    if not low_stock_items:
        print("No low-stock items.")
    else:
        for item in low_stock_items:
            print(
                f"{item.sku} - {item.name}: "
                f"{item.quantity} remaining"
            )

    print("\nOut of Stock")
    print("------------")

    if not out_of_stock_items:
        print("No out-of-stock items.")
    else:
        for item in out_of_stock_items:
            print(f"{item.sku} - {item.name}")


def process_next_demo_order(
    warehouse: DemoWarehouse,
) -> None:
    """Process the next order in the FIFO queue."""

    try:
        next_order = peek_next_order(warehouse.order_queue)

        print(
            f"\nProcessing {next_order.order_id} "
            f"for {next_order.customer_name}..."
        )

        completed_order = process_order(
            warehouse.order_queue,
            warehouse.inventory,
        )

        print(f"Completed {completed_order.order_id}.")
        print(f"Orders remaining: {len(warehouse.order_queue)}")

    except (OrderError, InventoryError) as error:
        print(f"\nUnable to process order: {error}")


def show_route(
    warehouse: DemoWarehouse,
) -> None:
    """Display the warehouse layout and calculate a shortest route."""

    print(
        "\nWarehouse Layout\n"
        "----------------\n"
        "\n"
        "                 RECEIVING\n"
        "                     |\n"
        "        A-01-01 -- A-01-02 -- A-01-03\n"
        "           |          |          |\n"
        "        B-01-01 -- B-01-02 -- B-01-03\n"
        "           |          |          |\n"
        "        C-01-01 -- C-01-02 -- C-01-03\n"
        "           |          |          |\n"
        "        D-01-01 -- D-01-02 -- D-01-03\n"
        "                      |\n"
        "                   PACKING\n"
        "                      |\n"
        "                   SHIPPING\n"
    )

    start_location = input("Start location: ").strip().upper()
    end_location = input("Destination: ").strip().upper()

    try:
        route = find_shortest_pick_path(
            warehouse.warehouse_graph,
            start_location,
            end_location,
        )

        print("\nShortest Route")
        print("--------------")
        print(" -> ".join(route.locations))
        print(f"Total distance: {route.total_distance}")

    except (RouteNotFoundError, ValueError) as error:
        print(f"\nUnable to calculate route: {error}")


def print_menu() -> None:
    """Display the demonstration menu."""

    print(
        "\nWarehouse Operations Engine\n"
        "---------------------------\n"
        "1. Inventory summary\n"
        "2. Low/out-of-stock items\n"
        "3. Process next order\n"
        "4. Find shortest route\n"
        "5. Exit"
    )


def main() -> None:
    """Run the interactive warehouse operations demonstration."""

    warehouse = seed_demo_warehouse()

    while True:
        print_menu()

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            print_inventory_summary(warehouse)

        elif choice == "2":
            print_low_stock_items(warehouse)

        elif choice == "3":
            process_next_demo_order(warehouse)

        elif choice == "4":
            show_route(warehouse)

        elif choice == "5":
            print("\nGoodbye.")
            break

        else:
            print("\nPlease choose an option from 1 through 5.")


if __name__ == "__main__":
    main()