#!/usr/bin/env python3
"""CYBERNYTE: a defensive cybersecurity learning command center."""

from __future__ import annotations

import email
import getpass
import hashlib
import importlib.util
import ipaddress
import json
import os
import re
import socket
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    import psutil
    import requests
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from PIL import Image
    from pyfiglet import Figlet
    from rich.align import Align
    from rich.console import Console
    from rich.console import Group
    from rich.panel import Panel
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Missing dependencies. Run: python -m pip install -r requirements.txt")
    raise SystemExit(1)

console = Console()
APP_DIR = Path.home() / ".cybernyte"
APP_DIR.mkdir(exist_ok=True)

GRADIENT = ["#ff1010", "#ff3010", "#ff5a00", "#ff7b00", "#ffad42", "#ffffff"]
ASCII_RAMP = "@#%&890OQ1!?+=-:;,."
DISCLAIMER = (
    "DISCLAIMER: This project was made by me (@motionmanryan), in attempts to make cybersecurity a bigger "
    "talked about topic. Your security online is very important, which is why its even more important to try "
    "and know the basics of internet protection."
)


def asset_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "assets" / name


def application_dir() -> Path:
    """Folder containing the script, or the executable when packaged."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def logo_renderable(target_width: int = 92, vertical_scale: int = 3) -> Group:
    """Large CYBERNYTE wordmark stretched in both terminal dimensions."""
    figlet = Figlet(font="ansi_shadow", width=120)
    lines = figlet.renderText("CYBERNYTE").rstrip().splitlines()
    source_width = max(map(len, lines))
    rendered = []
    for index, line in enumerate(lines):
        color = GRADIENT[min(index, len(GRADIENT) - 1)]
        padded = line.ljust(source_width)
        widened = "".join(
            padded[min(source_width - 1, (column * source_width) // target_width)]
            for column in range(target_width)
        ).rstrip()
        for _ in range(vertical_scale):
            rendered.append(Text(widened, style=f"bold {color}"))
    rendered.append(Text("━━ DEFENSIVE SECURITY COMMAND CENTER // NIGHT OPS ━━", style="bold white"))
    return Group(*rendered)


def _mix_color(start: tuple[int, int, int], end: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end))


def _reaper_color(pixel: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """Tint a grayscale source pixel into CYBERNYTE's red/orange/white theme."""
    red, green, blue, alpha = pixel
    luminance = (red * 299 + green * 587 + blue * 114) // 1000
    if luminance < 40:
        color = _mix_color((82, 0, 0), (235, 30, 0), luminance / 40)
    elif luminance < 120:
        color = _mix_color((235, 30, 0), (255, 132, 0), (luminance - 40) / 80)
    else:
        color = _mix_color((255, 132, 0), (255, 255, 255), (luminance - 120) / 135)
    # Preblend antialiased transparent edges against the terminal's black base.
    return tuple(round(channel * (alpha / 255)) for channel in color)


def _rgb(color: tuple[int, int, int]) -> str:
    return f"rgb({color[0]},{color[1]},{color[2]})"


