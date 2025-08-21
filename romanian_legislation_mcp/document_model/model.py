from typing import Optional

import enum


class DocumentPartType(enum.Enum):
    TOP = 0
    BOOK = 1
    TITLE = 2
    CHAPTER = 3
    SECTION = 4
    ARTICLE = 5

    def to_keyword(self) -> str:
        if self == DocumentPartType.BOOK:
            return "Cartea"
        elif self == DocumentPartType.TITLE:
            return "Titlul"
        elif self == DocumentPartType.CHAPTER:
            return "Capitolul"
        elif self == DocumentPartType.SECTION:
            return "Secţiunea"
        elif self == DocumentPartType.ARTICLE:
            return "Articolul"
        else:
            return None

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
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.BOOK:
            return [
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.TITLE:
            return [
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        elif self == DocumentPartType.CHAPTER:
            return [DocumentPartType.SECTION, DocumentPartType.ARTICLE]
        elif self == DocumentPartType.SECTION:
            return [DocumentPartType.ARTICLE]
        elif self == DocumentPartType.ARTICLE:
            return []
        else:
            return []

    def get_possible_equal_or_greater_types(self) -> list["DocumentPartType"]:
        """Returns element types that are at the same hierarchical level or higher.

        This is useful for determining when to close current elements during parsing.
        The hierarchy from highest to lowest is: TOP -> BOOK -> TITLE -> CHAPTER
        """
        if self == DocumentPartType.TOP:
            return []
        elif self == DocumentPartType.BOOK:
            return [DocumentPartType.BOOK]
        elif self == DocumentPartType.TITLE:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
            ]
        elif self == DocumentPartType.CHAPTER:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
            ]
        elif self == DocumentPartType.SECTION:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
            ]
        elif self == DocumentPartType.ARTICLE:
            return [
                DocumentPartType.BOOK,
                DocumentPartType.TITLE,
                DocumentPartType.CHAPTER,
                DocumentPartType.SECTION,
                DocumentPartType.ARTICLE,
            ]
        else:
            return []


class DocumentPart:
    def __init__(
        self,
        type_name: DocumentPartType,
        number: str = "0",
        start_pos=-1,
        end_pos=-1,
        title: str = "",
        parent: Optional["DocumentPart"] = None,
    ):
        self.type_name = type_name
        self.title = title
        self.number = number
        self.parent = parent
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.children = []

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
        
    def set_number(self, number: str):
        self.number = number

