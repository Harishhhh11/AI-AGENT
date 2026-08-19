"""
Document processing service.

Handles:

1. File validation
2. Text extraction
3. Embedding generation
4. Knowledge-base storage
"""

from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_repository import (
    KnowledgeRepository,
)
from app.services.embedding_service import (
    EmbeddingService,
)


class DocumentService:
    """
    Service responsible for document ingestion.
    """

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    def __init__(
        self,
        knowledge_repository: KnowledgeRepository,
    ) -> None:

        self.knowledge_repository = (
            knowledge_repository
        )

        self.embedding_service = (
            EmbeddingService()
        )

    async def process_upload(
        self,
        file: UploadFile,
        organization_id: int,
        category: str = "general",
        agent_id: int | None = None,
    ) -> KnowledgeBase:
        """
        Process an uploaded document.

        Pipeline:

        Upload
          ↓
        Validate
          ↓
        Extract text
          ↓
        Generate embedding
          ↓
        Create KnowledgeBase
          ↓
        Save
        """

        filename = (
            file.filename
            or "uploaded_document"
        )

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        # ---------------------------------------------------------
        # 1. Validate file type
        # ---------------------------------------------------------

        if (
            extension
            not in self.ALLOWED_EXTENSIONS
        ):

            raise ValueError(
                "Unsupported file type. "
                "Only PDF, DOCX and TXT files are allowed."
            )

        # ---------------------------------------------------------
        # 2. Read uploaded file
        # ---------------------------------------------------------

        file_content = await file.read()

        if not file_content:

            raise ValueError(
                "Uploaded file is empty."
            )

        # ---------------------------------------------------------
        # 3. Extract text
        # ---------------------------------------------------------

        if extension == ".pdf":

            content = self._extract_pdf(
                file_content
            )

        elif extension == ".docx":

            content = self._extract_docx(
                file_content
            )

        else:

            content = file_content.decode(
                "utf-8",
                errors="ignore",
            )

        content = content.strip()

        if not content:

            raise ValueError(
                "No readable text was found "
                "in the uploaded file."
            )

        # ---------------------------------------------------------
        # 4. Generate embedding
        # ---------------------------------------------------------

        embedding = (
            self.embedding_service.generate(
                content
            )
        )

        # ---------------------------------------------------------
        # 5. Create knowledge record
        # ---------------------------------------------------------

        knowledge = KnowledgeBase(
            organization_id=organization_id,
            agent_id=agent_id,
            title=Path(filename).stem,
            category=category,
            source="document_upload",
            content=content,
            embedding=embedding,
        )

        # ---------------------------------------------------------
        # 6. Save knowledge
        # ---------------------------------------------------------

        return self.knowledge_repository.add(
            knowledge
        )

    # =============================================================
    # PDF extraction
    # =============================================================

    def _extract_pdf(
        self,
        file_content: bytes,
    ) -> str:

        import io

        reader = PdfReader(
            io.BytesIO(file_content)
        )

        pages: list[str] = []

        for page in reader.pages:

            text = page.extract_text()

            if text:

                pages.append(
                    text
                )

        return "\n\n".join(
            pages
        )

    # =============================================================
    # DOCX extraction
    # =============================================================

    def _extract_docx(
        self,
        file_content: bytes,
    ) -> str:

        import io

        document = Document(
            io.BytesIO(file_content)
        )

        paragraphs: list[str] = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:

                paragraphs.append(
                    text
                )

        return "\n".join(
            paragraphs
        )
