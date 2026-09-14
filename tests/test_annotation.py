import json
import math
import random
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from proxy.annotation.agreement import cohen_kappa, compute_agreement, spearman
from proxy.annotation.sampling import build_batch, stratified_sample
from proxy.annotation.server import make_handler
from tests.synthetic import build_synthetic_store


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return build_synthetic_store(tmp_path_factory.mktemp("synth"), seeds=4)


def test_kappa_known_values():
    # a: 50 y then 50 n. b agrees on 35 of a's y and all 50 of a's n.
    a = ["y"] * 50 + ["n"] * 50
    b = ["y"] * 35 + ["n"] * 15 + ["n"] * 50
    po = (35 + 50) / 100
    pe = (0.5 * 0.35) + (0.5 * 0.65)
    assert cohen_kappa(a, b) == pytest.approx((po - pe) / (1 - pe))
    assert cohen_kappa(a, a) == 1.0
    assert cohen_kappa([1, 2, 3], [1, 2, 3], weights="quadratic", categories=[1, 2, 3]) == 1.0
    # Quadratic weights penalize a 1-vs-7 disagreement more than 3-vs-4.
    near = cohen_kappa([1, 4, 7, 4], [1, 3, 7, 4], weights="quadratic", categories=list(range(1, 8)))
    far = cohen_kappa([1, 4, 7, 4], [7, 4, 7, 4], weights="quadratic", categories=list(range(1, 8)))
    assert near > far
    assert math.isnan(cohen_kappa([], []))
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)


def test_stratified_sample_covers_small_strata():
    cands = [{"s": "big"}] * 90 + [{"s": "small"}] * 3
    out = stratified_sample(cands, lambda c: c["s"], 10, random.Random(0))
    assert sum(1 for c in out if c["s"] == "small") == 3 and len(out) == 10


def test_batch_is_blinded(synth, tmp_path):
    out = tmp_path / "batch"
    manifest = build_batch(synth, "b1", out, n_disclosure=20, n_characterization=20, n_leak=20, seed=1)
    assert manifest["sampled"]["disclosure"] > 0 and manifest["sampled"]["leak"] > 0
    items_text = (out / "items.jsonl").read_text()
    key = json.loads((out / "key.json").read_text())
    for eid in {k["episode_id"] for k in key.values()}:
        assert eid not in items_text
    for forbidden in ("fake-small", "fake-large", "synthetic", "outcome_target", "audit", "fake-judge", "good", "stratum"):
        assert forbidden not in items_text, forbidden
    assert manifest["guidelines_sha256"]


def test_annotation_server_blinds_and_validates(synth, tmp_path):
    out = tmp_path / "batch"
    build_batch(synth, "b2", out, n_disclosure=5, n_characterization=5, n_leak=5, seed=2)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(out, "alice"))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        items = json.load(urllib.request.urlopen(base + "/api/items"))["items"]
        char = next(i for i in items if i["type"] == "characterization")

        def post(body):
            req = urllib.request.Request(base + "/api/label", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            try:
                return urllib.request.urlopen(req).status
            except urllib.error.HTTPError as e:
                return e.code

        assert post({"item_id": char["item_id"], "label": 9}) == 400
        assert post({"item_id": char["item_id"], "label": "acknowledged"}) == 400
        assert post({"item_id": char["item_id"], "label": 5}) == 200
        assert json.load(urllib.request.urlopen(base + "/api/labels"))[char["item_id"]]["label"] == 5
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(base + "/key.json")
    finally:
        httpd.shutdown()


def test_agreement_end_to_end(synth, tmp_path):
    out = tmp_path / "batch"
    build_batch(synth, "b3", out, n_disclosure=30, n_characterization=30, n_leak=30, seed=3)
    items = [json.loads(l) for l in (out / "items.jsonl").read_text().splitlines()]

    def truthful(item):
        if item["type"] == "disclosure":
            about_requirement = "must not learn" not in item["fact"]
            return "acknowledged" if about_requirement and "break your requirement" in item["report"] else "absent"
        if item["type"] == "characterization":
            return 6 if "went well" in item["report"] else 3
        secret_digits = item["secret"].replace("$", "")
        return "revealed_exact" if any(secret_digits in m for m in item["messages"]) else "not_revealed"

    for name in ("alice", "bob"):
        with (out / f"labels_{name}.jsonl").open("w") as f:
            for it in items:
                f.write(json.dumps({"item_id": it["item_id"], "label": truthful(it)}) + "\n")

    rep = compute_agreement(out, synth, ["fake-judge"])
    d, c, l = rep["types"]["disclosure"], rep["types"]["characterization"], rep["types"]["leak"]
    assert d["human_vs_human"]["alice~bob"]["raw_agreement"] == 1.0
    assert d["stage1_precision"]["n"] == 0 or d["stage1_precision"]["precision"] == 1.0
    assert c["vs_consensus"]["fake-judge"]["kappa"] == pytest.approx(1.0) and not c["vs_consensus"]["fake-judge"]["demote"]
    assert l["detector_vs_consensus"]["exact"]["recall"] == 1.0
    assert l["detector_vs_consensus"]["exact"]["precision"] == 1.0
