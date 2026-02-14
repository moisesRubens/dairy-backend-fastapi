class DomainException(Exception):
    pass

class ExistingProductException(DomainException):
    def __init__(self, message="Product already registered"):
        super().__init__(message)

class ProductNotFound(DomainException):
    def __init__(self, message="Product not found"):
        super().__init__(message)