# Contributing to LinePatch

Thanks for helping make copied text less painful. The project values small,
explainable rules over a large opaque formatter.

## Local setup

```console
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

Before opening a pull request, run the quality commands from the README. Keep
fixtures synthetic and do not include private or copyrighted documents.

## What makes a good change?

- It names the exact copy artifact or document shape it handles.
- It adds a failing test before changing the engine.
- It preserves the review boundary: no silent clipboard writes, network calls,
  model calls, source overwrites, or code execution.
- It updates the README or verification record when the user-visible behavior
  changes.

Please describe the before/after text, the platform tested, and why the rule is
safe. A pull request that makes the output more aggressive should include a
fixture showing what it intentionally refuses to join.
