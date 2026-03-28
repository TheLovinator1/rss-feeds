import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from amd.models import PromotionItem
from amd.models import PromotionsResponse
from main import main as run_main

if TYPE_CHECKING:
    import pytest


def setup_module(module: object) -> None:
    """Backup restock state and dev feed if they exist."""
    for fname in ["pages/data/amd_gaming_keys_restock_state.json", "pages/amd_gaming_promotions_dev.xml"]:
        f = Path(fname)
        if f.exists():
            shutil.copy(f, f.with_suffix(f.suffix + ".bak"))


def teardown_module(module: object) -> None:
    """Restore backups after tests."""
    for fname in ["pages/data/amd_gaming_keys_restock_state.json", "pages/amd_gaming_promotions_dev.xml"]:
        f = Path(fname)
        bak = f.with_suffix(f.suffix + ".bak")
        if bak.exists():
            shutil.move(bak, f)
        elif f.exists():
            f.unlink()


def write_state(state: dict[str, dict[str, int]]) -> None:
    path = Path("pages/data/amd_gaming_keys_restock_state.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f)


def test_no_restock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that no dev feed is written if no restock occurs."""
    # Ensure dev feed file does not exist before test
    dev_feed = Path("pages/amd_gaming_promotions_dev.xml")
    if dev_feed.exists():
        dev_feed.unlink()

    write_state({"promotions": {"test1": 0, "test2": 0}})

    class DummyScraper:
        def fetch_promotions(self, *, save_response: bool = True) -> PromotionsResponse:  # noqa: ARG002
            return PromotionsResponse(
                items=[
                    PromotionItem(
                        id="test1",
                        title="A",
                        slug="a",
                        content="",
                        gameWebsiteUrl="",
                        platform="",
                        developer="",
                        thumbnailImageUrl="",
                        tags="",
                        color="#fff",
                        status="active",
                        featured=False,
                        keysAvailable=0,
                        maxKeysPerIp=1,
                        createdAt=1,
                        updatedAt=1,
                        redemptionInstructions="",
                        consumerId="c",
                        deleted=False,
                    ),
                    PromotionItem(
                        id="test2",
                        title="B",
                        slug="b",
                        content="",
                        gameWebsiteUrl="",
                        platform="",
                        developer="",
                        thumbnailImageUrl="",
                        tags="",
                        color="#fff",
                        status="active",
                        featured=False,
                        keysAvailable=0,
                        maxKeysPerIp=1,
                        createdAt=1,
                        updatedAt=1,
                        redemptionInstructions="",
                        consumerId="c",
                        deleted=False,
                    ),
                ],
            )

    monkeypatch.setattr("main.AMDGamingScraper", DummyScraper)

    class DummyDownloader:
        def download_image(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
            return None

        def get_github_pages_url(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
            return None

    monkeypatch.setattr("main.ImageDownloader", DummyDownloader)
    monkeypatch.setattr("main.append_keys_data_to_csv", lambda *a, **kw: None)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType] # noqa: ARG005
    monkeypatch.setattr("main.RSSFeedGenerator", lambda *a, **kw: type("G", (), {"generate_feed": lambda s, c, d, t: "<rss></rss>"})())  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType] # noqa: ARG005
    run_main()
    dev_feed = Path("pages/amd_gaming_promotions_dev.xml")
    assert not dev_feed.exists() or not dev_feed.read_text(encoding="utf-8")


def test_restock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that dev feed is written if a restock occurs."""
    write_state({"promotions": {"test1": 0, "test2": 0}})

    class DummyScraper:
        def fetch_promotions(self, *, save_response: bool = True) -> PromotionsResponse:  # noqa: ARG002
            return PromotionsResponse(
                items=[
                    PromotionItem(
                        id="test1",
                        title="A",
                        slug="a",
                        content="",
                        gameWebsiteUrl="",
                        platform="",
                        developer="",
                        thumbnailImageUrl="",
                        tags="",
                        color="#fff",
                        status="active",
                        featured=False,
                        keysAvailable=5,
                        maxKeysPerIp=1,
                        createdAt=1,
                        updatedAt=1,
                        redemptionInstructions="",
                        consumerId="c",
                        deleted=False,
                    ),
                    PromotionItem(
                        id="test2",
                        title="B",
                        slug="b",
                        content="",
                        gameWebsiteUrl="",
                        platform="",
                        developer="",
                        thumbnailImageUrl="",
                        tags="",
                        color="#fff",
                        status="active",
                        featured=False,
                        keysAvailable=0,
                        maxKeysPerIp=1,
                        createdAt=1,
                        updatedAt=1,
                        redemptionInstructions="",
                        consumerId="c",
                        deleted=False,
                    ),
                ],
            )

    monkeypatch.setattr("main.AMDGamingScraper", DummyScraper)

    class DummyDownloader:
        def download_image(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
            return None

        def get_github_pages_url(self, *args: object, **kwargs: object) -> None:  # noqa: ARG002
            return None

    monkeypatch.setattr("main.ImageDownloader", DummyDownloader)
    monkeypatch.setattr("main.append_keys_data_to_csv", lambda *a, **kw: None)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType] # noqa: ARG005
    monkeypatch.setattr("main.RSSFeedGenerator", lambda *a, **kw: type("G", (), {"generate_feed": lambda s, c, d, t: "<rss>restocked</rss>"})())  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType] # noqa: ARG005
    run_main()
    dev_feed = Path("pages/amd_gaming_promotions_dev.xml")
    assert dev_feed.exists()
    assert "restocked" in dev_feed.read_text(encoding="utf-8")
