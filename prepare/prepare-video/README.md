# strata-prepare-video

Video into frames a catalog can take, each recording which video it came
from, so a project can keep a video on one side of a split. A plugin to
`strata-prepare`, found through its entry points, carrying OpenCV.

Not on PyPI: it installs from its repository at a release tag. uv takes a
git source only for a package named directly, so the strata packages
beneath it are named beside it.

```bash
g=git+https://github.com/emaroppo
uv add "strata-prepare-video @ $g/strata-plugins@v0.1.0#subdirectory=prepare/prepare-video" \
       "strata-prepare @ $g/strata-prepare@v0.1.0"                                          \
       "strata-contracts @ $g/strata-contracts@v0.1.0"                                      \
       "strata-common @ $g/strata-common@v0.1.0"
```

## What it adds

| entry point | name | what it does |
|---|---|---|
| `strata.preparers` | `video-frames` | `.mp4`, `.mov`, `.mkv` and the rest into `frames` |

Frames are written one directory per video, sampled every `every` frames
up to `max_frames`, as JPEG at `quality`. The prepared index records each
frame's video under the metadata key `video`, which the `frames` type
requires; a project that freezes its versions with `group_by = "video"`
keeps consecutive near-duplicate frames on one side of a split. The
directory layout says the same thing for tools that read only that.

Every frame is decoded in order and most are thrown away, rather than
seeking by frame number: a seek lands on the nearest keyframe, which
depends on the codec, and decoding in order is the only way the same
frames come out on a second run. Determinism is what keeps a re-prepared
corpus from re-checksumming into new samples.

## Decisions

`docs/adr/NNNN`, wherever this code says it, is a record in the strata
umbrella repository: https://github.com/emaroppo/strata/tree/main/docs/adr.

## Tests

```bash
cd prepare/prepare-video      # in the strata-plugins repository
uv sync --find-links ../../dist --group dev --extra test   # after .github/sibling-wheels.sh contracts common prepare
uv run pytest
```

Inside the strata workspace: `uv run pytest packages/plugins` from its root.

Includes `PreparerContract` from `strata.prepare.conformance`.
