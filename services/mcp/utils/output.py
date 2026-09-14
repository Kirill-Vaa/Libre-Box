def truncate_output(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False

    head_size = limit // 2
    tail_size = limit - head_size
    removed = len(text) - limit

    marker = f"\n[... {removed} chars truncated ...]\n"

    head = text[:head_size]
    tail = text[len(text) - tail_size :] if tail_size else ""

    return f"{head}{marker}{tail}", True
