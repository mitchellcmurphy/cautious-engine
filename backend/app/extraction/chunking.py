import tiktoken

DEFAULT_ENCODING = "o200k_base"  # gpt-4o family


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


def chunk_text(
    text: str, max_tokens: int, encoding_name: str = DEFAULT_ENCODING
) -> list[str]:
    """Splits text into chunks of at most `max_tokens`, breaking on paragraph
    boundaries where possible so a chunk doesn't cut off mid-sentence.

    A single paragraph larger than `max_tokens` on its own is hard-split by
    token count as a fallback (rare for filing text, common only for huge
    unbroken data dumps).
    """
    enc = tiktoken.get_encoding(encoding_name)
    paragraphs = [p for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = len(enc.encode(paragraph))

        if paragraph_tokens > max_tokens:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts, current_tokens = [], 0
            chunks.extend(_hard_split(paragraph, max_tokens, enc))
            continue

        if current_tokens + paragraph_tokens > max_tokens and current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts, current_tokens = [], 0

        current_parts.append(paragraph)
        current_tokens += paragraph_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def _hard_split(paragraph: str, max_tokens: int, enc: tiktoken.Encoding) -> list[str]:
    tokens = enc.encode(paragraph)
    return [
        enc.decode(tokens[i : i + max_tokens])
        for i in range(0, len(tokens), max_tokens)
    ]
