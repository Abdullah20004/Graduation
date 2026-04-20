"""
HackOps Tools Registry
======================
Defines ALL security tools in the system and access-control rules:
  - AI-only tools  (never exposed to the human player)
  - User tools     (difficulty-gated)
  - Shared tools   (role-gated, optionally difficulty-gated)

Difficulty encoding:  'easy' > 'medium' > 'hard'
Role encoding:        'red'  = attacker  |  'blue' = defender

Usage
-----
from tools_registry import ToolsRegistry

# Get the tools a human attacker can use at medium difficulty
available = ToolsRegistry.get_available_tools(role='red', difficulty='medium')

# Check a specific call is allowed before executing
allowed, reason = ToolsRegistry.check_tool_access('sqli_scanner', role='red', difficulty='hard')
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Difficulty ordering (lower index = easier = more tools)
# ---------------------------------------------------------------------------
DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']


def _difficulty_index(d: str) -> int:
    """Return the position of a difficulty in the ordering (0 = easiest)."""
    try:
        return DIFFICULTY_LEVELS.index(d.lower())
    except ValueError:
        return 0  # Unknown difficulties default to easiest (most permissive)


# ---------------------------------------------------------------------------
# Tool catalog
# ---------------------------------------------------------------------------
#
# Each entry describes one tool that can appear in the system.
# Fields:
#   id          : unique snake_case identifier used in API calls
#   name        : human-friendly label shown in the UI
#   description : one-line summary shown in the UI
#   category    : 'ai_only' | 'user' | 'shared'
#   roles       : list of roles that can use this tool ('red', 'blue', 'any')
#   max_difficulty: the HARDEST difficulty at which this tool is available.
#                   e.g. 'medium' means it works on easy + medium but NOT hard.
#                   None means available at all difficulties.
#   icon        : emoji used in the UI for quick recognition
#   endpoint    : the API route relative to /api/tools/ (or None for AI-only)
#

TOOL_CATALOG: list[dict] = [

    # ------------------------------------------------------------------ AI-only
    {
        "id": "ai_port_scan",
        "name": "Port & Service Scan",
        "description": "Reconnaissance scan to discover open services and versions.",
        "category": "ai_only",
        "roles": ["red"],
        "max_difficulty": None,
        "icon": "📡",
        "endpoint": None,
    },
    {
        "id": "ai_dir_discovery",
        "name": "Directory Discovery",
        "description": "Brute-force discovery of hidden pages and endpoints.",
        "category": "ai_only",
        "roles": ["red"],
        "max_difficulty": None,
        "icon": "📂",
        "endpoint": None,
    },
    {
        "id": "ai_auto_sqli",
        "name": "Auto SQL Injection",
        "description": "Automated SQLi exploitation across all parameters.",
        "category": "ai_only",
        "roles": ["red"],
        "max_difficulty": None,
        "icon": "💉",
        "endpoint": None,
    },
    {
        "id": "ai_auto_xss",
        "name": "Auto XSS Exploit",
        "description": "Automated XSS probing across reflected and stored vectors.",
        "category": "ai_only",
        "roles": ["red"],
        "max_difficulty": None,
        "icon": "⚡",
        "endpoint": None,
    },
    {
        "id": "ai_auto_patch",
        "name": "Auto Patch",
        "description": "Automatically identify and apply security patches.",
        "category": "ai_only",
        "roles": ["blue"],
        "max_difficulty": None,
        "icon": "🛡️",
        "endpoint": None,
    },

    # ------------------------------------------------------------------ User tools (difficulty-gated)
    {
        "id": "sqli_scanner",
        "name": "SQL Injection Scanner",
        "description": "Automatically scan a page for SQL injection vulnerabilities.",
        "category": "user",
        "roles": ["red", "any"],
        "max_difficulty": "easy",   # Easy only
        "icon": "🔍",
        "endpoint": "sqlmap/scan",
    },
    {
        "id": "xss_scanner",
        "name": "XSS Scanner",
        "description": "Automatically scan a page for reflected and stored XSS.",
        "category": "user",
        "roles": ["red", "any"],
        "max_difficulty": "easy",   # Easy only
        "icon": "🕷️",
        "endpoint": "xss/scan",
    },
    {
        "id": "vuln_hint",
        "name": "Vulnerability Hint",
        "description": "Reveals the vulnerability type present on a page (not the payload).",
        "category": "user",
        "roles": ["red", "any"],
        "max_difficulty": "medium",  # Easy + Medium
        "icon": "💡",
        "endpoint": "hint",
    },
    {
        "id": "page_hint",
        "name": "Page Security Hint",
        "description": "Highlights which input fields on a page are worth investigating.",
        "category": "user",
        "roles": ["red", "any"],
        "max_difficulty": "easy",   # Easy only
        "icon": "🗺️",
        "endpoint": "page-hint",
    },

    # ------------------------------------------------------------------ Shared tools (role + difficulty gated)
    {
        "id": "semgrep_sast",
        "name": "Semgrep SAST",
        "description": "Static analysis of PHP source code to spot security issues.",
        "category": "shared",
        "roles": ["blue"],
        "max_difficulty": "medium",  # Easy + Medium defenders only
        "icon": "🔬",
        "endpoint": "semgrep/scan",
    },
    {
        "id": "zap_scanner",
        "name": "OWASP ZAP Scanner",
        "description": "Full web application active scanner (spider + active scan).",
        "category": "shared",
        "roles": ["blue"],
        "max_difficulty": "easy",   # Easy defenders only
        "icon": "🌐",
        "endpoint": "zap/scan",
    },
    {
        "id": "http_inspector",
        "name": "HTTP Inspector",
        "description": "View the raw HTTP request and response for any DVWA page.",
        "category": "shared",
        "roles": ["red", "blue", "any"],
        "max_difficulty": None,     # Always available to everyone
        "icon": "🔭",
        "endpoint": "http-inspect",
    },
]

# Pre-built lookups
_CATALOG_BY_ID: dict[str, dict] = {t["id"]: t for t in TOOL_CATALOG}
AI_TOOL_IDS: set[str] = {t["id"] for t in TOOL_CATALOG if t["category"] == "ai_only"}


# ---------------------------------------------------------------------------
# Main registry class
# ---------------------------------------------------------------------------

class ToolsRegistry:
    """Stateless helper that evaluates tool access based on role & difficulty."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def get_available_tools(role: str, difficulty: str) -> list[dict]:
        """
        Return the list of tools available to a *human* player with the given
        role and difficulty.  AI-only tools are never included.

        Parameters
        ----------
        role       : 'red' | 'blue'
        difficulty : 'easy' | 'medium' | 'hard'

        Returns
        -------
        List of tool dicts (subset of TOOL_CATALOG) with an extra
        ``available`` key set to True (always True for returned items).
        """
        result = []
        for tool in TOOL_CATALOG:
            if tool["category"] == "ai_only":
                continue  # Never expose AI tools to humans
            allowed, _ = ToolsRegistry.check_tool_access(
                tool["id"], role=role, difficulty=difficulty
            )
            if allowed:
                result.append({**tool, "available": True})
        return result

    @staticmethod
    def get_all_tools_with_status(role: str, difficulty: str) -> list[dict]:
        """
        Like get_available_tools but returns ALL non-AI tools with an
        ``available`` flag so the UI can render locked tools greyed-out.
        """
        result = []
        for tool in TOOL_CATALOG:
            if tool["category"] == "ai_only":
                continue
            allowed, reason = ToolsRegistry.check_tool_access(
                tool["id"], role=role, difficulty=difficulty
            )
            result.append({**tool, "available": allowed, "locked_reason": "" if allowed else reason})
        return result

    @staticmethod
    def check_tool_access(tool_id: str, role: str, difficulty: str) -> tuple[bool, str]:
        """
        Check whether a given tool can be used by a human player.

        Parameters
        ----------
        tool_id    : the tool's id string
        role       : 'red' | 'blue'
        difficulty : 'easy' | 'medium' | 'hard'

        Returns
        -------
        (allowed: bool, reason: str)
            allowed=True  → tool access granted
            allowed=False → reason explains why access is denied
        """
        tool = _CATALOG_BY_ID.get(tool_id)
        if not tool:
            return False, f"Unknown tool: {tool_id}"

        # AI-only tools are never available to humans
        if tool["category"] == "ai_only":
            return False, "This tool is reserved for AI agents only."

        # Role check
        tool_roles = tool.get("roles", ["any"])
        if "any" not in tool_roles and role not in tool_roles:
            role_label = "attackers (red team)" if role == "red" else "defenders (blue team)"
            return False, f"This tool is only available to {'defenders (blue team)' if 'blue' in tool_roles else 'attackers (red team)'}."

        # Difficulty check
        max_difficulty = tool.get("max_difficulty")
        if max_difficulty is not None:
            req_idx = _difficulty_index(max_difficulty)
            cur_idx = _difficulty_index(difficulty)
            if cur_idx > req_idx:
                return False, (
                    f"This tool is not available on {difficulty.capitalize()} difficulty. "
                    f"It requires {max_difficulty.capitalize()} difficulty or easier."
                )

        return True, ""

    @staticmethod
    def get_ai_tools(role: str) -> list[dict]:
        """Return the AI-only tools for the given agent role."""
        return [t for t in TOOL_CATALOG if t["category"] == "ai_only" and
                ("any" in t["roles"] or role in t["roles"])]

    @staticmethod
    def get_tool_info(tool_id: str) -> dict | None:
        """Return raw tool definition by ID, or None if not found."""
        return _CATALOG_BY_ID.get(tool_id)

    @staticmethod
    def difficulty_label(difficulty: str) -> str:
        """Return a human-readable description of what the difficulty means tool-wise."""
        labels = {
            "easy": "Easy — All scanners, hints, and ZAP available. Great for learning.",
            "medium": "Medium — SQLi scanner and vuln type hints only. XSS must be done manually.",
            "hard": "Hard — No scanners or hints. Pure manual exploitation. AI uses full toolset.",
        }
        return labels.get(difficulty.lower(), "Unknown difficulty.")