def photo_renderable(width: int = 54, rows: int | None = None, asset: str = "reaper-block-cutout.png") -> Text:
    """Render the transparent Reaper cutout with true-color half-block pixels."""
    source = Image.open(asset_path(asset)).convert("RGBA")
    alpha_mask = source.getchannel("A").point(lambda alpha: 255 if alpha >= 24 else 0)
    bounds = alpha_mask.getbbox()
    if bounds:
        source = source.crop(bounds)

    pixel_rows = rows * 2 if rows is not None else max(2, round((source.height / source.width) * width))
    if pixel_rows % 2:
        pixel_rows += 1
    source = source.resize((width, pixel_rows), Image.Resampling.LANCZOS)

    output = Text()
    terminal_rows = pixel_rows // 2
    for y in range(0, pixel_rows, 2):
        for x in range(width):
            top = source.getpixel((x, y))
            bottom = source.getpixel((x, y + 1))
            top_visible = top[3] >= 24
            bottom_visible = bottom[3] >= 24
            if not top_visible and not bottom_visible:
                output.append(" ")
            elif top_visible and bottom_visible:
                output.append("▀", style=f"{_rgb(_reaper_color(top))} on {_rgb(_reaper_color(bottom))}")
            elif top_visible:
                output.append("▀", style=_rgb(_reaper_color(top)))
            else:
                output.append("▄", style=_rgb(_reaper_color(bottom)))
        if (y // 2) + 1 < terminal_rows:
            output.append("\n")
    return output


def command_prompt_renderable() -> Panel:
    return Panel.fit(
        "[bold white]PRESS ANY DISPLAYED COMMAND KEY[/]",
        border_style="#ff650d",
    )


def menu_key(show_prompt: bool = True) -> str:
    """Read one menu key immediately on Windows; use Enter elsewhere."""
    if show_prompt:
        console.print(command_prompt_renderable())
    if os.name == "nt":
        import msvcrt
        while True:
            key = msvcrt.getwch().upper()
            if key in TOOLS or key == "0":
                console.print(f"[bold white]Selected:[/] [bold #ff650d]{key}[/]")
                return key
    return console.input("[bold #ff650d]CYBERNYTE > [/]").strip().upper()


def pause() -> None:
    console.input("\n[dim]Press Enter to return to the command center...[/]")


def path_prompt(label: str) -> Path:
    raw = Prompt.ask(label).strip().strip('"')
    return Path(raw).expanduser().resolve()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def port_scanner() -> None:
    console.rule("[bold cyan]Authorized Local/Private Port Scanner")
    target = Prompt.ask("Hostname or private IP", default="127.0.0.1")
    try:
        resolved = socket.gethostbyname(target)
        ip = ipaddress.ip_address(resolved)
    except (socket.gaierror, ValueError) as exc:
        console.print(f"[red]Could not resolve target:[/] {exc}")
        return
    if not (ip.is_private or ip.is_loopback):
        console.print("[red]CYBERNYTE only scans loopback or private-network addresses.[/]")
        return
    if not Confirm.ask(f"Do you own or have permission to scan {target} ({resolved})?"):
        return
    start = IntPrompt.ask("Starting port", default=1)
    end = IntPrompt.ask("Ending port", default=1024)
    if not (1 <= start <= end <= 65535) or end - start > 4095:
        console.print("[red]Use a valid range of at most 4,096 ports.[/]")
        return

    def check(port: int):
        with socket.socket() as sock:
            sock.settimeout(0.25)
            if sock.connect_ex((resolved, port)) == 0:
                try:
                    service = socket.getservbyport(port)
                except OSError:
                    service = "unknown"
                return port, service
        return None

    found = []
    with console.status("Scanning authorized target..."):
        with ThreadPoolExecutor(max_workers=100) as pool:
            jobs = [pool.submit(check, p) for p in range(start, end + 1)]
            for job in as_completed(jobs):
                result = job.result()
                if result:
                    found.append(result)
    table = Table("Port", "Likely service", title=f"Open ports on {resolved}")
    for port, service in sorted(found):
        table.add_row(str(port), service)
    console.print(table if found else "[green]No open ports found in that range.[/]")


def integrity_monitor() -> None:
    console.rule("[bold cyan]File Integrity Monitor")
    path = path_prompt("File or folder to monitor")
    database = APP_DIR / "integrity.json"
    prior = json.loads(database.read_text()) if database.exists() else {}
    files = [path] if path.is_file() else list(path.rglob("*")) if path.is_dir() else []
    files = [p for p in files if p.is_file()]
    if not files:
        console.print("[red]No readable files found.[/]")
        return
    current = {str(p): sha256_file(p) for p in files}
    changed = [p for p, h in current.items() if p in prior and prior[p] != h]
    new = [p for p in current if p not in prior]
    missing = [p for p in prior if (p == str(path) or p.startswith(str(path) + os.sep)) and p not in current]
    table = Table("Status", "File")
    for status, items, color in (("CHANGED", changed, "yellow"), ("NEW", new, "green"), ("MISSING", missing, "red")):
        for item in items:
            table.add_row(f"[{color}]{status}[/]", item)
    console.print(table if changed or new or missing else "[green]No changes detected.[/]")
    if Confirm.ask("Save this as the new baseline?", default=True):
        prior.update(current)
        for item in missing:
            prior.pop(item, None)
        database.write_text(json.dumps(prior, indent=2))


def password_analyzer() -> None:
    console.rule("[bold cyan]Password Strength Analyzer")
    password = getpass.getpass("Password (hidden; never stored): ")
    score = 0
    checks = {
        "12+ characters": len(password) >= 12,
        "16+ characters": len(password) >= 16,
        "Uppercase and lowercase": any(c.isupper() for c in password) and any(c.islower() for c in password),
        "Contains a number": any(c.isdigit() for c in password),
        "Contains a symbol": any(c in string.punctuation for c in password),
        "Avoids obvious sequences": not re.search(r"(?i)password|qwerty|1234|admin|letmein", password),
    }
    score = sum(checks.values())
    table = Table("Check", "Result")
    for check, passed in checks.items():
        table.add_row(check, "[green]PASS[/]" if passed else "[red]IMPROVE[/]")
    console.print(table)
    label = "Strong" if score >= 5 else "Fair" if score >= 3 else "Weak"
    console.print(f"Rating: [bold]{label} ({score}/6)[/] — prefer a unique 16+ character passphrase and MFA.")


def log_analyzer() -> None:
    console.rule("[bold cyan]Security Log Analyzer")
    path = path_prompt("Plain-text log file")
    if not path.is_file():
        console.print("[red]File not found.[/]")
        return
    patterns = {
        "Failed login": re.compile(r"failed (?:login|password)|authentication failure|invalid user", re.I),
        "Access denied": re.compile(r"access denied|permission denied|forbidden", re.I),
        "Possible scan": re.compile(r"port scan|nmap|masscan", re.I),
        "Malware term": re.compile(r"malware|trojan|ransomware|virus detected", re.I),
    }
    counts = {name: 0 for name in patterns}
    examples = []
    with path.open(errors="replace") as stream:
        for number, line in enumerate(stream, 1):
            for name, pattern in patterns.items():
                if pattern.search(line):
                    counts[name] += 1
                    if len(examples) < 12:
                        examples.append((number, name, line.strip()[:100]))
    table = Table("Indicator", "Count")
    for name, count in counts.items():
        table.add_row(name, str(count))
    console.print(table)
    for number, name, sample in examples:
        console.print(f"[yellow]Line {number} · {name}:[/] {sample}")


def header_scanner() -> None:
    console.rule("[bold cyan]HTTP Security Header Scanner")
    url = Prompt.ask("Website URL you own or are authorized to assess")
    if not urlparse(url).scheme:
        url = "https://" + url
    wanted = {
        "strict-transport-security": "HSTS",
        "content-security-policy": "Content-Security-Policy",
        "x-content-type-options": "X-Content-Type-Options",
        "x-frame-options": "X-Frame-Options",
        "referrer-policy": "Referrer-Policy",
        "permissions-policy": "Permissions-Policy",
    }
    try:
        response = requests.get(url, timeout=8, allow_redirects=True, stream=True)
    except requests.RequestException as exc:
        console.print(f"[red]Request failed:[/] {exc}")
        return
    table = Table("Protection", "Status")
    present = 0
    lower = {k.lower(): v for k, v in response.headers.items()}
    for key, label in wanted.items():
        ok = key in lower
        present += ok
        table.add_row(label, "[green]Present[/]" if ok else "[yellow]Missing[/]")
    console.print(f"Final URL: {response.url} · HTTP {response.status_code}")
    console.print(table)
    console.print(f"Basic header score: [bold]{present}/{len(wanted)}[/] (manual review is still required)")
    response.close()


def phishing_analyzer() -> None:
    console.rule("[bold cyan]Phishing Email Header Analyzer")
    path = path_prompt("Saved .eml or email-header text file")
    if not path.is_file():
        console.print("[red]File not found.[/]")
        return
    message = email.message_from_bytes(path.read_bytes())
    sender, reply_to, return_path = message.get("From", ""), message.get("Reply-To", ""), message.get("Return-Path", "")
    auth = message.get("Authentication-Results", "")
    findings = []
    if reply_to and sender and reply_to.split("@")[-1].lower() not in sender.lower():
        findings.append("Reply-To domain may differ from the From address")
    if return_path and sender and return_path.split("@")[-1].strip("> ").lower() not in sender.lower():
        findings.append("Return-Path domain may differ from the From address")
    for method in ("spf", "dkim", "dmarc"):
        if re.search(fr"{method}=fail", auth, re.I):
            findings.append(f"{method.upper()} authentication failed")
    if re.search(r"urgent|verify.*account|gift card|wire transfer|password expires", message.get("Subject", ""), re.I):
        findings.append("Subject contains a common social-engineering phrase")
    console.print(f"From: {sender or '[missing]'}\nReply-To: {reply_to or '[missing]'}\nSubject: {message.get('Subject', '[missing]')}")
    if findings:
        for item in findings:
            console.print(f"[yellow]• {item}[/]")
    else:
        console.print("[green]No basic red flags found. This does not prove the message is safe.[/]")


def connection_dashboard() -> None:
    console.rule("[bold cyan]Local Network Connection Dashboard")
    table = Table("Protocol", "Local", "Remote", "Status", "PID")
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        console.print("[red]Access denied. Try running the terminal as Administrator.[/]")
        return
    for item in connections[:150]:
        proto = "TCP" if item.type == socket.SOCK_STREAM else "UDP"
        local = f"{item.laddr.ip}:{item.laddr.port}" if item.laddr else "-"
        remote = f"{item.raddr.ip}:{item.raddr.port}" if item.raddr else "-"
        table.add_row(proto, local, remote, item.status or "-", str(item.pid or "-"))
    console.print(table)
    console.print(f"Displayed {min(len(connections), 150)} of {len(connections)} local connections/listeners.")


def static_file_analyzer() -> None:
    console.rule("[bold cyan]Static Suspicious-File Analyzer")
    path = path_prompt("File to inspect (it will NOT be executed)")
    if not path.is_file():
        console.print("[red]File not found.[/]")
        return
    size = path.stat().st_size
    data = path.read_bytes()[:5_000_000]
    text_data = "\n".join(x.decode("ascii", "ignore") for x in re.findall(rb"[ -~]{6,}", data))
    indicators = {
        "PowerShell command": r"powershell(?:\.exe)?",
        "Command shell": r"cmd\.exe|/bin/(?:ba)?sh",
        "Encoded command": r"-enc(?:odedcommand)?\b|frombase64string",
        "Downloads content": r"downloadstring|urlretrieve|invoke-webrequest|curl\s+https?",
        "Persistence registry path": r"currentversion\\run|currentversion\\runonce",
        "Credential-related term": r"credential|password|browser.*cookie",
    }
    found = [name for name, pattern in indicators.items() if re.search(pattern, text_data, re.I)]
    console.print(f"Name: {path.name}\nSize: {size:,} bytes\nSHA-256: {sha256_file(path)}")
    if found:
        for item in found:
            console.print(f"[yellow]• {item}[/]")
        console.print("[dim]Indicators are clues, not proof of malware. Do not execute an untrusted file.[/]")
    else:
        console.print("[green]No basic string indicators found. This does not prove the file is safe.[/]")


def derive_key(password: str, salt: bytes) -> bytes:
    import base64
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def prompt_vault_password(confirm: bool) -> str | None:
    """Ask for a vault password, either hidden or visible on screen.

    When confirm is True (encrypting), the password must be entered twice
    and both entries must match. Returns None if the user cancels or the
    entries don't satisfy the requirements.
    """
    visible = Confirm.ask(
        "Show the password on screen while typing? (hidden is more secure)",
        default=False,
    )
    entry_fn = (lambda label: Prompt.ask(label)) if visible else (lambda label: getpass.getpass(label + " "))

    password = entry_fn("Vault password (do not lose it):")
    if len(password) < 12:
        console.print("[red]Use at least 12 characters.[/]")
        return None

    if confirm:
        again = entry_fn("Re-enter the password to confirm:")
        if password != again:
            console.print("[red]Passwords did not match. Try again.[/]")
            return None

    return password


def encrypted_vault() -> None:
    console.rule("[bold cyan]Encrypted File Vault")
    mode = Prompt.ask("Choose action", choices=["encrypt", "decrypt"])
    source = path_prompt("Input file")
    if not source.is_file():
        console.print("[red]File not found.[/]")
        return
    password = prompt_vault_password(confirm=(mode == "encrypt"))
    if password is None:
        return
    if mode == "encrypt":
        salt = os.urandom(16)
        output = source.with_name(source.name + ".cybernyte")
        output.write_bytes(b"CYBERNYTE1" + salt + Fernet(derive_key(password, salt)).encrypt(source.read_bytes()))
        console.print(f"[green]Encrypted copy created:[/] {output}")
        console.print("[yellow]The original was not deleted.[/]")
    else:
        blob = source.read_bytes()
        if not blob.startswith(b"CYBERNYTE1"):
            console.print("[red]Not a CYBERNYTE vault file.[/]")
            return
        salt, token = blob[10:26], blob[26:]
        output = source.with_suffix("") if source.suffix == ".cybernyte" else source.with_name(source.name + ".decrypted")
        try:
            output.write_bytes(Fernet(derive_key(password, salt)).decrypt(token))
            console.print(f"[green]Decrypted copy created:[/] {output}")
        except InvalidToken:
            console.print("[red]Wrong password or damaged file.[/]")


def rat_detector() -> None:
    """Defensive review of persistence entries and remote connections."""
    console.rule("[bold #ff3d16]RAT & Persistence Warning-Sign Detector")
    findings = []
    if os.name == "nt":
        import winreg
        locations = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU RunOnce"),
        ]
        for root, key_path, label in locations:
            try:
                with winreg.OpenKey(root, key_path) as key:
                    index = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, index)
                            findings.append((label, name, str(value)))
                            index += 1
                        except OSError:
                            break
            except (FileNotFoundError, PermissionError):
                pass
        startup = Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        if startup.is_dir():
            for item in startup.iterdir():
                if item.name.lower() != "desktop.ini":
                    findings.append(("Startup folder", item.name, str(item)))
    else:
        console.print("[yellow]Registry persistence checks are Windows-only.[/]")

    table = Table("Location", "Entry", "Command / path", border_style="#ff650d")
    for location, name, value in findings:
        table.add_row(location, name, value[:120])
    console.print(table if findings else "[green]No common startup entries were found.[/]")

    external = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "ESTABLISHED" and conn.raddr:
                try:
                    remote_ip = ipaddress.ip_address(conn.raddr.ip)
                except ValueError:
                    continue
                if not (remote_ip.is_private or remote_ip.is_loopback):
                    process = "unknown"
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid).name()
                        except (psutil.Error, PermissionError):
                            pass
                    external.append((process, str(conn.pid or "-"), f"{conn.raddr.ip}:{conn.raddr.port}"))
    except (psutil.AccessDenied, PermissionError):
        console.print("[yellow]Run as Administrator to inspect all connections.[/]")
    remote_table = Table("Process", "PID", "Established external connection", border_style="#ff8c00")
    for row in external[:75]:
        remote_table.add_row(*row)
    console.print(remote_table if external else "[green]No visible established external connections.[/]")
    console.print(
        "[dim]Startup entries and remote connections are often legitimate. Review unfamiliar items; "
        "do not delete anything based only on this screen.[/]"
    )


