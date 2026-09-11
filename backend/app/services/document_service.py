"""Document processing service with retrieval-friendly chunked ingestion."""

from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.embedding_service import EmbeddingService
from app.services.text_chunking import chunk_text


class DocumentService:
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    CHUNK_MAX_CHARS = 1200
    CHUNK_OVERLAP_CHARS = 150

    def __init__(self, knowledge_repository: KnowledgeRepository) -> None:
        self.knowledge_repository = knowledge_repository
        self.embedding_service = EmbeddingService()

    async def process_upload(
        self,
        file: UploadFile,
        organization_id: int,
        category: str = "general",
        agent_id: int | None = None,
    ) -> list[KnowledgeBase]:
        filename = file.filename or "uploaded_document"
        extension = Path(filename).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type. Only PDF, DOCX and TXT files are allowed.")

        file_content = await file.read()
        if not file_content:
            raise ValueError("Uploaded file is empty.")

        if extension == ".pdf":
            content = self._extract_pdf(file_content)
        elif extension == ".docx":
            content = self._extract_docx(file_content)
        else:
            content = file_content.decode("utf-8", errors="ignore")
        content = content.strip()
        if not content:
            raise ValueError("No readable text was found in the uploaded file.")

        chunks = chunk_text(content, max_chars=self.CHUNK_MAX_CHARS, overlap_chars=self.CHUNK_OVERLAP_CHARS)
        if not chunks:
            raise ValueError("No readable text was found in the uploaded file.")

        base_title = Path(filename).stem
        records: list[KnowledgeBase] = []
        total = len(chunks)
        for index, chunk in enumerate(chunks, start=1):
            title = base_title if total == 1 else f"{base_title} (Part {index} of {total})"
            embedding_text = f"TITLE:\n{title}\n\nCATEGORY:\n{category}\n\nCONTENT:\n{chunk}".strip()
            record = KnowledgeBase(
                organization_id=organization_id,
                agent_id=agent_id,
                title=title,
                category=category,
                source="document_upload",
                content=chunk,
                embedding=self.embedding_service.generate(embedding_text),
            )
            records.append(self.knowledge_repository.add(record))
        return records

    def _extract_pdf(self, file_content: bytes) -> str:
        import io
        reader = PdfReader(io.BytesIO(file_content))
        pages = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n\n".join(pages)

    def _extract_docx(self, file_content: bytes) -> str:
        import io
        document = Document(io.BytesIO(file_content))
        return "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
