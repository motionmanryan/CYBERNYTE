# CYBERNYTE

CYBERNYTE is a defensive cybersecurity learning command center for Windows,
macOS, and Linux. It uses a styled terminal interface and contains nine modules:

Its header uses a vertically stretched wordmark and converts the included
transparent grim-reaper artwork into terminal art made entirely from numbers,
punctuation, signs, and dashes. The portrait uses foreground text colors only—
no color blocks, background, box, or image label. It automatically resizes to
fill the visible height of your terminal window. The Windows launcher requests
a 150-column console so the character remains aligned to the right of the logo.
If the terminal is narrower, the app automatically stacks the character beneath
the logo instead of distorting it.

1. Authorized local/private port scanner
2. File integrity monitor
3. Password strength analyzer
4. Security log analyzer
5. HTTP security header scanner
6. Phishing email header analyzer
7. Local network connection dashboard
8. Static suspicious-file analyzer
9. Encrypted file vault
10. RAT and persistence warning-sign detector (`D` key)
11. Automatic custom-script plug-ins from the `plugins` folder

On Windows, the main menu accepts a single number key immediately—there is no
need to press Enter. Follow-up questions appear in high-contrast text and still
use Enter after you type an answer.

## Add your own scripts

Read `CUSTOM_SCRIPTS_GUIDE.md`. In short, copy `plugins/_template.py`, rename
the copy, select an unused letter, and put your code inside its `run(console)`
function. CYBERNYTE discovers valid plug-ins automatically when it starts. The
included `A` command is a working system-snapshot example.

## Windows setup

1. Install Python 3.10 or newer from https://python.org and enable **Add Python to PATH**.
2. Extract the downloaded ZIP.
3. Double-click `install.bat` once.
4. Double-click `run_cybernyte.bat` whenever you want to launch the app.

Or use Command Prompt:

```bat
python -m pip install -r requirements.txt
python cybernyte.py
```

## Optional: build CYBERNYTE.exe

```bat
python -m pip install pyinstaller
pyinstaller --onefile --name CYBERNYTE --add-data "assets\\reaper-cutout.png;assets" cybernyte.py
```

The executable will be created at `dist\CYBERNYTE.exe`. Antivirus tools may
inspect or flag newly packaged unsigned executables, so keep the Python source
and only distribute software you built and understand.

## Ethical-use rule

Only analyze devices, networks, websites, email, logs, and files that you own or
have explicit permission to test. The port scanner intentionally limits targets
to loopback and private-network IP addresses.

## Notes

- The file vault creates a new encrypted/decrypted copy and never deletes the original.
- Passwords entered into the password analyzer are not saved.
- Static findings and email findings are indicators, not proof that content is safe or malicious.
- Some network-connection details may require an Administrator terminal.
