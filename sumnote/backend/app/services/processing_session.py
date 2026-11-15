class ProcessingSession:
    """Request-scoped upload buffer that is cleared when processing ends."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def size(self) -> int:
        return len(self._buffer)

    def append(self, chunk: bytes) -> None:
        self._buffer.extend(chunk)

    def content(self) -> bytes:
        return bytes(self._buffer)

    def clear(self) -> None:
        self._buffer[:] = b"\0" * len(self._buffer)
        self._buffer.clear()

    def __enter__(self) -> "ProcessingSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.clear()
