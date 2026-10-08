class OrderNotFoundException(Exception):
    def __init__(self, message="Order not found"):
        super().__init__(message)


from exceptions.common_exceptions import AdminPermissionRequired
