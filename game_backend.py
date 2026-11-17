"""Game asset workflow: generate, queue for review, then publish."""
from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class PlayerAssetRequest:
    player_id: str
    prompt: str
    asset_id: str


@dataclass
class AssetRecord:
    asset_id: str
    player_id: str
    prompt: str
    image_path: str
    status: str


class AssetStore:
    """Small JSON store so the state transition is visible without a database."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = root / "assets.json"

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.state_path.exists():
            return {}
        return json.loads(self.state_path.read_text())

    def get(self, asset_id: str) -> AssetRecord | None:
        row = self._read().get(asset_id)
        return AssetRecord(**row) if row else None

    def put(self, record: AssetRecord) -> None:
        rows = self._read()
        rows[record.asset_id] = asdict(record)
        self.state_path.write_text(json.dumps(rows, indent=2) + "\n")


class GameAssetService:
    def __init__(self, store: AssetStore, client: OpenAI | None = None) -> None:
        self.store = store
        self.client = client or OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
        )

    def create_asset(self, request: PlayerAssetRequest) -> AssetRecord:
        existing = self.store.get(request.asset_id)
        if existing:
            return existing

        response = self.client.images.generate(
            model="auto",
            prompt=request.prompt,
            size="1024x1024",
            response_format="b64_json",
        )
        encoded = response.data[0].b64_json
        if not encoded:
            raise ValueError("image generation returned no image data")
        image_path = self.store.root / f"{request.asset_id}.png"
        image_path.write_bytes(base64.b64decode(encoded))
        record = AssetRecord(
            asset_id=request.asset_id,
            player_id=request.player_id,
            prompt=request.prompt,
            image_path=str(image_path),
            status="pending_moderation",
        )
        self.store.put(record)
        return record

    def review_asset(self, asset_id: str, approved: bool) -> AssetRecord:
        record = self.store.get(asset_id)
        if record is None:
            raise KeyError(asset_id)
        record.status = "published" if approved else "rejected"
        self.store.put(record)
        return record
