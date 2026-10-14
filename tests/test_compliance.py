"""The four rules that must be identical in every engine that sends email."""

from __future__ import annotations

import pytest
from outbound_compliance import (
    DAILY_SEND_CAP,
    IDENTITY_FIELDS,
    compose,
    footer,
    is_opt_out,
    is_suppressed,
)

IDENTITY = {
    "name": "Alex Smith",
    "title": "Founder",
    "company": "ArctusAI",
    "postal_address": "123 Main St, Austin TX 78701",
}


def test_footer_carries_every_statutory_element() -> None:
    text = footer(IDENTITY)
    for value in IDENTITY.values():
        assert value in text
    assert "unsubscribe" in text.lower()


def test_compose_leaves_the_body_first_and_appends_the_footer() -> None:
    result = compose("Hi Jane,\n\nQuick question.", IDENTITY)
    assert result.startswith("Hi Jane,")
    assert result.endswith(footer(IDENTITY))


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
def test_a_missing_identity_field_refuses_the_send(field: str) -> None:
    missing = {k: v for k, v in IDENTITY.items() if k != field}
    with pytest.raises(ValueError, match=field):
        compose("body", missing)


@pytest.mark.parametrize("field", IDENTITY_FIELDS)
def test_a_blank_identity_field_refuses_the_send(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        compose("body", {**IDENTITY, field: "   "})


ROWS = [
    {"kind": "email", "value": "jane@acme.com"},
    {"kind": "domain", "value": "blocked.com"},
]


def test_suppression_matches_email_and_domain_case_insensitively() -> None:
    assert is_suppressed("Jane@ACME.COM", ROWS) is True
    assert is_suppressed("anyone@BLOCKED.com", ROWS) is True
    assert is_suppressed("bob@acme.com", ROWS) is False
    assert is_suppressed("anyone@notblocked.com", ROWS) is False


def test_suppression_survives_junk_input() -> None:
    assert is_suppressed("", ROWS) is False
    assert is_suppressed(None, ROWS) is False
    assert is_suppressed("jane@acme.com", [{"kind": "domain"}]) is False


@pytest.mark.parametrize(
    "text",
    ["please unsubscribe me", "REMOVE ME from this list", "opt-out", "opt out",
     "stop emailing me", "Unsubscribe.",
     # The ten opt-outs from sales-engine's Laya spike (docs/spikes/laya/); v0.1.0 missed seven.
     "Please remove me from your list.", "Unsubscribe", "Stop emailing me.",
     "Not interested. Please don't contact me again.",
     "Take me off whatever list this is. We don't buy from cold outreach.",
     "This is the third message. If I get another one I'm reporting it as spam.",
     "No thanks, and please do not follow up.", "I never signed up for this. Remove my address.",
     "Hi, appreciate the effort, but please stop reaching out. Best of luck.", "STOP",
     "stop.", "Don’t email me again"],
)
def test_opt_out_phrases_are_recognised(text: str) -> None:
    assert is_opt_out(text) is True


@pytest.mark.parametrize(
    "text",
    ["sure, let's talk", "", "I'd like to stop by your office", "unsubscribed him already?",
     "Can you call me tomorrow at 10?", "Too busy this month. Ping me after the holidays.",
     "Thanks. Not looking at anything like this at the moment.",
     "We just signed a two-year contract with another vendor, so not for now.",
     "Stop by the front desk when you visit.", "Let me think about it and get back to you."],
)
def test_ordinary_replies_are_not_opt_outs(text: str) -> None:
    assert is_opt_out(text) is False


def test_the_cap_is_a_number_both_engines_read_rather_than_define() -> None:
    assert DAILY_SEND_CAP == 25


def test_an_account_domain_suppresses_a_contact_whose_address_is_elsewhere() -> None:
    assert is_suppressed("dana@gmail.com", ROWS, domain="blocked.com") is True
    assert is_suppressed("dana@gmail.com", ROWS, domain="allowed.com") is False
    assert is_suppressed(None, ROWS, domain="BLOCKED.com") is True
