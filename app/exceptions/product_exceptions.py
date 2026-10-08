class ExistingProductException(Exception):
    def __init__(self, message="Product already registered"):
        super().__init__(message)

class ProductNotFound(Exception):
    def __init__(self, message="Product not found"):
        super().__init__(message)
        
class InsuficientProductsAmountException(Exception):
    def __init__(self, message="Insufficient products amount"):
        self.message = message
        super().__init__(message)

class BusinessConflict(Exception):
    pass
