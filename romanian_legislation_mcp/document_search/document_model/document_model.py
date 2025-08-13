from dataclasses import dataclass
import logging
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DocumentModelArticle:
    number: int
    text: str
    pos_in_doc: int


@dataclass
class DocumentModelChapter:
    name: str
    pos_in_doc: int
    articles: Optional[list[DocumentModelArticle]] = None
    
    def add_child(self, child):
        if isinstance(child, DocumentModelArticle):
            if self.articles is None:
                self.articles = []
            self.articles.append(child)
        else:
            raise ValueError(f"DocumentModelChapter can only have articles as children, got {type(child)}")


@dataclass
class DocumentModelTitle:
    name: str
    pos_in_doc: int
    chapters: Optional[list[DocumentModelChapter]] = None
    articles: Optional[list[DocumentModelArticle]] = None
    
    def add_child(self, child):
        if isinstance(child, DocumentModelChapter):
            if self.chapters is None:
                self.chapters = []
            self.chapters.append(child)
        elif isinstance(child, DocumentModelArticle):
            if self.articles is None:
                self.articles = []
            self.articles.append(child)
        else:
            raise ValueError(f"DocumentModelTitle can only have chapters or articles as children, got {type(child)}")


@dataclass
class DocumentModelBook:
    name: str
    pos_in_doc: int
    titles: Optional[list[DocumentModelTitle]] = None
    chapters: Optional[list[DocumentModelChapter]] = None
    articles: Optional[list[DocumentModelArticle]] = None
    
    def add_child(self, child):
        if isinstance(child, DocumentModelTitle):
            if self.titles is None:
                self.titles = []
            self.titles.append(child)
        elif isinstance(child, DocumentModelChapter):
            if self.chapters is None:
                self.chapters = []
            self.chapters.append(child)
        elif isinstance(child, DocumentModelArticle):
            if self.articles is None:
                self.articles = []
            self.articles.append(child)
        else:
            raise ValueError(f"DocumentModelBook can only have titles, chapters, or articles as children, got {type(child)}")


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

    def log(self):
        logger.info("=== DOCUMENT STRUCTURE ===")
        
        if self.books:
            for i, book in enumerate(self.books):
                logger.info(f"📚 Book {i+1}: {book.name}")
                if book.titles:
                    for j, title in enumerate(book.titles):
                        logger.info(f"  📖 Title {j+1}: {title.name}")
                        if title.chapters:
                            for k, chapter in enumerate(title.chapters):
                                logger.info(f"    📑 Chapter {k+1}: {chapter.name}")
                                if chapter.articles:
                                    for article in chapter.articles:
                                        logger.info(f"      📄 Article {article.number}: {article.text[:50]}...")
                        elif title.articles:
                            for article in title.articles:
                                logger.info(f"    📄 Article {article.number}: {article.text[:50]}...")
                if book.chapters:
                    for k, chapter in enumerate(book.chapters):
                        logger.info(f"  📑 Chapter {k+1}: {chapter.name}")
                        if chapter.articles:
                            for article in chapter.articles:
                                logger.info(f"    📄 Article {article.number}: {article.text[:50]}...")
                if book.articles:
                    for article in book.articles:
                        logger.info(f"  📄 Article {article.number}: {article.text[:50]}...")
        
        if self.titles:
            for i, title in enumerate(self.titles):
                logger.info(f"📖 Title {i+1}: {title.name}")
                if title.chapters:
                    for j, chapter in enumerate(title.chapters):
                        logger.info(f"  📑 Chapter {j+1}: {chapter.name}")
                        if chapter.articles:
                            for article in chapter.articles:
                                logger.info(f"    📄 Article {article.number}: {article.text[:50]}...")
                elif title.articles:
                    for article in title.articles:
                        logger.info(f"  📄 Article {article.number}: {article.text[:50]}...")
        
        if self.chapters:
            for i, chapter in enumerate(self.chapters):
                logger.info(f"📑 Chapter {i+1}: {chapter.name}")
                if chapter.articles:
                    for article in chapter.articles:
                        logger.info(f"  📄 Article {article.number}: {article.text[:50]}...")
        
        if self.articles:
            for i, article in enumerate(self.articles):
                logger.info(f"📄 Article {article.number}: {article.text[:50]}...")
        
        if not self.books and not self.titles and not self.chapters and not self.articles:
            logger.info("📭 No document structure found")
