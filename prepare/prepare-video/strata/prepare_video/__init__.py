"""Video into frames: one directory per video, each frame declaring which
video it came from. See ``docs/adr/0010`` and ``docs/adr/0023``.
"""

from .frames import VideoFramesPreparer

__all__ = ["VideoFramesPreparer"]
