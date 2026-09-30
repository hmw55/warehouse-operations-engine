"""
Custom exceptions for the Warehouse Operations Engine.

This module defines the exception hierarchy used throughout the warehouse
operations system. The shared hierarchy allows callers to handle either
specific failures or broader categories of warehouse-related errors.
"""


class WarehouseError(Exception):
    """Base exception for all warehouse operations errors."""


class InventoryError(WarehouseError):
    """Base exception for inventory-related errors."""


# -------------------------------------------------------
# Inventory Exceptions
# -------------------------------------------------------

class InvalidInventoryItemError(InventoryError):
    """Raised when an inventory item contains invalid data."""


class DuplicateInventoryItemError(InventoryError):
    """Raised when attempting to add an inventory item whose SKU already exists."""


class InventoryNotFoundError(InventoryError):
    """Raised when a requested inventory item cannot be found."""


class InsufficientInventoryError(InventoryError):
    """Raised when inventory is insufficient to fulfill a request."""


# -------------------------------------------------------
# Order Exceptions
# -------------------------------------------------------

class OrderError(WarehouseError):
    """Base exception for order-related errors."""


class InvalidOrderError(OrderError):
    """Raised when an order contains invalid data."""


class EmptyOrderError(OrderError):
    """Raised when an order does not contain any order lines."""


class DuplicateOrderError(OrderError):
    """Raised when attempting to enqueue an order whose ID already exists."""


class OrderNotFoundError(OrderError):
    """Raised when a requested order cannot be found."""


# -------------------------------------------------------
# Routing Exceptions
# -------------------------------------------------------

class RoutingError(WarehouseError):
    """Base exception for warehouse routing errors."""


class RouteNotFoundError(RoutingError):
    """Raised when no valid route exists between warehouse locations."""


class DuplicateWarehouseLocationError(RoutingError):
    """Raised when a warehouse location already exists."""


# -------------------------------------------------------
# Analytics Exceptions
# -------------------------------------------------------

class AnalyticsError(WarehouseError):
    """Base exception for warehouse analytics errors."""


class InvalidLocationCapacityError(AnalyticsError):
    """Raised when warehouse location capacity data is invalid."""