# -*- coding: utf-8 -*-
"""
Multi-Provider AI CLI  *  cleanskiier27/gemini-cli
Providers: Google Gemini  |  Anthropic Claude  |  Alibaba Qwen  |  Microsoft Foundry
Usage:
  python gemini_cli.py                          interactive
  python gemini_cli.py "question"               one-shot
  python gemini_cli.py --set-key KEY            Gemini API key
  python gemini_cli.py --set-claude-key KEY     Anthropic API key
  python gemini_cli.py --set-qwen-key KEY       Dashscope API key
  python gemini_cli.py --set-foundry-key KEY    Azure AI / GitHub token
  python gemini_cli.py --set-foundry-url URL    Azure AI endpoint
  python gemini_cli.py --list-models            all available models
"""

import os
import sys
import json
import time
import textwrap
import urllib.request
import urllib.error

# ── ANSI colour palette ────────────────────────────────────────────
R    = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"

GEM = "\033[38;5;135m"   # purple   – Gemini / header
COP = "\033[38;5;75m"    # blue     – Copilot label
USR = "\033[38;5;51m"    # cyan     – user prompt
ACT = "\033[38;5;219m"   # pink     – active model badge
INF = "\033[38;5;245m"   # grey     – info
WRN = "\033[38;5;214m"   # amber    – warnings
ERR = "\033[38;5;196m"   # red      – errors
OK  = "\033[38;5;82m"    # green    – success
SEP = "\033[38;5;57m"    # indigo   – separators

TERMINAL_WIDTH = 72

# ── Providers ────────────────────────────────────────────────────
GEMINI_API_BASE  = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_LIST_URL  = "https://generativelanguage.googleapis.com/v1beta/models"
COPILOT_API_URL  = "https://api.githubcopilot.com/chat/completions"

# Gemini free-tier fallback chain
GEMINI_FALLBACK = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

# GitHub Copilot models
COPILOT_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "o1",
    "o3-mini",
    "claude-3.5-sonnet",
    "claude-3.7-sonnet",
]

MODEL_FALLBACK = GEMINI_FALLBACK  # default provider
HISTORY        = []
ACTIVE_MODEL   = MODEL_FALLBACK[0]

PROVIDER_LABELS = {
    "gemini":  (GEM, "Google Gemini"),
    "copilot": (COP, "GitHub Copilot"),
}

# ── Helpers ──────────────────────────────────────────────────────────────
def _colour_wrap(text, colour, width=TERMINAL_WIDTH, indent=0):
    prefix = " " * indent
    lines  = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        wrapped = textwrap.fill(para, width=width - indent,
                                initial_indent=prefix, subsequent_indent=prefix)
        lines.append(wrapped)
    return colour + "\n".join(lines) + R


def _hr(char="─", colour=SEP):
    return colour + char * TERMINAL_WIDTH + R


# ── Key management ────────────────────────────────────────────────────────
def _key_file():
    return os.path.join(os.path.expanduser("~"), ".gemini_key")


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and os.path.exists(_key_file()):
        with open(_key_file()) as f:
            key = f.read().strip()
    if not key:
        print(f"{WRN}No API key found.{R}")
        print(f"{DIM}Save one with:  python gemini_cli.py --set-key YOUR_KEY{R}\n")
        key = input(f"{USR}Paste your Gemini API key: {R}").strip()
        if not key:
            print(f"{ERR}No key provided. Exiting.{R}")
            sys.exit(1)
        with open(_key_file(), "w") as f:
            f.write(key)
        print(f"{OK}  Key saved to {_key_file()}{R}\n")
    return key


def save_key(key):
    with open(_key_file(), "w") as f:
        f.write(key.strip())
    print(f"{OK}  Gemini API key saved to {_key_file()}{R}")


def _copilot_key_file():
    return os.path.join(os.path.expanduser("~"), ".copilot_key")


def get_copilot_key(prompt=False):
    key = os.environ.get("GITHUB_TOKEN", "")
    if not key and os.path.exists(_copilot_key_file()):
        with open(_copilot_key_file()) as f:
            key = f.read().strip()
    if not key and prompt:
        print(f"{WRN}No GitHub token found.{R}")
        print(f"{DIM}Get one at: https://github.com/settings/tokens  (copilot scope){R}\n")
        key = input(f"{USR}Paste your GitHub token: {R}").strip()
        if key:
            with open(_copilot_key_file(), "w") as f:
                f.write(key)
            print(f"{OK}  Copilot key saved to {_copilot_key_file()}{R}\n")
    return key


