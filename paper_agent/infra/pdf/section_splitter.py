"""Split PDF text into academic paper sections using heuristics."""

from __future__ import annotations

import re
from typing import Any

from paper_agent.domain.models.paper_content import PaperSection

_SECTION_PATTERNS = [
    # "1. Introduction" or "1 Introduction"
    # Longer patterns must come first (e.g. "Experimental Results" before "Experiments")
    re.compile(r"^(\d+\.?\s+)(Introduction|Related\s+Work|Background|Methodology|Method|Methods|"
               r"Approach|Proposed\s+Method|Framework|Model|Architecture|"
               r"Experimental\s+Setup|Experimental\s+Results?|Experiments?|Results?\s+and\s+Discussion|Results?|"
               r"Evaluation|Analysis|Ablation\s+Study|Ablation|Discussion|"
               r"Conclusions?\s+and\s+Future\s+Work|Conclusions?|Conclusion|Summary|Future\s+Work|"
               r"Appendix|Supplementary|Acknowledgments?|Acknowledgements?|References|Bibliography)",
               re.IGNORECASE | re.MULTILINE),
    # "I. INTRODUCTION" (IEEE style)
    re.compile(r"^((?:I{1,3}V?|VI{0,3}|IX|X{0,3})\.?\s+)"
               r"(INTRODUCTION|RELATED\s+WORK|BACKGROUND|METHODOLOGY|METHOD|METHODS|"
               r"APPROACH|PROPOSED\s+METHOD|FRAMEWORK|MODEL|ARCHITECTURE|"
               r"EXPERIMENTAL\s+SETUP|EXPERIMENTAL\s+RESULTS?|EXPERIMENTS?|RESULTS?\s+AND\s+DISCUSSION|RESULTS?|EVALUATION|"
               r"ANALYSIS|ABLATION|DISCUSSION|CONCLUSIONS?\s+AND\s+FUTURE\s+WORK|CONCLUSIONS?|"
               r"APPENDIX|REFERENCES|BIBLIOGRAPHY)",
               re.MULTILINE),
]

_CANONICAL_NAMES: dict[str, str] = {
    "introduction": "introduction",
    "related work": "related_work",
    "background": "background",
    "methodology": "method",
    "method": "method",
    "methods": "method",
    "approach": "method",
    "proposed method": "method",
    "framework": "method",
    "model": "method",
    "architecture": "method",
    "experiments": "experiments",
    "experiment": "experiments",
    "experimental setup": "experiments",
    "experimental results": "experiments",
    "results and discussion": "results",
    "results": "results",
    "result": "results",
    "evaluation": "experiments",
    "analysis": "analysis",
    "ablation study": "ablation",
    "ablation": "ablation",
    "discussion": "discussion",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "conclusions and future work": "conclusion",
    "summary": "conclusion",
    "future work": "future_work",
    "appendix": "appendix",
    "supplementary": "appendix",
    "acknowledgments": "acknowledgments",
    "acknowledgement": "acknowledgments",
    "references": "references",
    "bibliography": "references",
}


def _canonicalize(heading: str) -> str:
    key = heading.lower().strip()
    return _CANONICAL_NAMES.get(key, key.replace(" ", "_"))


def split_sections(
    full_text: str,
    page_texts: list[dict[str, Any]] | None = None,
) -> list[PaperSection]:
    """Split paper text into sections based on heading detection.

    If page_texts is provided (list of {"page": int, "text": str}),
    page ranges are estimated for each section.
    """
    matches: list[tuple[int, int, str, str]] = []  # (start, end, prefix, heading)

    for pattern in _SECTION_PATTERNS:
        for m in pattern.finditer(full_text):
            prefix = m.group(1).strip()
            heading = m.group(2).strip()
            matches.append((m.start(), m.end(), prefix, heading))

    if not matches:
        return [PaperSection(name="full_text", heading="Full Text", text=full_text, page_range=(0, 0))]

    matches.sort(key=lambda x: x[0])

    # Deduplicate overlapping matches (keep the first at each position)
    deduped: list[tuple[int, int, str, str]] = []
    for start, end, prefix, heading in matches:
        if not deduped or start - deduped[-1][0] > 20:
            deduped.append((start, end, prefix, heading))
    matches = deduped

    # Build page offset map for page_range estimation
    page_offsets: list[tuple[int, int]] = []  # (char_offset, page_num)
    if page_texts:
        offset = 0
        for p in page_texts:
            page_offsets.append((offset, p["page"]))
            offset += len(p["text"]) + 2  # +2 for "\n\n" separator

    def _find_page(char_pos: int) -> int:
        if not page_offsets:
            return 0
        for i in range(len(page_offsets) - 1, -1, -1):
            if char_pos >= page_offsets[i][0]:
                return page_offsets[i][1]
        return 0

    # Add preamble (abstract / text before first section heading)
    sections: list[PaperSection] = []
    if matches[0][0] > 100:
        preamble_text = full_text[: matches[0][0]].strip()
        if preamble_text:
            sections.append(PaperSection(
                name="abstract",
                heading="Abstract",
                text=preamble_text,
                page_range=(0, _find_page(matches[0][0])),
            ))

    for i, (start, end, prefix, heading) in enumerate(matches):
        next_start = matches[i + 1][0] if i + 1 < len(matches) else len(full_text)
        section_text = full_text[end: next_start].strip()

        start_page = _find_page(start)
        end_page = _find_page(next_start)

        sections.append(PaperSection(
            name=_canonicalize(heading),
            heading=heading,
            text=section_text,
            page_range=(start_page, end_page),
        ))

    return sections
