"""Prepare one host-wide review file and validate its evidence before scoring."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import run_matrix
import score


def evaluations(record: dict) -> list[tuple[dict, str]]:
    return [
        (score.read_json(p), score.object_id(p.read_bytes()))
        for p in sorted(run_matrix.eval_directory(record["session"]).glob("SR-*.json"))
        if score.read_json(p)["session"] == record["session"]
    ]


def identity(record: dict, results: Path) -> tuple[str, dict]:
    evals = evaluations(record)
    files = score.finished_files(record, results)
    _, digest = score.rubric_evidence(record, evals, files)
    state = record.get("rubricReview", {})
    keys = {
        f"{e['rule']}:{i}"
        for e, _ in evals
        for i, a in enumerate(e["assertions"], 1)
        if a["kind"] == "rubric"
    }
    if not keys:
        return digest, {}
    if state.get("evidenceSha256") != digest or set(state.get("verdicts", {})) != keys:
        raise score.RecordError(
            "missing or stale model judgments: " + record["session"]
        )
    verdicts = {
        k: {field: v[field] for field in ("verdict", "judge", "reason")}
        for k, v in state["verdicts"].items()
    }
    if any(
        not score.valid_decision(v, tested_model=record["model"])
        for v in verdicts.values()
    ):
        raise score.RecordError("invalid model judgment")
    return digest, verdicts


def latest_paths(results: Path) -> list[Path]:
    paths = []
    for host in run_matrix.HOSTS:
        names = {
            s["name"]
            for root in run_matrix.groups(host)
            for _, s in run_matrix.runner.sessions_for(root)
        }
        for name in sorted(names):
            candidates = list((results / host / name).glob("*.json"))
            if not candidates:
                raise score.RecordError(f"missing record: {host}/{name}")
            paths.append(max(candidates, key=lambda p: int(p.stem)))
    return paths


def catalog(results: Path) -> dict:
    data = {}
    for path in latest_paths(results):
        record = score.read_json(path)
        if record.get("notRun") or record.get("brokenAt"):
            raise score.RecordError(
                "incomplete session: " + str(path.relative_to(results))
            )
        digest, verdicts = identity(record, results)
        data[path.relative_to(results).as_posix()] = {
            "host": record["host"],
            "evidenceSha256": digest,
            "verdicts": verdicts,
        }
    return data


def selection(data: dict, previous: dict | None = None) -> dict:
    digest = score.evidence_digest(data)
    if previous:
        if previous.get("evidenceSha256") != digest:
            raise score.RecordError(
                "review batch evidence changed; prepare a new review file"
            )
        return previous
    samples = {}
    for host in run_matrix.HOSTS:
        passes = [
            f"{path}#{key}"
            for path, item in data.items()
            if item["host"] == host
            for key, v in item["verdicts"].items()
            if v["verdict"] == "PASS"
        ]
        samples[host] = sorted(
            random.SystemRandom().sample(passes, min(10, len(passes)))
        )
    return {
        "policy": "host-ten-v1",
        "evidenceSha256": digest,
        "records": data,
        "samples": samples,
        "verdicts": {},
    }


def required(batch: dict, host: str) -> tuple[set[str], bool]:
    data = batch["records"]
    all_keys = {
        f"{path}#{key}": v
        for path, item in data.items()
        if item["host"] == host
        for key, v in item["verdicts"].items()
    }
    passes = {k for k, v in all_keys.items() if v["verdict"] == "PASS"}
    sample = batch["samples"][host]
    if (
        len(sample) != min(10, len(passes))
        or len(set(sample)) != len(sample)
        or not set(sample) <= passes
    ):
        raise score.RecordError("invalid host-wide sample")
    reviews = batch["verdicts"]
    for key, review in reviews.items():
        if key in all_keys and not score.valid_decision(review, human=True):
            raise score.RecordError("invalid human review")
    wrong = sum(
        k in reviews and reviews[k]["verdict"] != all_keys[k]["verdict"] for k in sample
    )
    manual_all = 10 * wrong > len(sample)
    keys = (
        set(all_keys)
        if manual_all
        else set(sample) | {k for k, v in all_keys.items() if v["verdict"] == "FAIL"}
    )
    return keys, manual_all


def for_record(record: dict, results: Path, filename: str) -> dict:
    path = results / score.safe_path(filename)
    if not path.resolve().is_relative_to(results.resolve()):
        raise score.RecordError("review file leaves results root")
    batch = score.read_json(path)
    data = catalog(results)
    if (
        batch.get("policy") != "host-ten-v1"
        or batch.get("evidenceSha256") != score.evidence_digest(data)
        or batch.get("records") != data
    ):
        raise score.RecordError("stale batch review")
    digest, _ = identity(record, results)
    matches = [
        p
        for p, item in data.items()
        if item["host"] == record["host"] and item["evidenceSha256"] == digest
    ]
    if len(matches) != 1:
        raise score.RecordError("record absent or ambiguous in review batch")
    prefix = matches[0] + "#"
    keys, manual_all = required(batch, record["host"])
    all_keys = {f"{p}#{k}" for p, item in data.items() for k in item["verdicts"]}
    if not set(batch["verdicts"]) <= all_keys:
        raise score.RecordError("unknown human verdict key")
    # Every record remains pending until the whole host's required review is complete.
    complete = keys <= batch["verdicts"].keys()
    local = [k.removeprefix(prefix) for k in keys if k.startswith(prefix)]
    if not complete:
        local = sorted(data[matches[0]]["verdicts"])
    return {
        "evidenceSha256": digest,
        "batchFile": filename,
        "sample": [
            k.removeprefix(prefix)
            for k in batch["samples"][record["host"]]
            if k.startswith(prefix)
        ],
        "manualAll": manual_all,
        "required": local,
        "verdicts": {
            k.removeprefix(prefix): v
            for k, v in batch["verdicts"].items()
            if k.startswith(prefix)
        },
        "complete": complete,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=score.EVALS / "results")
    parser.add_argument("--review-file", default="review.json")
    parser.add_argument("--judge-model")
    args = parser.parse_args(argv)
    try:
        paths = latest_paths(args.results)
        for path in paths:
            record = score.read_json(path)
            score.score_record(
                record,
                run_matrix.eval_directory(record["session"]),
                results=args.results,
                judge_model=args.judge_model,
            )
            score.write_json(path, record)
        path = args.results / score.safe_path(args.review_file)
        batch = selection(
            catalog(args.results), score.read_json(path) if path.exists() else None
        )
        batch["batchFile"] = args.review_file
        batch["instructions"] = (
            "Read each required record and its eval rubric. Add each required key under verdicts with verdict PASS or FAIL, judge human:developer, and a nonempty reason. Never edit the catalog or samples."
        )
        batch["required"] = sorted(
            {key for host in run_matrix.HOSTS for key in required(batch, host)[0]}
        )
        score.write_json(path, batch)
        print(
            f"{path}: {len(batch['required'])} human verdicts required; add decisions under verdicts"
        )
        code = 0
        for record_path in paths:
            record = score.read_json(record_path)
            code = max(
                code,
                score.score_record(
                    record,
                    run_matrix.eval_directory(record["session"]),
                    results=args.results,
                    reviews={"batchFile": args.review_file},
                ),
            )
            score.write_json(record_path, record)
        return code
    except (OSError, ValueError, score.RecordError) as error:
        print(f"review: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
