"""Runnable example for a storefront-shaped game content workflow."""
from pathlib import Path

from game_backend import AssetStore, GameAssetService, PlayerAssetRequest


def main() -> None:
    service = GameAssetService(AssetStore(Path(".game-data")))
    asset = service.create_asset(
        PlayerAssetRequest(
            player_id="player-42",
            asset_id="player-42-banner",
            prompt="A bright banner for a cooperative sky-island game, no text",
        )
    )
    print(f"queued {asset.asset_id}: {asset.status}")
    published = service.review_asset(asset.asset_id, approved=True)
    print(f"reviewed {published.asset_id}: {published.status}")


if __name__ == "__main__":
    main()
