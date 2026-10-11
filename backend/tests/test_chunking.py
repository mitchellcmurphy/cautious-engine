from app.extraction.chunking import chunk_text, count_tokens


def test_short_text_is_single_chunk():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(text, max_tokens=1000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunks_respect_max_tokens():
    paragraph = "word " * 500  # ~500 tokens
    text = "\n\n".join([paragraph] * 10)

    chunks = chunk_text(text, max_tokens=800)

    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk) <= 800


def test_chunks_do_not_split_within_a_paragraph_when_it_fits():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunk_text(text, max_tokens=5)

    # each paragraph is short enough to stand alone; verify boundaries
    # are at paragraph breaks, not mid-sentence
    for chunk in chunks:
        assert (
            chunk
            in (
                "First paragraph.",
                "Second paragraph.",
                "Third paragraph.",
            )
            or chunk == text
        )


def test_oversized_single_paragraph_is_hard_split():
    huge_paragraph = "word " * 2000
    chunks = chunk_text(huge_paragraph, max_tokens=500)

    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk) <= 500


def test_empty_text_returns_no_chunks():
    assert chunk_text("", max_tokens=100) == []
