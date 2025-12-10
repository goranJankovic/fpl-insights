import json
import shutil
from textwrap import wrap

# ANSI COLORS
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Terminal width detection
TERM_WIDTH = shutil.get_terminal_size((80, 20)).columns
MAX_WIDTH = min(78, TERM_WIDTH - 2)


def indent_lines(text: str, spaces: int = 6) -> str:
    pad = " " * spaces
    wrapped = wrap(text, MAX_WIDTH - spaces)
    return "\n".join(pad + line for line in wrapped)


def header(title: str) -> str:
    bar = "━" * MAX_WIDTH
    return f"{YELLOW}{bar}\n {title}\n{bar}{RESET}"


def print_pretty_transfer(result: dict):
    """
    Pretty, color-coded, wrapped CLI transfer output.
    """
    if result.get("error"):
        print(f"{RED}[ERROR]{RESET} {result['error']}\n")
        if "raw" in result:
            print("Raw LLM output:\n")
            print(json.dumps(result["raw"], indent=2, ensure_ascii=False))
        return

    data = result["json"]

    gw = data.get("gameweek", "?")
    transfers = data.get("suggested_transfers", [])
    hit_cost = data.get("hit_cost", 0)
    rationale = data.get("rationale", "")

    print(header(f"FPLInsights Transfer Advisor – GW{gw}"))
    print()

    for t in transfers:
        out_name = t.get("out_name", "Unknown")
        in_name = t.get("in_name", "Unknown")
        reason = t.get("reason", "")

        out_team = t.get("out_team", "")
        in_team = t.get("in_team", "")

        out_price = t.get("out_price", None)
        in_price = t.get("in_price", None)

        out_line = f"{RED}  OUT  {RESET}"
        out_line += f"({out_team}) " if out_team else ""
        out_line += f"{out_name}"
        out_line += f" — {out_price}m" if out_price else ""
        print(out_line)

        in_line = f"{GREEN}  IN   {RESET}"
        in_line += f"({in_team}) " if in_team else ""
        in_line += f"{in_name}"
        in_line += f" — {in_price}m" if in_price else ""
        print(in_line)

        if  reason:
            print(indent_lines(reason))
        print()

    print(f"{CYAN}  Hit cost:{RESET} {hit_cost}\n")

    if rationale:
        print(f"{CYAN}  Rationale:{RESET}")
        print(indent_lines(rationale))
        print()

    print(header(""))
