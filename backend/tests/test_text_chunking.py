from app.services.text_chunking import chunk_text


def test_short_text_is_single_chunk():
    text = "Java course covers OOP and JDBC."
    assert chunk_text(text, max_chars=100) == [text]


def test_long_text_is_split():
    text = "\n\n".join(["Paragraph %d. Java classes and objects are covered." % i for i in range(20)])
    chunks = chunk_text(text, max_chars=150, overlap_chars=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 150 for chunk in chunks)


def test_facts_survive_chunking():
    text = "Course fee is INR 25,000.\n\nDuration is 3 months.\n\nClasses are Monday to Friday, 10 AM to 11 AM."
    joined = " ".join(chunk_text(text, max_chars=70, overlap_chars=10))
    assert "INR 25,000" in joined
    assert "3 months" in joined
    assert "Monday to Friday" in joined
