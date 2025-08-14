from dataclasses import dataclass
import logging
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DocumentModelArticle:
    number: int
    text: str
    pos_in_doc: int
    changes: Optional[list[dict]] = None


@dataclass
class DocumentModelChapter:
    name: str
    article_numbers: Optional[list[int]] = None
    changes: Optional[list[dict]] = None
    pos_in_doc: Optional[int] = 0

    def add_article_reference(self, article_number: int):
        if self.article_numbers is None:
            self.article_numbers = []
        if article_number not in self.article_numbers:
            self.article_numbers.append(article_number)


@dataclass
class DocumentModelTitle:
    name: str
    chapters: Optional[list[DocumentModelChapter]] = None
    article_numbers: Optional[list[int]] = None
    changes: Optional[list[dict]] = None
    pos_in_doc: Optional[int] = 0

    def add_child(self, child):
        if isinstance(child, DocumentModelChapter):
            if self.chapters is None:
                self.chapters = []
            self.chapters.append(child)
        else:
            raise ValueError(
                f"DocumentModelTitle can only have chapters as children, got {type(child)}"
            )
    
    def add_article_reference(self, article_number: int):
        if self.article_numbers is None:
            self.article_numbers = []
        if article_number not in self.article_numbers:
            self.article_numbers.append(article_number)


@dataclass
class DocumentModelBook:
    name: str
    titles: Optional[list[DocumentModelTitle]] = None
    chapters: Optional[list[DocumentModelChapter]] = None
    article_numbers: Optional[list[int]] = None
    changes: Optional[list[dict]] = None
    pos_in_doc: Optional[int] = 0

    def add_child(self, child):
        if isinstance(child, DocumentModelTitle):
            if self.titles is None:
                self.titles = []
            self.titles.append(child)
        elif isinstance(child, DocumentModelChapter):
            if self.chapters is None:
                self.chapters = []
            self.chapters.append(child)
        else:
            raise ValueError(
                f"DocumentModelBook can only have titles or chapters as children, got {type(child)}"
            )
    
    def add_article_reference(self, article_number: int):
        if self.article_numbers is None:
            self.article_numbers = []
        if article_number not in self.article_numbers:
            self.article_numbers.append(article_number)


class DocumentModel:
    def __init__(self):
        self.books: list[DocumentModelBook] = []
        self.titles: list[DocumentModelTitle] = []
        self.chapters: list[DocumentModelChapter] = []
        self.articles: list[DocumentModelArticle] = []

    def add_title(self, title: DocumentModelTitle):
        self.titles.append(title)

    def add_book(self, book: DocumentModelBook):
        self.books.append(book)

    def add_chapter(self, chapter: DocumentModelChapter):
        self.chapters.append(chapter)

    def add_article(self, article: DocumentModelArticle):
        self.articles.append(article)
        
    def has_articles(self):
        return self.articles is not None and len(self.articles) > 0
    
    def get_articles(self):
        return self.articles
    
    def get_article(self, art_no):
        return self.articles[art_no]
    
    def get_book(self, book_no: int):
        if book_no <= len(self.books):
            return self.books[book_no]
        else:
            return None
        
    def get_title(self, title_no: int):
        if title_no <= len(self.titles):
            return self.titles[title_no]
        else:
            return None
        
    def get_chapter(self, ch_no: int):
        if ch_no <= len(self.chapters):
            return self.chapters[ch_no]
        else:
            return None

    def log(self):
        logger.info(self.get_document_structure_info())

    def get_document_structure_info(self) -> str:
        """Generate a comprehensive string representation of the document structure."""
        lines = []
        lines.append("=== DOCUMENT STRUCTURE ===")
        lines.append(f"Total Books: {len(self.books)}")
        lines.append(f"Total Titles: {len(self.titles)}")
        lines.append(f"Total Chapters: {len(self.chapters)}")
        lines.append(f"Total Articles: {len(self.articles)}")
        lines.append("")
        
        # Log books and their children
        for i, book in enumerate(self.books):
            lines.append(f"Book {i+1}: {book.name} (pos: {book.pos_in_doc})")
            if book.titles:
                for j, title in enumerate(book.titles):
                    lines.append(f"  Title {j+1}: {title.name} (pos: {title.pos_in_doc})")
                    if title.chapters:
                        for k, chapter in enumerate(title.chapters):
                            lines.append(f"    Chapter {k+1}: {chapter.name} (pos: {chapter.pos_in_doc})")
                            if chapter.article_numbers:
                                lines.append(f"      Articles: {chapter.article_numbers}")
                    if title.article_numbers:
                        lines.append(f"    Articles: {title.article_numbers}")
            if book.chapters:
                for j, chapter in enumerate(book.chapters):
                    lines.append(f"  Chapter {j+1}: {chapter.name} (pos: {chapter.pos_in_doc})")
                    if chapter.article_numbers:
                        lines.append(f"    Articles: {chapter.article_numbers}")
            if book.article_numbers:
                lines.append(f"  Articles: {book.article_numbers}")
        
        # Log standalone titles
        for i, title in enumerate(self.titles):
            lines.append(f"Title {i+1}: {title.name} (pos: {title.pos_in_doc})")
            if title.chapters:
                for j, chapter in enumerate(title.chapters):
                    lines.append(f"  Chapter {j+1}: {chapter.name} (pos: {chapter.pos_in_doc})")
                    if chapter.article_numbers:
                        lines.append(f"    Articles: {chapter.article_numbers}")
            if title.article_numbers:
                lines.append(f"  Articles: {title.article_numbers}")
        
        # Log standalone chapters
        for i, chapter in enumerate(self.chapters):
            lines.append(f"Chapter {i+1}: {chapter.name} (pos: {chapter.pos_in_doc})")
            if chapter.article_numbers:
                lines.append(f"  Articles: {chapter.article_numbers}")
        
        # Log all articles
        # if self.articles:
        #     lines.append("")
        #     lines.append("=== ALL ARTICLES ===")
        #     for article in self.articles[:10]:  # Limit to first 10 for brevity
        #         lines.append(f"Article {article.number} (pos: {article.pos_in_doc}): {article.text[:100]}...")
        #     if len(self.articles) > 10:
        #         lines.append(f"... and {len(self.articles) - 10} more articles")
        
        return "\n".join(lines)

    def _log_articles(self, article_numbers: list[int]):
        if article_numbers:
            logger.info(f"Articles {min(article_numbers)} - {max(article_numbers)}")
