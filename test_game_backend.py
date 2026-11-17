from pathlib import Path

from game_backend import AssetStore, AssetRecord, GameAssetService


def test_approval_is_the_only_path_to_published(tmp_path: Path) -> None:
    store = AssetStore(tmp_path)
    store.put(AssetRecord("a1", "p1", "banner", str(tmp_path / "a1.png"), "pending_moderation"))
    service = GameAssetService(store, client=object())

    pending = store.get("a1")
    assert pending is not None
    assert pending.status == "pending_moderation"
    assert service.review_asset("a1", approved=False).status == "rejected"
    assert service.review_asset("a1", approved=True).status == "published"
