# CYBERNYTE custom scripts

CYBERNYTE automatically loads valid `.py` files from this folder when it starts.
Files beginning with `_`, including `_template.py`, are ignored.

Every active script needs exactly these parts:

```python
PLUGIN_KEY = "B"
PLUGIN_NAME = "My tool"

def run(console):
    console.print("My tool is running!")
```

Use one unused letter from A through Z for `PLUGIN_KEY`. The built-in detector
already uses `D`, and the included system-snapshot example uses `A`. Restart
CYBERNYTE after adding or changing a script.

Custom scripts execute with the same Windows permissions as CYBERNYTE. Only add
code you wrote, reviewed, and trust. Keep cybersecurity tools lawful, defensive,
and limited to systems you own or are explicitly authorized to test.

