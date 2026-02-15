class ExistingSalePointException(Exception):
    def __init__(self, message="Sale point already exists"):
        super().__init__(message)

class SalePointNotFound(Exception):
    def __init__(self, message="Sale point not found"):
        super().__init__(message)