class Ballpark(object):

    def __init__(self):

        pass

    # # Want these things included
    # - city, intersection, year_built
    # - mapping of coordinates to whether they are in the stands, on base paths, etc.
    # - mapping of coordinates to ground rule double areas
    # - type of grass, and coefficient of restitution for that grass and
    #   coefficient of friction for that grass (which will be each be a dynamic @property)
    #   (CORs:  0.562 for non-turfed base paths (increases with more sub-surface soil compaction)
    #           0.479 for turf grass (varies per cutting height and moisture)
    #           0.520 for synthetic turf (varies according to material composition))
    # - weather and altitude stuff
    # - dampness of grass