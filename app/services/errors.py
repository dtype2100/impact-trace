class NotReadyError(Exception): pass
class UpstreamError(Exception):
    def __init__(self, message="upstream service unavailable", status=502): self.status, self.message = status, message; super().__init__(message)
class NotFoundError(Exception): pass
class ConflictError(Exception): pass
