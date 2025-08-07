import json
import logging
import os

logger = logging.getLogger(__name__)

# These are the size limits for Claude Desktop - might be different in other cases
MAX_RESPONSE_SIZE_BYTES = int(os.environ.get("MAX_RESPONSE_SIZE_BYTES", 950 * 1024))
MAX_TEXT_LENGTH_CHARS = int(os.environ.get("MAX_TEXT_LENGTH_CHARS", 10000))
TRUNCATION_SUFFIX = os.environ.get("TRUNCATION_SUFFIX", "\n\n[... Content truncated due to size limits. Use document_search for the full document if you need the complete text ...]")


def _calculate_response_size(response: dict) -> int:
    """Calculate the byte size of a JSON response."""
    try:
        return len(json.dumps(response, ensure_ascii=False).encode("utf-8"))
    except Exception as e:
        logger.warning(f"Failed to calculate response size: {e}")
        return 0


def _truncate_document_content(results: list) -> tuple[list, bool]:
    """Truncate document text content to fit within size limits."""

    was_truncated = False

    for result in results:
        if isinstance(result, dict) and "text" in result:
            text = result.get("text", "")
            if len(text) > MAX_TEXT_LENGTH_CHARS:
                result["text"] = text[:MAX_TEXT_LENGTH_CHARS] + TRUNCATION_SUFFIX
                result["content_truncated"] = True
                was_truncated = True

    return results, was_truncated


def _manage_response_size(response: dict) -> dict:
    """Manage response size by truncating content if needed."""

    current_size = _calculate_response_size(response)

    if current_size <= MAX_RESPONSE_SIZE_BYTES:
        return response

    logger.info(
        f"Response size ({current_size} bytes) exceeds limit ({MAX_RESPONSE_SIZE_BYTES} bytes), truncating content..."
    )

    if "results" in response and isinstance(response["results"], list):
        truncated_results, was_truncated = _truncate_document_content(
            response["results"]
        )
        response["results"] = truncated_results

        if was_truncated:
            response["size_management"] = {
                "content_truncated": True,
                "reason": "Response size exceeded Claude Desktop limits",
                "original_size_bytes": current_size,
                "note": "Use document_search for specific documents to get full content",
            }

        new_size = _calculate_response_size(response)
        logger.info(f"After truncation: {new_size} bytes")

        if new_size > MAX_RESPONSE_SIZE_BYTES and len(response["results"]) > 1:
            logger.info("Still too large, reducing number of results...")

            # Binary search to find maximum number of results that fit, thanks Claude for this trick
            left, right = 1, len(response["results"])
            best_count = 1

            while left <= right:
                mid = (left + right) // 2
                test_response = response.copy()
                test_response["results"] = response["results"][:mid]
                test_response["total"] = mid

                test_size = _calculate_response_size(test_response)

                if test_size <= MAX_RESPONSE_SIZE_BYTES:
                    best_count = mid
                    left = mid + 1
                else:
                    right = mid - 1

            original_count = len(response["results"])
            response["results"] = response["results"][:best_count]
            response["total"] = best_count
            response["size_management"]["results_reduced"] = True
            response["size_management"]["original_result_count"] = original_count
            response["size_management"]["reduced_to_count"] = best_count

            final_size = _calculate_response_size(response)
            response["size_management"]["final_size_bytes"] = final_size
            logger.info(
                f"Reduced to {best_count} results, final size: {final_size} bytes"
            )

    return response