TOOLS = {
    "1": ("Authorized local/private port scanner", port_scanner),
    "2": ("File integrity monitor", integrity_monitor),
    "3": ("Password strength analyzer", password_analyzer),
    "4": ("Security log analyzer", log_analyzer),
    "5": ("HTTP security header scanner", header_scanner),
    "6": ("Phishing email header analyzer", phishing_analyzer),
    "7": ("Local network connection dashboard", connection_dashboard),
    "8": ("Static suspicious-file analyzer", static_file_analyzer),
    "9": ("Encrypted file vault", encrypted_vault),
    "D": ("RAT & persistence warning-sign detector", rat_detector),
}

PLUGIN_ERRORS = []


def load_plugins() -> None:
    """Load validated user scripts from the external plugins directory."""
    plugins_dir = application_dir() / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    for script in sorted(plugins_dir.glob("*.py")):
        if script.name.startswith("_"):
            continue
        try:
            module_name = f"cybernyte_plugin_{script.stem}"
            spec = importlib.util.spec_from_file_location(module_name, script)
            if spec is None or spec.loader is None:
                raise ValueError("Python could not load the file")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            key = str(getattr(module, "PLUGIN_KEY", "")).strip().upper()
            name = str(getattr(module, "PLUGIN_NAME", "")).strip()
            runner = getattr(module, "run", None)
            if len(key) != 1 or key not in string.ascii_uppercase:
                raise ValueError("PLUGIN_KEY must be one letter from A to Z")
            if key in TOOLS or key == "D":
                raise ValueError(f"menu key {key!r} is already in use")
            if not name:
                raise ValueError("PLUGIN_NAME cannot be empty")
            if not callable(runner):
                raise ValueError("the script needs a run(console) function")

            def launch(plugin_runner=runner):
                plugin_runner(console)

            TOOLS[key] = (f"Custom · {name}", launch)
        except Exception as exc:
            PLUGIN_ERRORS.append(f"{script.name}: {exc}")


