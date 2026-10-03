"""Owner-approved ceiling amendment for ``psv3-r1``: the frozen collector, run with a new ceiling.

Gateway errors that report no charge keep their $5 reservation in the frozen accounting for the
rest of the run. The owner raised the cumulative ceiling to absorb those holds. Nothing frozen
changes: ``collect.verify`` still checks every bound input, and ``collect.collect_loop`` runs
unchanged with the amended ceiling, which is recorded once in ``ceiling_amendment.json``.
"""

from __future__ import annotations

import signal

from latent_art_bench.painter_specificity_v1.workflow import now
from latent_art_bench.painter_specificity_v3 import collect
from latent_art_bench.painter_specificity_v3 import study as s

RECORD = s.DATA / "ceiling_amendment.json"


def record(ceiling_usd: float, approval: str, reason: str) -> dict:
    frozen = collect.verify()
    if ceiling_usd <= frozen["ceiling_usd"]:
        raise ValueError("an amendment may only raise the frozen ceiling")
    events = s.rows(s.DATA / "attempts.jsonl")
    held = [e["id"] for e in events if e["kind"] == "end" and e["cost_usd"] is None]
    value = dict(created_at=now(), run_id=s.RUN, frozen_ceiling_usd=frozen["ceiling_usd"],
                 ceiling_usd=float(ceiling_usd), approval=approval, reason=reason,
                 accounted_usd_at_amendment=s.accounted(events, frozen["baseline_usd"]),
                 unknown_charge_holds=held, freeze_sha256=s.sha(s.DATA / "freeze.json"))
    s.write_new(RECORD, value)
    return value


def collect_amended() -> None:
    frozen = collect.verify()
    amendment = s.read(RECORD)
    if amendment["freeze_sha256"] != s.sha(s.DATA / "freeze.json"):
        raise ValueError("amendment belongs to a different freeze")
    if (s.DATA / "collection.json").exists():
        raise ValueError("terminal collection cannot restart")
    lock = s.WORK / "collector.lock"
    with lock.open("x") as stream:
        stream.write(now())
    stopped: list[str] = []
    previous = signal.signal(signal.SIGINT, lambda *_: stopped.append("operator pause"))
    try:
        collect.collect_loop(stopped, frozen["baseline_usd"], amendment["ceiling_usd"])
    finally:
        signal.signal(signal.SIGINT, previous)
        lock.unlink()
