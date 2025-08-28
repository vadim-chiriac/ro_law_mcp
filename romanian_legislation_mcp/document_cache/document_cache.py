import json
import hashlib
import logging
from typing import Optional
from pathlib import Path
from dataclasses import asdict

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.mappings.issuer_mappings import (
    get_canonical_issuer,
)
from romanian_legislation_mcp.mappings.document_type_mappings import (
    get_canonical_document_type,
)

logger = logging.getLogger(__name__)


class DocumentCache:
    """Simple filesystem cache for Romanian legislation documents.

    Caches documents by their canonical identifiers (type/number/year/issuer)
    to avoid repeated API calls during testing and development.
    """

    def __init__(self, cache_dir: str = ".document_cache"):
        """Initialize the document cache.

        Args:
            cache_dir: Directory to store cached documents. Defaults to '.document_cache'
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        logger.info(f"Document cache initialized at: {self.cache_dir.absolute()}")

    def _get_cache_key(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> str:
        """Generate a cache key for the given document parameters.

        Uses canonical forms of document type and issuer to ensure consistent caching.

        Args:
            document_type: The type of the document (e.g. "lege", "hotarare")
            number: The number of the document
            year: The issuance year of the document
            issuer: The issuing authority of the document

        Returns:
            A hash-based cache key
        """
        issuer_canonical = get_canonical_issuer(issuer)
        doc_type_canonical = get_canonical_document_type(
            document_type, issuer_canonical
        )

        cache_identifier = f"{doc_type_canonical}|{number}|{year}|{issuer_canonical}"

        return hashlib.sha256(cache_identifier.encode("utf-8")).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the filesystem path for a cache file.

        Args:
            cache_key: The cache key for the document

        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self, document_type: str, number: int, year: int, issuer: str
    ) -> Optional[LegislationDocument]:
        """Retrieve a cached document if it exists.

        Args:
            document_type: The type of the document (e.g. "lege", "hotarare")
            number: The number of the document
            year: The issuance year of the document
            issuer: The issuing authority of the document

        Returns:
            The cached LegislationDocument if found, None otherwise
        """
        cache_key = self._get_cache_key(document_type, number, year, issuer)
        cache_file = self._get_cache_file_path(cache_key)
        logger.info(f"Cache file: {cache_file}")
        logger.info(f"CWD: {Path.cwd()}")
        if not cache_file.exists():
            logger.debug(
                f"Cache miss for document: {document_type} {number}/{year} from {issuer}"
            )
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            document = LegislationDocument(**cached_data)
            logger.info(
                f"Cache hit for document: {document_type} {number}/{year} from {issuer}"
            )
            return document

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Failed to load cached document {cache_key}: {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def put(
        self,
        document: LegislationDocument,
        document_type: str,
        number: int,
        year: int,
        issuer: str,
    ) -> None:
        """Cache a document for future retrieval.

        Args:
            document: The LegislationDocument to cache
            document_type: The type of the document (e.g. "lege", "hotarare")
            number: The number of the document
            year: The issuance year of the document
            issuer: The issuing authority of the document
        """
        cache_key = self._get_cache_key(document_type, number, year, issuer)
        cache_file = self._get_cache_file_path(cache_key)

        try:
            document_data = asdict(document)

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(document_data, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Cached document: {document_type} {number}/{year} from {issuer}"
            )

        except (TypeError, OSError) as e:
            logger.error(f"Failed to cache document {cache_key}: {e}")

    def clear(self) -> int:
        """Clear all cached documents.

        Returns:
            Number of files removed
        """
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                removed_count += 1
            except OSError as e:
                logger.warning(f"Failed to remove cache file {cache_file}: {e}")

        logger.info(f"Cleared {removed_count} cached documents")
        return removed_count

    def size(self) -> int:
        """Get the number of cached documents.

        Returns:
            Number of cached documents
        """
        return len(list(self.cache_dir.glob("*.json")))

    def get_cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(self.cache_dir.absolute()),
            "document_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }
