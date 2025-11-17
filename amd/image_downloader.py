"""Image downloader utility for AMD Gaming promotions."""

from pathlib import Path
from urllib.parse import ParseResult
from urllib.parse import urlparse

from curl_cffi import requests
from loguru import logger


class ImageDownloader:
    """Download and cache promotion images to serve from GitHub Pages."""

    def __init__(self, output_dir: Path = Path("pages/images")) -> None:
        """Initialize the image downloader.

        Args:
            output_dir: Directory to save downloaded images (default: pages/images)
        """
        self.output_dir: Path = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: requests.Session[requests.Response] = requests.Session()

    def download_image(self, image_url: str, promotion_id: str) -> Path | None:
        """Download an image and save it locally.

        Args:
            image_url: URL of the image to download
            promotion_id: Unique promotion ID to use in filename

        Returns:
            Path to the downloaded image file, or None if download failed
        """
        if not image_url:
            logger.warning(f"Empty image URL for promotion {promotion_id}")
            return None

        # Extract file extension from URL
        parsed_url: ParseResult = urlparse(image_url)
        path_parts: list[str] = parsed_url.path.split(".")
        extension: str = path_parts[-1].lower() if len(path_parts) > 1 else "jpg"

        # Sanitize extension (only allow common image formats)
        if extension not in {"jpg", "jpeg", "png", "gif", "webp"}:
            extension = "jpg"

        # Create filename: promotion-id.extension
        filename: str = f"{promotion_id}.{extension}"
        output_path: Path = self.output_dir / filename

        # Skip if already downloaded
        if output_path.exists():
            logger.debug(f"Image already exists: {output_path}")
            return output_path

        try:
            logger.info(f"Downloading image from {image_url}")

            headers: dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
                "Accept": "image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
                "Accept-Language": "en-US,en;q=0.7,sv;q=0.3",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            }

            response: requests.Response = self.session.get(
                image_url,
                headers=headers,
                impersonate="firefox",
                timeout=30,
            )
            response.raise_for_status()

        except (OSError, ValueError, TimeoutError) as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return None
        else:
            # Save image to file
            output_path.write_bytes(response.content)  # pyright: ignore[reportUnknownMemberType]
            logger.success(f"Downloaded image to {output_path}")
            return output_path

    def get_github_pages_url(self, local_path: Path | None, base_url: str = "https://thelovinator1.github.io/rss-feeds") -> str | None:
        """Convert local image path to GitHub Pages URL.

        Args:
            local_path: Path to the local image file
            base_url: Base URL for GitHub Pages site

        Returns:
            Full GitHub Pages URL for the image, or None if image unavailable
        """
        if not local_path or not local_path.exists():
            return None

        # Convert path relative to pages/ directory
        try:
            relative_path: Path = local_path.relative_to("pages")
            return f"{base_url}/{relative_path.as_posix()}"
        except ValueError:
            # If path is not relative to pages/, use just the filename
            return f"{base_url}/images/{local_path.name}"
