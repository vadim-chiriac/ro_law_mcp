from dataclasses import dataclass
import enum


class DocumentElementName(enum.Enum):
    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3
    
    def get_possible_child_types(self) -> list['DocumentElementName']:
        """Returns all possible child element types in decreasing hierarchical order.
        
        The hierarchy is not strict - elements can contain both immediate children
        and skip levels (e.g., TOP can contain BOOK and directly TITLE).
        """
        if self == DocumentElementName.TOP:
            return [DocumentElementName.BOOK, DocumentElementName.TITLE, DocumentElementName.CHAPTER]
        elif self == DocumentElementName.BOOK:
            return [DocumentElementName.TITLE, DocumentElementName.CHAPTER]
        elif self == DocumentElementName.TITLE:
            return [DocumentElementName.CHAPTER]
        elif self == DocumentElementName.CHAPTER:
            return []
        else:
            return []
    
    def get_possible_equal_or_greater_types(self) -> list['DocumentElementName']:
        """Returns element types that are at the same hierarchical level or higher.
        
        This is useful for determining when to close current elements during parsing.
        The hierarchy from highest to lowest is: TOP -> BOOK -> TITLE -> CHAPTER
        """
        if self == DocumentElementName.TOP:
            return [DocumentElementName.TOP]
        elif self == DocumentElementName.BOOK:
            return [DocumentElementName.TOP, DocumentElementName.BOOK]
        elif self == DocumentElementName.TITLE:
            return [DocumentElementName.TOP, DocumentElementName.BOOK, DocumentElementName.TITLE]
        elif self == DocumentElementName.CHAPTER:
            return [DocumentElementName.TOP, DocumentElementName.BOOK, DocumentElementName.TITLE, DocumentElementName.CHAPTER]
        else:
            return []

class DocumentPart:
    name: DocumentElementName
    children: list["DocumentPart"]
    article_numbers: list[int]
    start_pos: int
    end_pos: int

    def __init__(self, name: DocumentElementName, start_pos, end_pos):
        self.name = name
        self.children = []
        self.article_numbers = []
        self.start_pos = start_pos
        self.end_pos = end_pos

    def has_articles(self):
        return len(self.article_numbers) > 0


class DocumentModel:
    def __init__(self):
        self.children: list[DocumentPart] = []
