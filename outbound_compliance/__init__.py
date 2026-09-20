"""The CAN-SPAM rules, once, for every engine that sends email.

Pure: no I/O, no clock, no database. Each engine keeps its own storage and its
own send path and reads the rules from here, so the footer wording is identical
by construction rather than by two people remembering to edit two files.

Scope is email only. SMS is not a config change away: TCPA damages are
statutory and uncapped, so a text channel needs per-recipient written consent,
10DLC registration in the sending brand's own entity, opt-out keyword handling,
and counsel review of the program before any code. Each engine enforces that
boundary in its own schema.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

__all__ = [
    "DAILY_SEND_CAP",
    "FOOTER_TEMPLATE",
    "IDENTITY_FIELDS",
    "OPT_OUT",
    "compose",
    "footer",
    "is_opt_out",
    "is_suppressed",
]

# Sends per calendar day, per engine. A deliverability guardrail, independent of
# approval: every send is already approved, and approving eighty in one sitting
# is exactly when the cap earns its keep.
# ponytail: one number for every engine and tenant. Per-tenant caps when a
# tenant's own volume justifies one, not before.
DAILY_SEND_CAP = 25

# 15 U.S.C. 7704(a)(5)(A): the postal address must be inside the message, not
# behind a link, and the opt-out must be usable by reply alone.
FOOTER_TEMPLATE = """\

--
{name} · {title}, {company}
{postal_address}
If you'd rather not hear from me, just reply "unsubscribe" and I won't email again."""

IDENTITY_FIELDS = ("name", "title", "company", "postal_address")

OPT_OUT = re.compile(r"\b(unsubscribe|remove me|opt[ -]?out|stop emailing)\b", re.IGNORECASE)


def footer(identity: Mapping[str, Any]) -> str:
    """The statutory footer. Raises ValueError naming every blank field."""
    blank = [f for f in IDENTITY_FIELDS if not str(identity.get(f) or "").strip()]
    if blank:
        raise ValueError(
            f"sender identity incomplete: {blank}. No email composes without a "
            "complete CAN-SPAM footer."
        )
    return FOOTER_TEMPLATE.format(**{f: identity[f] for f in IDENTITY_FIELDS})


def compose(body: str, identity: Mapping[str, Any]) -> str:
    """Body with the footer appended, or ValueError. There is no third outcome."""
    return body + footer(identity)


def is_opt_out(text: str | None) -> bool:
    """True if a reply asks to stop being contacted."""
    return bool(OPT_OUT.search(text or ""))


def is_suppressed(email: str | None, rows: list[dict[str, Any]]) -> bool:
    """True if the address, or its domain, appears in the suppression rows.

    Rows are `{"kind": "email"|"domain", "value": ...}`. Callers pass their own
    query's output, so each engine keeps its own store.
    ponytail: linear over the rows. Suppression lists are in the hundreds; index
    the query, not this function, if one ever gets large.
    """
    email = (email or "").lower()
    if not email:
        return False
    domain = email.split("@", 1)[1] if "@" in email else ""

    for row in rows:
        value = str(row.get("value") or "").lower()
        if not value:
            continue
        kind = row.get("kind")
        if kind == "email" and value == email:
            return True
        if kind == "domain" and domain and value == domain:
            return True
    return False
