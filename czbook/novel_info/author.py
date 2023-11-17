from ..http import HyperLink


class Author(HyperLink):
    """
    Represents a book author.
    """

    def __init__(self, name: str) -> None:
        """
        Initializes a new instance of the Author class.
        
        :param name: The name of the author.
        :type name: str
        """
        super().__init__(name, f"https://czbooks.net/a/{name}")

    @property
    def name(self) -> str:
        """
        Gets the name of the author.

        :return: The name of the author.
        :rtype: str
        """
        return self.text
