from typing import BinaryIO, Callable, Dict, Optional, Tuple, Union

class MultipartEncoder:
    len: int
    def __init__(self, fields: Dict[str, Tuple[str, Union[BinaryIO, bytes], str]]): ...

class MultipartEncoderMonitor:
    bytes_read: int
    content_type: str
    def __init__(
        self,
        encoder: MultipartEncoder,
        callback: Optional[Callable[[MultipartEncoderMonitor], None]],
    ): ...
