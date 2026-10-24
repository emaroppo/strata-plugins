"""Extracting frames, and declaring which video they came from.

Each frame records its video in the index and is written under one directory
per video; every frame is decoded, never sought. See ``docs/adr/0003``,
``docs/adr/0010``, ``docs/adr/0023`` and ``docs/adr/0033``.
"""

from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from strata.prepare import Prepared, Preparer, PreparerError
from strata.prepare.files import checksum_of

#: Container formats to admit, not codecs. docs/adr/0010
CONTAINERS = frozenset({"mp4", "mov", "mkv", "avi", "webm", "m4v"})

#: Enough of the video's checksum to name its directory uniquely behind a readable stem.
DIGEST_CHARS = 12


class VideoFramesPreparer(Preparer):
    """One video into one directory of frames."""

    name: ClassVar[str] = "video-frames"
    produces: ClassVar[str] = "frames"
    sources: ClassVar[frozenset[str]] = CONTAINERS

    def __init__(self, every: int = 30, max_frames: int | None = None, quality: int = 95):
        """Every ``every``th frame, at most ``max_frames`` of them.

        The defaults are declared, not inferred from the footage: one in
        thirty is about one a second, where consecutive frames stop matching.
        """
        if every < 1:
            raise PreparerError(f"every must be at least 1, got {every}")
        self.every = every
        self.max_frames = max_frames
        self.quality = quality

    def prepare(self, source: Path, out_dir: Path, *, root: Path) -> Iterable[Prepared]:
        # Lazy: for_source() resolves every registered preparer to pick one, so a
        # module-level import would load OpenCV whenever any file is prepared.
        import cv2

        source = Path(source)
        video = str(source)
        capture = cv2.VideoCapture(video)
        if not capture.isOpened():
            raise PreparerError(
                f"OpenCV could not open {source.name}. What it can decode "
                f"depends on how it was built, so this is a fact about the "
                f"install rather than about the file."
            )

        # The video's checksum, so a renamed source keeps its frames' names. docs/adr/0033
        group = f"{source.stem[-60:]}-{checksum_of(source)[:DIGEST_CHARS]}"
        directory = Path(out_dir) / group
        directory.mkdir(parents=True, exist_ok=True)
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0

        index = kept = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if index % self.every == 0:
                    path = directory / f"{index:06d}.jpg"
                    if not cv2.imwrite(
                        str(path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
                    ):
                        raise PreparerError(f"Could not write {path}")
                    yield Prepared(
                        path=path,
                        metadata={
                            "source_file": source.name,
                            "frame_index": index,
                            # Null rather than a wrong number. docs/adr/0038
                            "seconds": round(index / fps, 3) if fps > 0 else None,
                            # Which video: what a project names as group_by. docs/adr/0023
                            "video": group,
                        },
                    )
                    kept += 1
                    if self.max_frames is not None and kept >= self.max_frames:
                        break
                index += 1
        finally:
            capture.release()

        if kept == 0:
            raise PreparerError(
                f"{source.name} yielded no frames. It opened, so this is an "
                f"empty or unreadable stream rather than a missing decoder."
            )
