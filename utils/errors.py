class NoVacantTractsError(Exception):
    """An error that gets raised a city has no tract on which to build a park or cemetery."""
    pass