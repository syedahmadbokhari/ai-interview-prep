from __future__ import annotations

from rag.chunking import MAX_WORDS, Chunk, chunk_markdown, split_sections

SAMPLE = """\
# Demo Project

Intro paragraph before any section heading.

## Architecture

The system uses DuckDB as the warehouse and reads from S3.

```
## this heading is inside a code fence and must be ignored
```

## Results

| Metric | Value |
|---|---|
| Reduction | 58.7% |

### Caveats

Small dataset, so clustering effects are hard to isolate.
"""


def test_sections_split_on_headings():
    sections = dict(split_sections(SAMPLE))
    assert "Architecture" in sections
    assert "Results" in sections
    assert "Caveats" in sections


def test_intro_before_first_heading_is_kept_and_titled():
    sections = split_sections(SAMPLE)
    assert sections[0][0] == "Demo Project (Introduction)"
    assert "Intro paragraph" in sections[0][1]


def test_heading_inside_code_fence_is_not_a_section():
    headings = [h for h, _ in split_sections(SAMPLE)]
    assert not any("code fence" in h for h in headings)
    # the fenced content stays inside the Architecture section
    sections = dict(split_sections(SAMPLE))
    assert "inside a code fence" in sections["Architecture"]


def test_chunks_carry_metadata():
    chunks = chunk_markdown(SAMPLE, project="demo-project", source_file="demo.md")
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.project == "demo-project" for c in chunks)
    assert all(c.source_file == "demo.md" for c in chunks)
    results = [c for c in chunks if c.heading == "Results"]
    assert len(results) == 1
    assert "58.7%" in results[0].text
    assert results[0].citation() == "demo-project > Results"


def test_short_sections_stay_whole():
    chunks = chunk_markdown(SAMPLE, project="p", source_file="f.md")
    assert all("part" not in c.heading for c in chunks)


def test_long_section_is_split_with_overlap():
    paragraphs = [f"Paragraph {i} " + ("word " * 60) for i in range(12)]
    long_doc = "## Big Section\n\n" + "\n\n".join(paragraphs)
    chunks = chunk_markdown(long_doc, project="p", source_file="f.md")
    assert len(chunks) > 1
    assert all(c.heading.startswith("Big Section (part") for c in chunks)
    assert all(len(c.text.split()) <= MAX_WORDS + 61 for c in chunks)
    # overlap: last paragraph of piece N reappears in piece N+1
    for a, b in zip(chunks, chunks[1:]):
        last_para_a = a.text.split("\n\n")[-1]
        assert last_para_a in b.text


def test_roundtrip_serialization():
    chunks = chunk_markdown(SAMPLE, project="p", source_file="f.md")
    restored = [Chunk.from_dict(c.to_dict()) for c in chunks]
    assert restored == chunks
