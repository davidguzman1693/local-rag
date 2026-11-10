from pathlib import Path
from typing import List, Tuple
import pypdf


class DocumentLoaderError(Exception):
    """Custom exception raised when a document cannot be loaded."""
    pass


class DocumentLoader:
    """Extracts raw text and metadata from heterogeneous document formats."""

    @staticmethod
    def load_from_file(file_path: Path) -> Tuple[str, List[Tuple[int, str]]]:
        """Loads a file and returns:
        1. Full combined text
        2. List of (page_number, page_text) tuples (for PDFs), or [(1, full_text)] for other formats.
        """
        if not file_path.exists():
            raise DocumentLoaderError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix in [".txt", ".md", ".markdown", ".json", ".csv"]:
            return DocumentLoader._load_text_file(file_path)
        elif suffix == ".pdf":
            return DocumentLoader._load_pdf_file(file_path)
        else:
            raise DocumentLoaderError(f"Unsupported file format: {suffix}. Supported: .txt, .md, .pdf")

    @staticmethod
    def _load_text_file(file_path: Path) -> Tuple[str, List[Tuple[int, str]]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return content, [(1, content)]
        except Exception as e:
            raise DocumentLoaderError(f"Failed to read text file {file_path}: {e}") from e

    @staticmethod
    def _load_pdf_file(file_path: Path) -> Tuple[str, List[Tuple[int, str]]]:
        try:
            reader = pypdf.PdfReader(file_path)
            pages: List[Tuple[int, str]] = []
            full_texts: List[str] = []

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = page_text.strip()
                if cleaned:
                    pages.append((i + 1, cleaned))
                    full_texts.append(cleaned)

            combined_text = "\n\n".join(full_texts)
            return combined_text, pages
        except Exception as e:
            raise DocumentLoaderError(f"Failed to extract PDF content from {file_path}: {e}") from e
