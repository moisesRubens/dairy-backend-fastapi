class ExistingProductException(Exception):
    def __init__(self, message="Product already registered"):
        super().__init__(message)

class ProductNotFound(Exception):
    def __init__(self, message="Product not found"):
        super().__init__(message)
        
class InsuficientProductsAmountException(Exception):
    message = "Insufucient products amount"
    def __inti__(self, message=message):
        super().__init__(message)
