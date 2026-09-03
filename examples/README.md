# Example

`messy.txt` is a synthetic copy/paste sample. It contains a wrapped paragraph,
a line-ending word hyphen, a non-breaking space, a list, and a URL.

```console
linepatch messy.txt --diff
linepatch messy.txt --output clean.txt
```

`clean.txt` is the expected reviewed result. It contains no personal or source
document content.
