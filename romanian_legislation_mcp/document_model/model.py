from typing import Optional

import enum


class DocumentPartType(enum.Enum):
    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3

    def to_keyword(self) -> str:
        if self == DocumentPartType.BOOK:
            return "Cartea"
        elif self == DocumentPartType.TITLE:
            return "Titlul"
        elif self == DocumentPartType.CHAPTER:
            return "Capitolul"

    def get_possible_child_types(self) -> list["DocumentPartType"]:
        """Returns all possible child element types in decreasing hierarchical order.

        The hierarchy is not strict - elements can contain both immediate children
        and skip levels (e.g., TOP can contain BOOK and directly TITLE).
        """
        if self == DocumentPartType.TOP:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
            ]
        elif self == DocumentPartType.BOOK:
            return [DocumentPartType.TITLE, DocumentPartType.CHAPTER]
        elif self == DocumentPartType.TITLE:
            return [DocumentPartType.CHAPTER]
        elif self == DocumentPartType.CHAPTER:
            return []
        else:
            return []

    def get_possible_equal_or_greater_types(self) -> list["DocumentPartType"]:
        """Returns element types that are at the same hierarchical level or higher.

        This is useful for determining when to close current elements during parsing.
        The hierarchy from highest to lowest is: TOP -> BOOK -> TITLE -> CHAPTER
        """
        if self == DocumentPartType.TOP:
            return [DocumentPartType.TOP]
        elif self == DocumentPartType.BOOK:
            return [DocumentPartType.TOP, DocumentPartType.BOOK]
        elif self == DocumentPartType.TITLE:
            return [
                DocumentPartType.TOP,
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
            ]
        elif self == DocumentPartType.CHAPTER:
            return [
                DocumentPartType.TOP,
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
            ]
        else:
            return []


class DocumentPart:
    type_name: DocumentPartType
    children: list["DocumentPart"]
    title: str
    article_numbers: list[int]
    start_pos: int
    end_pos: int

    def __init__(
        self,
        name: DocumentPartType,
        title: str,
        parent: Optional["DocumentPart"],
        start_pos=-1,
        end_pos=-1,
    ):
        self.type_name = name
        self.title = title
        self.parent = parent
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.children = []
        self.article_numbers = []
        
    def add_child(self, child: "DocumentPart"):
        child.set_parent(self)
        self.children.append(child)
        
    def get_children_of_type(self, child_type: DocumentPartType):
        results = []
        for child in self.children:
            if child.type_name == child_type:
                results.append(child)
                
        return results
    
    def set_parent(self, parent: "DocumentPart"):
        self.parent = parent

    def has_articles(self):
        return len(self.article_numbers) > 0


class DocumentModel:
    def __init__(self):
        self.children: list[DocumentPart] = []
