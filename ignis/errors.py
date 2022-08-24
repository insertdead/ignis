class InternalServerError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidScopeError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidAuthError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class NotFoundError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ApiConflictError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MiscApiError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
