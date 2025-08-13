import json
import logging

from romanian_legislation_mcp.api_client.legislation_document import LegislationDocument
from romanian_legislation_mcp.document_search.document_model.document_model import (
    DocumentModel,
    DocumentModelArticle,
    DocumentModelBook,
    DocumentModelChapter,
    DocumentModelTitle,
)

ROMAN_NUMERALS = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
    "XVII",
    "XVIII",
    "XIX",
    "XX",
]

logger = logging.getLogger(__name__)


class DocumentModelBuilder:
    def __init__(self, document: LegislationDocument):
        self.document = document
        self.model = None

    def build_document_model(self) -> DocumentModel:
        self.model = DocumentModel()
        self._get_books(self.document.text, parent=None, pos_in_doc=0)
        if len(self.model.books) > 0:
            for i, book in enumerate(self.model.books):
                book_text, book_start_pos = self._get_element_text_range(
                    i, self.model.books
                )
                self._get_titles(book_text, parent=book, pos_in_doc=book_start_pos)
                if book.titles:
                    for j, title in enumerate(book.titles):
                        title_text, title_start_pos = self._get_element_text_range(
                            j, book.titles
                        )
                        self._get_chapters(
                            title_text, parent=title, pos_in_doc=title_start_pos
                        )
                        if title.chapters:
                            for k, chapter in enumerate(title.chapters):
                                chapter_text, chapter_start_pos = (
                                    self._get_element_text_range(k, title.chapters)
                                )
                                self._get_articles(chapter_text, chapter, chapter_start_pos)
        else:
            self._get_titles(self.document.text, parent=None, pos_in_doc=0)
            if self.model.titles:
                for i, title in enumerate(self.model.titles):
                    title_text, title_start_pos = self._get_element_text_range(
                        i, self.model.titles
                    )
                    self._get_chapters(
                        title_text, parent=title, pos_in_doc=title_start_pos
                    )
                    if title.chapters:
                        for k, chapter in enumerate(title.chapters):
                            chapter_text, chapter_start_pos = self._get_element_text_range(
                                k, title.chapters
                            )
                            self._get_articles(chapter_text, chapter, chapter_start_pos)
                    else:
                        self._get_articles(title_text, title, title_start_pos)
            else:
                self._get_chapters(self.document.text, parent=None, pos_in_doc=0)
                if self.model.chapters:
                    for i, chapter in enumerate(self.model.chapters):
                        chapter_text, chapter_start_pos = self._get_element_text_range(
                            i, self.model.chapters
                        )
                        self._get_articles(chapter_text, chapter, chapter_start_pos)
                else:
                    self._get_articles(self.document.text, parent=None, pos_in_doc=0)

        self.model.log()
        pass

    def _build_document_structure(self):
        pass

    def _get_element_text_range(self, element_index: int, element_list):
        """Extract text range for a specific element from the document."""
        current_element = element_list[element_index]

        if element_index + 1 < len(element_list):
            next_element = element_list[element_index + 1]
            element_text = self.document.text[
                current_element.pos_in_doc : next_element.pos_in_doc
            ]
        else:
            element_text = self.document.text[current_element.pos_in_doc :]

        return element_text, current_element.pos_in_doc

    def _extract_element_and_recurse(
        self,
        parent_text: str,
        keyword: str,
        element_type: str,
        parent=None,
        pos_in_doc: int = 0,
    ):
        element_start = parent_text.find(keyword)
        if element_start == -1:
            return

        element_name_start = element_start + len(keyword)
        part_element_name_end = parent_text[element_name_start:].find("\n")
        if part_element_name_end == -1:
            full_element_name_end = len(parent_text)
        else:
            full_element_name_end = element_name_start + part_element_name_end
        element_name_row = parent_text[element_name_start:full_element_name_end]

        element_pos_in_doc = pos_in_doc + element_name_start  # Position in full doc

        if self._validate_element(element_name_row, element_type):
            if element_type == "Article":
                article_full_content = self._extract_article_content(
                    parent_text, element_start, element_name_row.strip()
                )
                self._create_and_add_element(
                    element_type, article_full_content, element_pos_in_doc, parent
                )
            else:
                self._create_and_add_element(
                    element_type, element_name_row.strip(), element_pos_in_doc, parent
                )

        search_start = full_element_name_end + 1
        while search_start < len(parent_text):
            next_element_start = parent_text.find(keyword, search_start)
            if next_element_start == -1:
                break  

            next_element_name_start = next_element_start + len(keyword)
            next_part_element_name_end = parent_text[next_element_name_start:].find("\n")
            if next_part_element_name_end == -1:
                next_full_element_name_end = len(parent_text)
            else:
                next_full_element_name_end = next_element_name_start + next_part_element_name_end
                
            next_element_name_row = parent_text[next_element_name_start:next_full_element_name_end]
            next_element_pos_in_doc = pos_in_doc + next_element_name_start

            if self._validate_element(next_element_name_row, element_type):
                if element_type == "Article":
                    next_article_full_content = self._extract_article_content(
                        parent_text, next_element_start, next_element_name_row.strip()
                    )
                    self._create_and_add_element(
                        element_type, next_article_full_content, next_element_pos_in_doc, parent
                    )
                else:
                    self._create_and_add_element(
                        element_type, next_element_name_row.strip(), next_element_pos_in_doc, parent
                    )

            search_start = next_full_element_name_end + 1

    def _create_and_add_element(
        self, element_type: str, element_name: str, pos_in_doc: int, parent=None
    ):
        """Create and add an element to its appropriate parent."""
        if element_type == "Chapter":
            chapter = DocumentModelChapter(name=element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(chapter)
            else:
                self.model.add_chapter(chapter)
        elif element_type == "Article":
            lines = element_name.split('\n', 1)
            header_line = lines[0].strip()
            article_body = lines[1].strip() if len(lines) > 1 else ""
            
            parts = header_line.split(None, 1)  
            if len(parts) >= 1:
                try:
                    article_number = int(parts[0])
                    article_title = parts[1].strip() if len(parts) > 1 else ""
                    
                    if article_body:
                        full_text = f"{article_title}\n{article_body}" if article_title else article_body
                    else:
                        full_text = article_title
                    
                    article = DocumentModelArticle(
                        number=article_number, 
                        text=full_text, 
                        pos_in_doc=pos_in_doc
                    )
                    if parent is not None:
                        parent.add_child(article)
                    else:
                        self.model.add_article(article)
                except ValueError:
                    pass
        elif element_type == "Title":
            title = DocumentModelTitle(element_name, pos_in_doc=pos_in_doc)
            if parent is not None:
                parent.add_child(title)
            else:
                self.model.add_title(title)
        elif element_type == "Book":
            book = DocumentModelBook(name=element_name, pos_in_doc=pos_in_doc)
            self.model.add_book(book)

    def _get_titles(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Titlul", "Title", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_books(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Cartea", "Book", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_chapters(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Capitolul", "Chapter", parent=parent, pos_in_doc=pos_in_doc
        )

    def _get_articles(self, text_content: str, parent=None, pos_in_doc: int = 0):
        self._extract_element_and_recurse(
            text_content, "Articolul", "Article", parent=parent, pos_in_doc=pos_in_doc
        )

    def _validate_element(self, element_name_row: str, element_type: str) -> bool:
        if element_type == "Book":
            return self._validate_book(element_name_row)
        if element_type == "Title":
            return self._validate_title(element_name_row)
        if element_type == "Chapter":
            return self._validate_chapter(element_name_row)
        if element_type == "Article":
            return self._validate_article(element_name_row)
        return True

    def _validate_book(self, book_name_row: str) -> bool:
        book_name_row = book_name_row.strip()
        # logger.info(f"Validating book: {book_name_row}")

        if book_name_row[0] != "a" and book_name_row[0] != "I":
            return False

        if len(book_name_row) > 200:
            return False

        return True

    def _validate_title(self, title_name_row: str) -> bool:
        if title_name_row.split()[0] not in ROMAN_NUMERALS:
            return False

        return True

    def _validate_chapter(self, chapter_name_row: str) -> bool:
        chapter_name_row = chapter_name_row.strip()

        words = chapter_name_row.split()
        if len(words) == 0:
            return False

        first_word = words[0]
        if first_word not in ROMAN_NUMERALS:
            return False

        if len(chapter_name_row) > 200:
            return False

        return True

    def _validate_article(self, article_name_row: str) -> bool:
        article_name_row = article_name_row.strip()

        parts = article_name_row.split()
        if len(parts) < 1:
            return False

        try:
            int(parts[0])
        except ValueError:
            return False

        return True

    def _extract_article_content(self, doc_text: str, article_start: int, article_header: str) -> str:
        """Extract the full content of an article including its text body."""
        # Find the end of this article by looking for next structural element
        article_start_in_text = article_start + len("Articolul")
        
        # Use single search to find closest next element for better performance
        article_end = len(doc_text)  # Default to end of text
        search_patterns = ["Articolul", "Capitolul", "Titlul", "Cartea"]
        
        for pattern in search_patterns:
            pos = doc_text.find(pattern, article_start_in_text)
            if pos != -1 and pos < article_end:
                article_end = pos
        
        # Extract complete article content (from "Articolul" to next element)
        article_content = doc_text[article_start:article_end].strip()
        
        # Split into header line and body
        lines = article_content.split('\n', 1)
        if len(lines) > 1:
            # Extract just the header part after "Articolul" 
            header_after_keyword = lines[0][len("Articolul"):].strip()
            article_body = lines[1].strip()
            # Return in consistent format: "number title\nbody"
            return f"{header_after_keyword}\n{article_body}" if article_body else header_after_keyword
        else:
            # Single line article - extract part after "Articolul"
            return lines[0][len("Articolul"):].strip()
