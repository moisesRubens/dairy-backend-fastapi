class OutboundNotFound(Exception):
    def __init__(self, message="Outbound not found"):
        super().__init__(message)
