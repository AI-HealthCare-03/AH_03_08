"""3-4 피드백 수집·조회 API 실측 검증.

Usage:
  $env:EVAL_EMAIL="jimin_medilog@example.com"
  $env:EVAL_PASSWORD="Password123!"
  uv run python scripts/eval_3_4_feedback_flow.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_guide_common import login_admin_client, login_client  # noqa: E402


async def main_async(args: argparse.Namespace) -> int:
    executed_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    client, headers = await login_client()

    # 가이드 ID 확보
    r = await client.get("/guides", headers=headers, params={"page": 1, "limit": 1})
    r.raise_for_status()
    data = r.json().get("data") or {}
    items = data.get("items") or []
    if not items:
        print("ERROR: no guides — create one first")
        await client.aclose()
        return 1
    guide_id = str(items[0].get("id") or items[0].get("guide_id"))

    tag_id = f"negative_1_{uuid.uuid4().hex[:6]}"
    payload = {
        "guide_id": guide_id,
        "rating": 0,
        "tag_ids": [tag_id],
        "comment": "eval_3_4_feedback_flow test",
    }
    post = await client.post("/guides/feedbacks", headers=headers, json=payload)
    list_r = await client.get("/guides/feedbacks/list", headers=headers)

    post_ok = post.status_code in (200, 201)
    list_ok = list_r.status_code == 200
    list_body = list_r.json() if list_ok else {}
    list_items = (list_body.get("data") or {}).get("items") or list_body.get("data") or []
    if isinstance(list_items, dict):
        list_items = list_items.get("items") or []
    found = any(
        str(it.get("guide_id")) == guide_id and it.get("comment") == payload["comment"]
        for it in (list_items if isinstance(list_items, list) else [])
    )

    admin_ok = False
    admin_status = None
    if post_ok:
        admin_client, admin_headers = await login_admin_client()
        try:
            admin_r = await admin_client.get(
                "/admin/feedbacks", headers=admin_headers, params={"page": 1, "limit": 20}
            )
            admin_status = admin_r.status_code
            admin_ok = admin_r.status_code == 200
        finally:
            await admin_client.aclose()

    result = {
        "executed_at": executed_at,
        "guide_id": guide_id,
        "post_status": post.status_code,
        "post_ok": post_ok,
        "list_status": list_r.status_code,
        "list_ok": list_ok,
        "feedback_found_in_list": found,
        "admin_status": admin_status,
        "admin_ok": admin_ok,
        "pass": post_ok and list_ok and found and admin_ok,
    }

    out_json = Path(args.output)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = out_json.with_suffix(".md")
    md_path.write_text(
        "\n".join(
            [
                "# MediLog 8조 — 3-4 피드백 API 실측",
                "",
                f"| 실행 일시 | {executed_at} |",
                f"| POST /guides/feedbacks | {post.status_code} ({'OK' if post_ok else 'FAIL'}) |",
                f"| GET /guides/feedbacks/list | {list_r.status_code} ({'OK' if list_ok else 'FAIL'}) |",
                f"| 목록에서 피드백 확인 | {'PASS' if found else 'FAIL'} |",
                f"| GET /admin/feedbacks | {admin_status} ({'OK' if admin_ok else 'FAIL'}) |",
                f"| **종합** | **{'PASS' if result['pass'] else 'FAIL'}** |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    await client.aclose()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"wrote {out_json}")
    print(f"wrote {md_path}")
    return 0 if result["pass"] else 1


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="docs/evaluation/reports/3-4-feedback-verify.json")
    raise SystemExit(asyncio.run(main_async(p.parse_args())))


if __name__ == "__main__":
    main()