def save_copilot_key(key):
    with open(_copilot_key_file(), "w") as f:
        f.write(key.strip())
    print(f"{OK}  GitHub Copilot key saved to {_copilot_key_file()}{R}")


# ── API calls ──────────────────────────────────────────────────────────────
def list_models(api_key):
    url = f"{GEMINI_LIST_URL}?key={api_key}"
    try:
        req  = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        return [
            m["name"].replace("models/", "")
            for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
    except Exception as e:
        return [f"[Error: {e}]"]


def ask_gemini(api_key, user_message):
    global ACTIVE_MODEL
    HISTORY.append({"role": "user", "parts": [{"text": user_message}]})

    for model in MODEL_FALLBACK:
        url     = GEMINI_API_BASE.format(model=model) + f"?key={api_key}"
        payload = json.dumps({"contents": HISTORY}).encode()
        req     = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
            if model != ACTIVE_MODEL:
                print(f"\n{INF}  switched to {ACT}{model}{R}")
                ACTIVE_MODEL = model
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            HISTORY.append({"role": "model", "parts": [{"text": text}]})
            return text
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            try:
                msg = json.loads(body).get("error", {}).get("message", body)
            except Exception:
                msg = body
            if e.code == 429:
                print(f"  {INF}quota hit on {model} — trying next...{R}")
                time.sleep(1)
                continue
            HISTORY.pop()
            return f"{ERR}[API {e.code}] {msg}{R}"
        except (KeyError, IndexError):
            break
        except Exception as exc:
            HISTORY.pop()
            return f"{ERR}[Error] {exc}{R}"

    HISTORY.pop()
    return (
        f"{ERR}All models exceeded quota.{R}\n"
        f"{DIM}  Check https://ai.dev/rate-limit{R}"
    )


def _provider(model):
    m = model.lower()
    if m.startswith(("gemini", "gemma", "nano")):
        return "gemini"
    return "copilot"


def _oai_history():
    msgs = []
    for entry in HISTORY:
        role = "assistant" if entry["role"] == "model" else entry["role"]
        msgs.append({"role": role, "content": entry["parts"][0]["text"]})
    return msgs


def ask_copilot(api_key, user_message):
    HISTORY.append({"role": "user", "parts": [{"text": user_message}]})
    payload = json.dumps({"model": ACTIVE_MODEL, "messages": _oai_history()}).encode()
    req = urllib.request.Request(
        COPILOT_API_URL, data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}",
                 "Copilot-Integration-Id": "vscode-chat"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
        text = result["choices"][0]["message"]["content"]
        HISTORY.append({"role": "model", "parts": [{"text": text}]})
        return text
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:    msg = json.loads(body).get("error", {}).get("message", body)
        except: msg = body
        HISTORY.pop()
        return f"{ERR}[API {e.code}] {msg}{R}"
    except Exception as exc:
        HISTORY.pop()
        return f"{ERR}[Error] {exc}{R}"


def ask(user_message, gemini_key):
    provider = _provider(ACTIVE_MODEL)
    if provider == "gemini":
        return ask_gemini(gemini_key, user_message)
    key = get_copilot_key(prompt=True)
    if not key:
        return f"{ERR}No GitHub token. Run: python gemini_cli.py --set-copilot-key KEY{R}"
    return ask_copilot(key, user_message)


# ── UI ────────────────────────────────────────────────────────────────────────
GEMINI_LOGO = (
    f"{GEM}{BOLD}"
    "  ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██╗\n"
    "  ██╔════╝██╔════╝████╗ ████║██║████╗  ██║██║\n"
    "  ██║     █████╗  ██╔████╔██║██║██╔██╗ ██║██║\n"
    "  ██║     ██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║\n"
    "  ╚██████╗███████╗██║ ╚═╝ ██║██║██║ ╚████║██║\n"
    "   ╚═════╝╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝"
    f"{R}"
)


def print_banner():
    print()
    print(GEMINI_LOGO)
    print()
    print(_hr())
    prov = _provider(ACTIVE_MODEL)
    print(f"  {BOLD}cleanskiier27 / gemini-cli{R}   {DIM}local agent · Python{R}")
    print(f"  {DIM}Model   :{R} {ACT}{BOLD}{ACTIVE_MODEL}{R}")
    print(f"  {DIM}Provider:{R} {DIM}{prov}{R}")
    print(f"  {DIM}Docs    :{R} {DIM}github.com/cleanskiier27/gemini-cli{R}")
    print(_hr())
    print(f"  {DIM}Type {R}{USR}/help{DIM} for commands  ·  Ctrl-C or {R}{USR}exit{DIM} to quit{R}")
    print()


def print_help():
    cmds = [
        ("/help",             "Show this help"),
        ("/model [name]",     "Show or switch active model"),
        ("/models",           "List Google Gemini models"),
        ("/models copilot",   "List GitHub Copilot models"),
        ("/clear",            "Clear conversation history"),
        ("/history",          "Show conversation turn count"),
        ("exit / quit",       "Exit the agent"),
    ]
    print()
    print(_hr("="))
    print(f"  {GEM}{BOLD}Commands{R}")
    print(_hr("-"))
    for cmd, desc in cmds:
        print(f"  {USR}{cmd:<24}{R}  {DIM}{desc}{R}")
    print(_hr("="))
    print()


def handle_slash(cmd, api_key):
    global ACTIVE_MODEL
    parts = cmd.strip().lstrip("/").split(maxsplit=1)
    verb  = parts[0].lower()
    arg   = parts[1].strip() if len(parts) > 1 else ""

    if verb == "help":
        print_help()
    elif verb == "clear":
        HISTORY.clear()
        print(f"  {OK}Conversation cleared.{R}\n")
    elif verb == "history":
        turns = len(HISTORY) // 2
        print(f"  {INF}{len(HISTORY)} messages  ({turns} turns){R}\n")
    elif verb == "models":
        sub = arg.lower()
        if sub == "copilot":
            print(f"\n  {COP}{BOLD}GitHub Copilot{R}")
            for m in COPILOT_MODELS:
                marker = f"{ACT} * " if m == ACTIVE_MODEL else f"{DIM}   "
                print(f"{marker}{m}{R}")
        else:
            print(f"  {DIM}Fetching Gemini models...{R}")
            models = list_models(api_key)
            print(f"\n  {GEM}{BOLD}Google Gemini{R}")
            for m in models:
                marker = f"{ACT} * " if m == ACTIVE_MODEL else f"{DIM}   "
                print(f"{marker}{m}{R}")
        print()
    elif verb == "model":
        if not arg:
            print(f"  {DIM}Active model:{R} {ACT}{BOLD}{ACTIVE_MODEL}{R}\n")
        else:
            ACTIVE_MODEL = arg
            if arg in MODEL_FALLBACK:
                MODEL_FALLBACK.remove(arg)
            MODEL_FALLBACK.insert(0, arg)
            print(f"  {OK}Switched to {BOLD}{ACTIVE_MODEL}{R}\n")
    else:
        print(f"  {WRN}Unknown command: /{verb}   (type /help){R}\n")


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--set-key":
        save_key(sys.argv[2]); return
    if len(sys.argv) == 3 and sys.argv[1] == "--set-copilot-key":
        save_copilot_key(sys.argv[2]); return

    api_key = get_api_key()

    if len(sys.argv) == 2 and sys.argv[1] == "--list-models":
        print("\n-- Google Gemini --")
        for m in list_models(api_key): print("  ", m)
        print("\n-- GitHub Copilot --")
        for m in COPILOT_MODELS: print("  ", m)
        return

    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        print(ask(" ".join(sys.argv[1:]), api_key))
        return

    # ── interactive ──
    print_banner()

    while True:
        try:
            user_input = input(f"{USR}{BOLD}>{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye.{R}\n")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handle_slash(user_input, api_key)
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print(f"\n{DIM}Goodbye.{R}\n")
            break

        prov = _provider(ACTIVE_MODEL)
        col, tag = PROVIDER_LABELS.get(prov, (GEM, prov.title()))
        print(f"\n{col}{BOLD}{tag}{R} {DIM}| {ACTIVE_MODEL}{R}")
        print(_hr("-", DIM))
        response = ask(user_input, api_key)
        print(_colour_wrap(response, R, indent=2))
        print()


if __name__ == "__main__":
    main()
