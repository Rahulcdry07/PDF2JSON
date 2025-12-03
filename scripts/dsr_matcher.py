"""
DSR Matcher Module

This module handles matching logic between input items and DSR reference rates.
It implements exact code matching with description similarity validation.
Cross-code search is disabled to preserve input DSR codes.
"""

from typing import Dict, List, Optional
from text_similarity import calculate_text_similarity


def find_best_dsr_match(
    input_description: str,
    dsr_code: str,
    dsr_entries: List[Dict],
    similarity_threshold: float = 0.3,
    return_similarity: bool = False,
) -> Optional[Dict]:
    """Find the best matching DSR entry based on description similarity.

    Requires BOTH exact DSR code match AND good description similarity.
    Returns None if description similarity is below threshold.

    Args:
        input_description: Description from input file
        dsr_code: DSR code being matched
        dsr_entries: List of possible entries for this code
        similarity_threshold: Minimum similarity required (default 0.3)
        return_similarity: If True, adds 'similarity' key to returned dict

    Returns:
        Best matching DSR entry dict if similarity meets threshold, else None

    Example:
        entry = find_best_dsr_match(
            "150 mm thick cement concrete",
            "11.55.1",
            [{"description": "Providing and laying 150mm cement concrete...", "rate": 3186.70, ...}],
            similarity_threshold=0.3,
            return_similarity=True
        )
        # Returns: {"description": "...", "rate": 3186.70, "similarity": 0.75}
    """
    if not dsr_entries:
        return None

    # If only one entry, check if it meets the similarity threshold
    if len(dsr_entries) == 1:
        entry = dsr_entries[0]
        similarity = calculate_text_similarity(input_description, entry["description"])

        print(f"  DSR {dsr_code} - Single entry, similarity: {similarity:.3f}")
        print(f"    Input: {input_description[:60]}...")
        print(f"    Match: {entry['description'][:60]}...")

        if similarity >= similarity_threshold:
            if return_similarity:
                result = entry.copy()
                result["similarity"] = similarity
                return result
            return entry
        else:
            print(
                f"  ❌ Rejected: Similarity {similarity:.3f} below threshold {similarity_threshold}"
            )
            if return_similarity:
                return {"similarity": similarity}
            return None

    # Calculate similarity scores for each entry
    scored_entries = []
    for entry in dsr_entries:
        similarity = calculate_text_similarity(input_description, entry["description"])
        scored_entries.append((similarity, entry))

    # Sort by similarity (highest first)
    scored_entries.sort(key=lambda x: x[0], reverse=True)

    best_score, best_entry = scored_entries[0]

    # Log the matching process for debugging
    print(
        f"  DSR {dsr_code} - Best match: {best_score:.3f} similarity (from {len(dsr_entries)} entries)"
    )
    print(f"    Input: {input_description[:60]}...")
    print(f"    Match: {best_entry['description'][:60]}...")

    # Return best match ONLY if above threshold
    if best_score >= similarity_threshold:
        if return_similarity:
            result = best_entry.copy()
            result["similarity"] = best_score
            return result
        return best_entry
    else:
        print(
            f"  ❌ Rejected: Best similarity {best_score:.3f} below threshold {similarity_threshold}"
        )
        if return_similarity:
            return {"similarity": best_score}
        return None


def match_items_with_rates(lko_items: List[Dict], dsr_rates: Dict[str, List[Dict]]) -> List[Dict]:
    """Match Lko items with DSR rates using exact code matching only.

    Cross-code search is DISABLED to preserve input DSR codes.
    Only matches items when input DSR code exists in reference and description similarity meets threshold.

    Args:
        lko_items: List of items extracted from input file, each with dsr_code, description, unit, quantity
        dsr_rates: Dictionary mapping DSR codes to lists of rate entries

    Returns:
        List of matched items with rate, amount, and match metadata

    Example:
        matched = match_items_with_rates(
            [{"dsr_code": "DSR-11.55.1", "description": "150mm cement concrete", "quantity": 19.65, ...}],
            {"11.55.1": [{"rate": 3186.70, "description": "...", ...}]}
        )
        # Returns enriched items with rates, amounts, similarity scores
    """
    matched_items = []

    for item in lko_items:
        dsr_code = item["dsr_code"]

        # Use the pre-extracted clean DSR code
        clean_dsr_code = item.get("clean_dsr_code", dsr_code)

        best_match = None
        best_similarity = 0.0
        match_code = None

        # First, try exact match with clean code
        if clean_dsr_code in dsr_rates:
            dsr_entries = dsr_rates[clean_dsr_code]

            # Use description matching to find best entry from duplicates
            best_match = find_best_dsr_match(
                item["description"], clean_dsr_code, dsr_entries, return_similarity=True
            )

            if best_match and "similarity" in best_match:
                best_similarity = best_match["similarity"]
                match_code = clean_dsr_code

                # If similarity is good enough, use this match
                if best_similarity >= 0.3:
                    item["rate"] = best_match["rate"]
                    item["dsr_description"] = best_match["description"]
                    item["dsr_unit"] = best_match["unit"]
                    item["dsr_volume"] = best_match["volume"]
                    item["dsr_page"] = best_match.get("page", "Unknown")
                    item["match_type"] = "exact_with_description_match"
                    item["duplicate_count"] = len(dsr_entries)
                    item["clean_dsr_code"] = clean_dsr_code
                    item["similarity_score"] = best_similarity
                else:
                    # Exact code found but similarity too low - keep code but mark as low match
                    print(
                        f"\n  ⚠️  DSR {clean_dsr_code} found but similarity {best_similarity:.3f} below threshold"
                    )
                    item["rate"] = best_match.get("rate") if best_match else None
                    item["dsr_description"] = (
                        best_match.get("description", "DSR code found but description mismatch")
                        if best_match
                        else "DSR code found but description mismatch"
                    )
                    item["dsr_unit"] = best_match.get("unit", "") if best_match else ""
                    item["dsr_volume"] = best_match.get("volume", "") if best_match else ""
                    item["dsr_page"] = (
                        best_match.get("page", "Unknown") if best_match else "Unknown"
                    )
                    item["match_type"] = "code_match_but_description_mismatch"
                    item["clean_dsr_code"] = clean_dsr_code
                    item["similarity_score"] = best_similarity
            else:
                # Code not found at all
                item["rate"] = None
                item["dsr_description"] = "DSR code not found in reference files"
                item["dsr_unit"] = ""
                item["dsr_volume"] = ""
                item["match_type"] = "not_found"
                item["clean_dsr_code"] = clean_dsr_code
                item["similarity_score"] = 0.0
        else:
            # Code not found at all
            item["rate"] = None
            item["dsr_description"] = "DSR code not found in reference files"
            item["dsr_unit"] = ""
            item["dsr_volume"] = ""
            item["match_type"] = "not_found"
            item["clean_dsr_code"] = clean_dsr_code
            item["similarity_score"] = 0.0

        # Calculate amount if quantity and rate are available
        if item.get("quantity") and item.get("rate"):
            try:
                qty = float(item["quantity"])
                rate = float(item["rate"])
                item["amount"] = qty * rate
            except (ValueError, TypeError):
                item["amount"] = None

        matched_items.append(item)

    return matched_items
