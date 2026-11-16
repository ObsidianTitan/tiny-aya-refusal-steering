#!/usr/bin/env python3
"""Standalone upload of the prepared folders. DISABLED BY DEFAULT.
Run only after the user's explicit go-ahead:
    HF_WRITE_TOKEN=... python upload_to_hf.py --publish --user <hf_username> --dir /content/lexsi_run [--include-vector]
Without --publish it only prints what it would do. Never prints the token."""
import argparse, os, sys
ap = argparse.ArgumentParser()
ap.add_argument("--publish", action="store_true", help="actually create repos and upload (default: dry run)")
ap.add_argument("--user", required=True); ap.add_argument("--dir", default="/content/lexsi_run")
ap.add_argument("--include-vector", action="store_true", help="also upload the refusal vector (dual use; default off)")
a = ap.parse_args()
DATASET_REPO = f"{a.user}/tiny-aya-refusal-steering-eval"; MODEL_REPO = f"{a.user}/tiny-aya-refusal-steering-config"
PUB, PUB_MODEL = f"{a.dir}/public_dataset", f"{a.dir}/public_model"
for d in (PUB, PUB_MODEL):
    assert os.path.exists(f"{d}/MANIFEST.sha256"), f"{d} not prepared (run the notebook through cell 14)"
vec = f"{PUB_MODEL}/refusal_direction.pt"
if os.path.exists(vec) and not a.include_vector:
    sys.exit("refusal_direction.pt is in the model folder but --include-vector was not given; remove it or pass the flag")
plan = [("create public dataset repo", DATASET_REPO), ("upload", PUB), ("create public model repo", MODEL_REPO),
        ("upload", PUB_MODEL), ("create public collection", "models (eval-only)"), ("create public collection", "data and logs")]
if not a.publish:
    for p in plan: print("DRY RUN:", *p)
    sys.exit(0)
from huggingface_hub import HfApi
tok = os.environ.get("HF_WRITE_TOKEN"); assert tok, "set HF_WRITE_TOKEN"
api = HfApi(token=tok); del tok
api.create_repo(DATASET_REPO, repo_type="dataset", private=False, exist_ok=True)
api.upload_folder(repo_id=DATASET_REPO, repo_type="dataset", folder_path=PUB, commit_message="Lexsi Track 2 Stage 1 eval pack")
api.create_repo(MODEL_REPO, repo_type="model", private=False, exist_ok=True)
api.upload_folder(repo_id=MODEL_REPO, repo_type="model", folder_path=PUB_MODEL, commit_message="Eval-only card, no weights")
cm = api.create_collection(title="Tiny Aya refusal steering: models (eval-only)", namespace=a.user, private=False, exists_ok=True)
api.add_collection_item(cm.slug, item_id="CohereLabs/tiny-aya-global", item_type="model", note="base model, revision af89d219b53e", exists_ok=True)
api.add_collection_item(cm.slug, item_id=MODEL_REPO, item_type="model", note="eval-only card", exists_ok=True)
cd = api.create_collection(title="Tiny Aya refusal steering: data and logs", namespace=a.user, private=False, exists_ok=True)
api.add_collection_item(cd.slug, item_id=DATASET_REPO, item_type="dataset", exists_ok=True)
print(f"https://huggingface.co/datasets/{DATASET_REPO}\nhttps://huggingface.co/{MODEL_REPO}")
print(f"https://huggingface.co/collections/{cm.slug}\nhttps://huggingface.co/collections/{cd.slug}")
print("Check every URL logged out, from your Mac, before submitting.")
