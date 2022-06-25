


def distribute(elements: "list", count_per_line: int=2):
    """
    Distribute elements in a list in a matrix.
    :param elements: list of elements
    :param count_per_line: number of elements in a line
    :return: list of lists
    """
    if len(elements) == 0:
        return []
    if len(elements) <= count_per_line:
        return [elements]
    else:
        return [elements[:count_per_line]] + distribute(elements[count_per_line:], count_per_line)
