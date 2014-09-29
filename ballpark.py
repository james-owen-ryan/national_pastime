class Ballpark(object):

    # # Want these things included
    # - ground rules! Can just be a set of (x, y) coordinates, and if
    # batted_ball.location in ballpark.ground_rules, then instantiate GroundRuleDouble()
    # - mapping of coordinates to whether they are in the stands, on base paths, etc.
    # - mapping of coordinates to ground rule double areas
    # - type of grass, and coefficient of restitution for that grass and
    #   coefficient of friction for that grass (which will be each be a dynamic @property)
    #   (CORs:  0.562 for non-turfed base paths (increases with more sub-surface soil compaction)
    #           0.479 for turf grass (varies per cutting height and moisture)
    #           0.520 for synthetic turf (varies according to material composition))
    # - coefficient of friction and restitution for playing-field boundary fences
    # - weather and altitude stuff
    # - dampness of grass

    def __init__(self, city, tenants=[]):
        self.country = city.country
        self.city = city
        self.intersection = None
        self.tenants = tenants
        # Trivia
        # self.broke_ground = self.city.country.date
        # self.opened = self.broke_ground  # For testing only
        self.renovated = None
        self.expanded = None
        self.closed = None
        self.demolished = None
        self.construction_costs = 0
        self.financier = None
        self.architect = None
        self.structural_engineer = None
        self.general_contractor = None
        # Get playing field boundaries, which represent the boundaries of
        # the entire playing field, including fieldable foul territory,
        # and thus can be used to determine whether a ball is fieldable
        self.playing_field_lower_bound, self.playing_field_upper_bound = (
            self.get_playing_field_boundaries()
        )
        # Get outfield and foul fence heights, which are necessary to
        # determine whether a ball hits a fence or flies over it
        self.outfield_fence_height = self.get_outfield_fence_height()
        self.foul_fence_height = self.get_foul_fence_height()
        # Get foul pole locations and heights
        self.left_foul_pole_location = (
            min(self.playing_field_upper_bound.keys()),
            self.playing_field_upper_bound[min(self.playing_field_upper_bound.keys())]
        )
        self.right_foul_pole_location = (
            min(self.playing_field_upper_bound.keys()),
            self.playing_field_upper_bound[min(self.playing_field_upper_bound.keys())]
        )
        self.left_foul_pole_height = self.outfield_fence_height[self.left_foul_pole_location[0]]
        self.right_foul_pole_height = self.outfield_fence_height[self.right_foul_pole_location[0]]
        # Set ground-rule coordinates TODO
        self.ground_rule_coords = set()

    @staticmethod
    def get_playing_field_boundaries():
        # NOTE: this method assumes the initial generic playing field that
        # I devised, with 320 feet to each foul pole and 400 feet to CF
        playing_field_lower_bound = {}
        playing_field_upper_bound = {}
        # Survey outfield fence -- a perfect parabola extending between
        # the foul poles, which are each 320 feet from home plate, with
        # a vertex of 400 feet right at center field
        h, k = 226, 400  # Our vertex is the center-field wall
        a = -0.0034
        for x in xrange(0, 453):
            y = (a * (x - h)**2) + k
            playing_field_upper_bound[x-226] = y
        # Survey curved fence behind the backstop
        h, k = 23, -60  # Our vertex is deepest part of the backstop
        a = 0.0378
        for x in xrange(0, 47):
            y = (a * (x - h)**2) + k
            playing_field_lower_bound[x-23] = y
        # Survey left foul fence -- which is on a straight line connecting the
        # left corner of the backstop fence with the left corner of the
        # outfield fence, i.e., the left field foul pole -- and beyond
        left_corner_of_backstop = [-23, -40.0038]
        left_foul_pole = [-226, 226.3416]
        x_diff = abs(left_foul_pole[0]-left_corner_of_backstop[0])
        y_diff = left_foul_pole[1]-left_corner_of_backstop[1]
        y_increments = y_diff/float(x_diff)
        for i in xrange(x_diff+1):
            x = left_corner_of_backstop[0] - i
            y = left_corner_of_backstop[1] + y_increments * i
            playing_field_lower_bound[x] = y
        # Survey right foul fence -- which is on a straight line connecting the
        # right corner of the backstop fence with the right corner of the
        # outfield fence, i.e., the right field foul pole -- and beyond
        right_corner_of_backstop = [23, -40.0038]
        right_foul_pole = [226, 226.3416]
        x_diff = abs(right_foul_pole[0]-right_corner_of_backstop[0])
        y_diff = right_foul_pole[1]-right_corner_of_backstop[1]
        y_increments = y_diff/float(x_diff)
        for i in xrange(x_diff+1):
            x = right_corner_of_backstop[0] + i
            y = right_corner_of_backstop[1] + y_increments * i
            playing_field_lower_bound[x] = y
        return playing_field_lower_bound, playing_field_upper_bound

    @staticmethod
    def get_outfield_fence_height():
        # NOTE: this method assumes the initial generic playing field that
        # I devised, with 7-foot fences all around the stadium
        outfield_fence_height = {}
        for i in xrange(-225, 226):
            outfield_fence_height[i] = 7.0
        outfield_fence_height[-226] = 90.0  # Left foul pole
        outfield_fence_height[226] = 90.0  # Right foul pole
        return outfield_fence_height

    @staticmethod
    def get_foul_fence_height():
        # NOTE: this method assumes the initial generic playing field that
        # I devised, with 7-foot fences all around the stadium
        foul_fence_height = {}
        for i in xrange(-226, 227):
            foul_fence_height[i] = 7.0
        return foul_fence_height