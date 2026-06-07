from __future__ import annotations

import argparse
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AGY_STATE_DIR = Path.home() / ".gemini" / "antigravity-cli"
LEGACY_STATE_DIR = Path.home() / ".antigravity" / "antigravity-cli"
URL_RE = re.compile(r"https?://\S+")
CODE_RE = re.compile(r"\b[A-Z0-9]{6,}\b")
AUTH_PROMPT = "Start Antigravity account authorization. If OAuth is required, show the browser verification URL and wait for the console code."


def _state_markers() -> list[Path]:
    return [
        AGY_STATE_DIR / "installation_id",
        AGY_STATE_DIR / "conversations",
        AGY_STATE_DIR / "cache",
        LEGACY_STATE_DIR / "settings.json",
    ]


def has_auth_marker() -> bool:
    return any(path.exists() for path in _state_markers())


def _run_capture(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)


def _print_models() -> int:
    proc = _run_capture(["agy", "models"], timeout=60)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode


def _verify_generation() -> bool:
    proc = _run_capture(["agy", "-p", "healthcheck: reply with ok", "--print-timeout", "60s"], timeout=90)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    return proc.returncode == 0


def is_ready() -> bool:
    return _run_capture(["agy", "models"], timeout=60).returncode == 0 and _verify_generation()


def _open_browser(url: str) -> bool:
    if webbrowser.open(url, new=1, autoraise=True):
        return True
    for cmd in (["xdg-open", url], ["flatpak-spawn", "--host", "xdg-open", url]):
        if shutil.which(cmd[0]) is None:
            continue
        try:
            subprocess.Popen(cmd)
            return True
        except Exception:
            continue
    return False


def _handle_output(text: str, opened_urls: set[str]) -> None:
    print(text, end="", flush=True)
    for url in URL_RE.findall(text):
        url = url.rstrip(".,);]")
        if url in opened_urls:
            continue
        opened_urls.add(url)
        print()
        if _open_browser(url):
            print(f"[antigravity-login] opened browser: {url}")
        else:
            print(f"[antigravity-login] open this URL manually: {url}")
    lower = text.lower()
    if "code" in lower or "verify" in lower or "oauth" in lower or "auth" in lower:
        match = CODE_RE.search(text)
        if match:
            print()
            print(f"[antigravity-login] detected code-like token: {match.group(0)}")


def _interactive_pty(cmd: list[str], timeout_sec: int) -> int:
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(cmd[0], cmd)

    opened_urls: set[str] = set()
    deadline = time.time() + timeout_sec
    ready_checked_at = 0.0

    if not sys.stdin.isatty():
        print("[antigravity-login] stdin is not a TTY; code input must happen in the agy/browser flow.")

    while True:
        if time.time() > deadline:
            print()
            print("[antigravity-login] timed out waiting for authorization", file=sys.stderr)
            try:
                os.kill(pid, 15)
            except OSError:
                pass
            return 1

        now = time.time()
        if now - ready_checked_at > 10:
            ready_checked_at = now
            if has_auth_marker() and _run_capture(["agy", "models"], timeout=30).returncode == 0:
                print()
                print(f"[antigravity-login] Antigravity state detected: {AGY_STATE_DIR}")
                return 0

        read_fds = [fd]
        if sys.stdin.isatty():
            read_fds.append(sys.stdin.fileno())
        readable, _, _ = select.select(read_fds, [], [], 0.5)

        if fd in readable:
            try:
                data = os.read(fd, 4096)
            except OSError:
                break
            if not data:
                break
            _handle_output(data.decode(errors="replace"), opened_urls)

        if sys.stdin.isatty() and sys.stdin.fileno() in readable:
            data = os.read(sys.stdin.fileno(), 4096)
            if data:
                os.write(fd, data)

        try:
            finished_pid, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return 0
        if finished_pid == pid:
            return os.waitstatus_to_exitcode(status)

    try:
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status)
    except ChildProcessError:
        return 0


def _login_log_path() -> Path:
    log_dir = AGY_STATE_DIR / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"login-helper-{stamp}.log"


def login_interactive(wait_timeout_sec: int = 600, force: bool = False) -> int:
    print("Starting Antigravity authorization session.")
    print("If a browser URL appears, this helper will try to open it.")
    print("If Antigravity asks for a code, paste it in this console and press Enter.")
    print(f"State directory: {AGY_STATE_DIR}")

    if not force and is_ready():
        print("Antigravity is already authorized and ready; browser login is not required.")
        _print_models()
        return 0

    log_file = _login_log_path()
    print(f"Log file: {log_file}")
    cmd = ["agy", "--log-file", str(log_file), "--prompt-interactive", AUTH_PROMPT]
    status = _interactive_pty(cmd, wait_timeout_sec)

    print()
    print("Checking Antigravity readiness...")
    models_status = _print_models()
    generation_ok = _verify_generation()
    if models_status == 0 and generation_ok:
        print("Antigravity is authorized and ready.")
        return 0
    print(f"Antigravity authorization was not confirmed. Check log: {log_file}", file=sys.stderr)
    return status or 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Antigravity login helper")
    parser.add_argument("--check", action="store_true", help="Check auth marker, models, and generation readiness")
    parser.add_argument("--login", action="store_true", help="Start browser/console authorization flow")
    parser.add_argument("--force-login", action="store_true", help="Start authorization flow even if agy already works")
    parser.add_argument("--models", action="store_true", help="Print available models")
    parser.add_argument("--verify", action="store_true", help="Run a small agy generation probe")
    parser.add_argument("--timeout", type=int, default=600, help="Seconds to wait for auth during --login")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.login or args.force_login:
        return login_interactive(wait_timeout_sec=max(30, args.timeout), force=args.force_login)

    if args.models:
        return _print_models()

    if args.verify:
        return 0 if _verify_generation() else 1

    if args.check:
        print(f"auth_marker_present={has_auth_marker()}")
        print(f"state_dir={AGY_STATE_DIR}")
        models_status = _print_models()
        generation_ok = _verify_generation()
        return 0 if models_status == 0 and generation_ok else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