load_plugins()


def status_renderable() -> Panel:
    return Panel.fit(
        f"DEFENSIVE SECURITY COMMAND CENTER\n{socket.gethostname()} · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        style="bold white",
        border_style="#ff3d16",
    )


def tools_renderable() -> Table:
    table = Table("Command", "Module", show_header=False, border_style="#ff650d", padding=(0, 1))
    for key, (name, _) in TOOLS.items():
        table.add_row(f"[bold #ff3d16]{key}[/]", f"[white]{name}[/]")
    table.add_row("[bold #ff3d16]0[/]", "[white]Exit[/]")
    return table


def left_dashboard_renderable() -> Group:
    parts = [logo_renderable(), status_renderable(), tools_renderable()]
    if PLUGIN_ERRORS:
        parts.append(Text(
            f"Skipped {len(PLUGIN_ERRORS)} invalid custom script(s). See plugins/README.md.",
            style="yellow",
        ))
    parts.extend([
        Text(DISCLAIMER, style="dim white", justify="left", overflow="fold"),
        command_prompt_renderable(),
    ])
    return Group(*parts)


def print_dashboard() -> None:
    """Keep controls high on the left while the larger Reaper fills the right."""
    left = left_dashboard_renderable()
    if console.width >= 176:
        dashboard = Table.grid(padding=(0, 1))
        dashboard.add_column(width=104)
        dashboard.add_column(width=70)
        dashboard.add_row(left, Align.center(photo_renderable(width=68), vertical="top"))
        console.print(dashboard)
    else:
        # On narrow terminals, prioritize keeping every command visible first.
        console.print(left)
        console.print(Align.center(photo_renderable(width=min(60, max(36, console.width - 4)))))


def main() -> None:
    while True:
        console.clear()
        print_dashboard()
        choice = menu_key(show_prompt=False)
        if choice == "0":
            console.print("[cyan]Stay curious. Stay ethical.[/]")
            return
        if choice in TOOLS:
            try:
                TOOLS[choice][1]()
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled.[/]")
            except Exception as exc:
                console.print(f"[red]Module error:[/] {exc}")
            pause()
        else:
            console.print("[yellow]Choose a displayed command key.[/]")
            time.sleep(1)


if __name__ == "__main__":
    main()
