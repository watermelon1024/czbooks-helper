from ..http import HyperLink


class Category(HyperLink):
    """
    Represents a category.
    """

    def __init__(self, name: str, url: str) -> None:
        """
        Initialize a new instance of the Category class.

        :param name: The name of the category.
        :type name: str
        :param url: The URL of the category.
        :type url: str
        """
        super().__init__(name, url)

    @property
    def name(self) -> str:
        """
        Get the name of the category.

        :return: The name of the category.
        :rtype: str
        """
        return self.text
