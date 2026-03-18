class OrderNotFound(Exception):
    def __init__(self, message="Order not found"):
        super().__init__(message)