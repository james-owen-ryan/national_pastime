import random
import pyqtree
from utils.utilities import PriorityQueue, clamp, insert_into, insert_once
from utils.config import Config
from corpora import Names


CONFIG = Config()


class CityPlan(object):
    """A plan for a city in terms of streets, parcels, lots, and tracts."""

    def __init__(self, city):
        """Initialize a CityPlan object.

        @param city: The city for whom this plan is being devised.
        """
        self.city = city
        self.streets = set()
        self.blocks = set()
        self.tracts = set()
        self.lots = set()
        # These get used internally by methods below
        self._planned_parcels = []
        self._planned_street_segments = {'ns': {}, 'ew': {}}
        self._house_numberings = {}
        self._north_south_streets = {}
        self._east_west_streets = {}
        self._parcels_listing = {}
        self._lots_listing = {}
        self._street_corners = set()
        self._street_connections = {}
        # Devise a city plan
        self.generate_city_plan()
        self.parcels = set(self._parcels_listing.values())
        self.travel_distances_between_parcels = self._determine_travel_distances_between_parcels()

    def generate_city_plan(self):
        """Generate a plan for a city that specifies what will be its streets, blocks, lots, and tracts.

        This partitioning is done by recursively subdividing the city area into square lots and tracts,
        using a quadtree data structure.
        """
        # Set quadtree parameters according to config file
        n_quadtree_loci, n_quadtree_samples, quadtree_size, quadtree_multiplier = (
            CONFIG.quadtree_loci, CONFIG.quadtree_samples, CONFIG.quadtree_size, CONFIG.quadtree_multiplier
        )
        # Build a quadtree
        quadtree = self._build_quadtree(size=quadtree_size, n_loci=n_quadtree_loci, n_samples=n_quadtree_samples)
        # Traverse it to collect planned parcels and segments of planned streets
        self._traverse_quadtree_to_collect_planned_parcels_and_street_segments(quadtree)
        # Combine street segments to form planned streets
        planned_streets = self._combine_street_segments_into_planned_streets(
            quadtree_size=quadtree_size, quadtree_multiplier=quadtree_multiplier,
            planned_street_segments=self._planned_street_segments
        )
        # Instantiate objects representing these planned streets
        for street_plan in planned_streets:
            street_object = self._reify_street(
                city=self.city, street_plan=street_plan, quadtree_multiplier=quadtree_multiplier
            )
            self.streets.add(street_object)
        # Survey which streets run which directions
        self._north_south_streets, self._east_west_streets = self._survey_street_directions(streets=self.streets)
        # Survey direct connections between streets
        self._street_connections = self._survey_street_connections(streets=self.streets)
        # Instantiate objects representing the planned parcels from above, as well as lots and
        # tracts incident on them; also do housekeeping associated with these new objects
        for parcel_plan in self._planned_parcels:
            ew = int(parcel_plan[0] / quadtree_multiplier) + 1
            ns = int(parcel_plan[1] / quadtree_multiplier) + 1
            size_of_parcel = int(parcel_plan[2] / quadtree_multiplier)
            self._reify_parcels_and_update_parcel_listing(ew=ew, ns=ns, size_of_parcel=size_of_parcel)
            self._update_house_numbering_listing_for_new_parcel(ew=ew, ns=ns, size_of_parcel=size_of_parcel)
            # If this parcel is incident on a tract, instantiate a Tract object for that
            if size_of_parcel > 1:
                self._reify_tract(
                    ew=ew, ns=ns, size_of_parcel=size_of_parcel, quadtree_size=quadtree_size,
                    n_buildings_per_parcel=CONFIG.n_buildings_per_parcel
                )
            self._reify_lots(
                ew=ew, ns=ns, size_of_parcel=size_of_parcel, quadtree_size=quadtree_size,
                n_buildings_per_parcel=CONFIG.n_buildings_per_parcel
            )
        # Attribute parcels to lots and vice versa
        self._attribute_parcels_and_lots()
        # Attribute to each parcel its neighboring parcels
        self._attribute_neighboring_parcels()

    @staticmethod
    def _build_quadtree(size, n_loci, n_samples):
        """Build a quadtree."""
        quadtree = pyqtree.Index(bbox=[0, 0, size, size])
        # Randomly determine coordinates for each locus
        loci_coordinates = []
        for _ in range(n_loci):
            locus_x_coord = random.gauss(size/2.0, size/6.0)
            locus_y_coord = random.gauss(size/2.0, size/6.0)
            loci_coordinates.append([locus_x_coord, locus_y_coord])
        for _ in range(n_samples):
            center = random.choice(loci_coordinates)
            point = [
                clamp(random.gauss(center[0], size/6.0), 0, size-1),
                clamp(random.gauss(center[1], size/6.0), 0, size-1)
            ]
            point += [point[0]+1, point[1]+1]
            quadtree.insert(point, point)
        return quadtree

    def _traverse_quadtree_to_collect_planned_parcels_and_street_segments(self, node):
        """Traverse a quadtree to collect all the planned blocks and street segments that it specifies."""
        if len(node.children) == 0 and node.width != 1:
            w = int(node.center[0] - node.width * 0.5)
            e = int(node.center[0] + node.width * 0.5)
            n = int(node.center[1] - node.width * 0.5)
            s = int(node.center[1] + node.width * 0.5)
            self._planned_parcels.append((w, n, node.width))
            self._planned_street_segments['ns'][(w, n)] = (w, s)
            self._planned_street_segments['ns'][(e, n)] = (e, s)
            self._planned_street_segments['ew'][(w, n)] = (e, n)
            self._planned_street_segments['ew'][(w, s)] = (e, s)
        for child in node.children:
            self._traverse_quadtree_to_collect_planned_parcels_and_street_segments(node=child)

    @staticmethod
    def _combine_street_segments_into_planned_streets(quadtree_size, quadtree_multiplier, planned_street_segments):
        """Combine segments of planned streets into full planned streets."""
        street_termini = {'ns': [], 'ew': []}
        planned_streets = []
        for i in xrange(0, quadtree_size+quadtree_multiplier, quadtree_multiplier):
            for j in xrange(0, quadtree_size+quadtree_multiplier, quadtree_multiplier):
                street_origin_coordinates = (i, j)
                if street_origin_coordinates in planned_street_segments['ns']:
                    direction = 'ns'
                    # Combine all planned segments of this street into a single planned street
                    street_terminus_coordinates = planned_street_segments[direction][street_origin_coordinates]
                    while street_terminus_coordinates in planned_street_segments[direction]:
                        street_terminus_coordinates = planned_street_segments[direction][street_terminus_coordinates]
                    if street_terminus_coordinates not in street_termini[direction]:
                        street_termini[direction].append(street_terminus_coordinates)
                        planned_streets.append([direction, street_origin_coordinates, street_terminus_coordinates])
                if street_origin_coordinates in planned_street_segments['ew']:
                    direction = 'ew'
                    # Combine all planned segments of this street into a single planned street
                    street_terminus_coordinates = planned_street_segments[direction][street_origin_coordinates]
                    while street_terminus_coordinates in planned_street_segments[direction]:
                        street_terminus_coordinates = planned_street_segments[direction][street_terminus_coordinates]
                    if street_terminus_coordinates not in street_termini[direction]:
                        street_termini[direction].append(street_terminus_coordinates)
                        planned_streets.append([direction, street_origin_coordinates, street_terminus_coordinates])
        return planned_streets

    @staticmethod
    def _reify_street(street_plan, city, quadtree_multiplier):
        """Instantiate a Street object given a street plan."""
        if street_plan[0] == "ns":
            number = int(street_plan[1][0]/quadtree_multiplier) + 1
        else:
            number = int(street_plan[1][1]/quadtree_multiplier) + 1
        if street_plan[0] == "ns":
            starting_parcel = street_plan[1][1]
            ending_parcel = street_plan[2][1]
        else:
            starting_parcel = street_plan[1][0]
            ending_parcel = street_plan[2][0]
        starting_parcel = int(starting_parcel/quadtree_multiplier) + 1
        ending_parcel = int(ending_parcel/quadtree_multiplier) + 1
        street_object = Street(
            city=city, number=number, direction=street_plan[0],
            starting_parcel=starting_parcel, ending_parcel=ending_parcel
        )
        return street_object

    @staticmethod
    def _survey_street_directions(streets):
        """Survey which streets run in which directions."""
        north_south_streets = {}
        east_west_streets = {}
        for street in streets:
            for i in xrange(street.starting_parcel, street.ending_parcel+1):
                if street.direction == "ns":
                    north_south_streets[(street.number, i)] = street
                else:
                    east_west_streets[(i, street.number)] = street
        return north_south_streets, east_west_streets

    @staticmethod
    def _survey_street_connections(streets):
        """Survey all direction connections between streets."""
        connections = {}
        for street in streets:
            for i in xrange(street.starting_parcel, street.ending_parcel):
                if street.direction == "ns":
                    coord_of_this_street = (street.number, i)
                    coord_of_next_street_over = (street.number, i+1)
                else:
                    coord_of_this_street = (i, street.number)
                    coord_of_next_street_over = (i+1, street.number)
                if coord_of_this_street not in connections:
                    connections[coord_of_this_street] = set()
                if coord_of_next_street_over not in connections:
                    connections[coord_of_next_street_over] = set()
                connections[coord_of_this_street].add(coord_of_next_street_over)
                connections[coord_of_next_street_over].add(coord_of_this_street)
        return connections

    def _reify_parcels_and_update_parcel_listing(self, ew, ns, size_of_parcel):
        """Instantiate new Block objects and update the listing of blocks."""
        for i in xrange(size_of_parcel+1):
            insert_once(
                self._parcels_listing, (ew, ns+i, 'NS'),
                Parcel(self._north_south_streets[(ew, ns)], (i+ns) * 100, (ew, ns+i))
            )
            insert_once(
                self._parcels_listing, (ew+i, ns, 'EW'),
                Parcel(self._east_west_streets[(ew, ns)], (i+ew) * 100, (ew+i, ns))
            )
            insert_once(
                self._parcels_listing, (ew+size_of_parcel, ns+i, 'NS'),
                Parcel(self._north_south_streets[(ew+size_of_parcel, ns)], (i+ns) * 100, (ew+size_of_parcel, ns+i))
            )
            insert_once(
                self._parcels_listing, (ew+i, ns+size_of_parcel, 'EW'),
                Parcel(self._east_west_streets[(ew, ns+size_of_parcel)], (i+ew) * 100, (ew+i, ns+size_of_parcel))
            )

    def _update_house_numbering_listing_for_new_parcel(self, ew, ns, size_of_parcel):
        """Update the listing of house numberings for each block for the newly instantiated blocks."""
        for i in xrange(size_of_parcel+1):
            insert_once(
                self._house_numberings, (ew + size_of_parcel, ns+i, 'W'),
                Parcel.determine_house_numbering((i + ns) * 100, 'W')
            )
            insert_once(
                self._house_numberings, (ew+i, ns, 'N'),
                Parcel.determine_house_numbering((i + ew) * 100, 'N')
            )
            insert_once(
                self._house_numberings, (ew, ns+i, 'E'),
                Parcel.determine_house_numbering((i + ns) * 100, 'E')
            )
            insert_once(
                self._house_numberings, (ew+i, ns + size_of_parcel, 'S'),
                Parcel.determine_house_numbering((i + ew) * 100, 'S')
            )

    def _reify_tract(self, ew, ns, size_of_parcel, quadtree_size, n_buildings_per_parcel):
        """Instantiate a Tract object and attribute its blocks."""
        tract = Tract(city=self.city)
        self.tracts.add(tract)
        for i in xrange(size_of_parcel+1):
            tract.attribute_parcel(
                parcel=self._parcels_listing[(ew, ns+i, 'NS')],
                number=self._house_numberings[(ew, ns+i, 'E')][n_buildings_per_parcel],
                side_of_street='E',
                position_in_parcel=0
            )
            tract.attribute_parcel(
                parcel=self._parcels_listing[(ew+i, ns, 'EW')],
                number=self._house_numberings[(ew+i, ns, 'N')][n_buildings_per_parcel],
                side_of_street='N',
                position_in_parcel=0
            )
            if ew + size_of_parcel <= quadtree_size / 2:
                tract.attribute_parcel(
                    parcel=self._parcels_listing[(ew + size_of_parcel, ns+i, 'NS')],
                    number=self._house_numberings[(ew + size_of_parcel, ns+i, 'W')][n_buildings_per_parcel],
                    side_of_street='W',
                    position_in_parcel=0
                )
            if ns + size_of_parcel <= quadtree_size / 2:
                tract.attribute_parcel(
                    parcel=self._parcels_listing[(ew+i, ns + size_of_parcel, 'EW')],
                    number=self._house_numberings[(ew+i, ns + size_of_parcel, 'S')][n_buildings_per_parcel],
                    side_of_street='S',
                    position_in_parcel=0
                )

    def _reify_lots(self, ew, ns, size_of_parcel, quadtree_size, n_buildings_per_parcel):
        """Instantiate Lot objects for a given block."""
        # Lot on northeast corner of block
        northeast_corner = Lot(city=self.city)
        insert_into(self._lots_listing, (ew, ns, 'N'), (0, northeast_corner))
        insert_into(self._lots_listing, (ew, ns, 'E'), (0, northeast_corner))
        self._street_corners.add((ew, ns, 'EW', ew, ns, 'NS'))
        self.lots.add(northeast_corner)
        # Lot on northwest corner of block
        northwest_corner = Lot(city=self.city)
        if ew + size_of_parcel <= quadtree_size / 2:
            insert_into(
                self._lots_listing, (ew + size_of_parcel - 1, ns, 'N'), (n_buildings_per_parcel - 1, northwest_corner)
            )
        insert_into(self._lots_listing, (ew + size_of_parcel, ns, 'W'), (0, northwest_corner))
        self._street_corners.add((ew + size_of_parcel - 1, ns, 'EW', ew + size_of_parcel, ns, 'NS'))
        self.lots.add(northwest_corner)
        # Lot on southeast corner of block
        southeast_corner = Lot(city=self.city)
        insert_into(self._lots_listing, (ew, ns + size_of_parcel, 'S'), (0, southeast_corner))
        if ns + size_of_parcel <= quadtree_size / 2:
            insert_into(
                self._lots_listing, (ew, ns + size_of_parcel - 1, 'E'), (n_buildings_per_parcel - 1, southeast_corner)
            )
        self._street_corners.add((ew, ns + size_of_parcel, 'EW', ew, ns + size_of_parcel - 1, 'NS'))
        self.lots.add(southeast_corner)
        # Lot on southwest corner of block
        southwest_corner = Lot(city=self.city)
        insert_into(
            self._lots_listing, (ew + size_of_parcel - 1, ns + size_of_parcel, 'S'),
            (n_buildings_per_parcel - 1, southwest_corner)
        )
        insert_into(
            self._lots_listing, (ew + size_of_parcel, ns + size_of_parcel - 1, 'W'),
            (n_buildings_per_parcel - 1, southwest_corner)
        )
        self._street_corners.add(
            (ew + size_of_parcel - 1, ns + size_of_parcel, 'EW', ew + size_of_parcel, ns + size_of_parcel - 1, 'NS'))
        self.lots.add(southwest_corner)
        # Interior lots (?)
        for i in range(1, size_of_parcel * CONFIG.n_buildings_per_parcel - 1):
            block_number = int(i / 2)
            lot = Lot(city=self.city)
            self.lots.add(lot)
            insert_into(self._lots_listing, (ew, ns + block_number, 'E'), (i % n_buildings_per_parcel, lot))
            lot = Lot(city=self.city)
            self.lots.add(lot)
            insert_into(self._lots_listing, (ew + block_number, ns, 'N'), (i % n_buildings_per_parcel, lot))
            lot = Lot(city=self.city)
            self.lots.add(lot)
            insert_into(
                self._lots_listing, (ew + size_of_parcel, ns + block_number, 'W'), (i % n_buildings_per_parcel, lot)
            )
            lot = Lot(city=self.city)
            self.lots.add(lot)
            insert_into(
                self._lots_listing, (ew + block_number, ns + size_of_parcel, 'S'), (i % n_buildings_per_parcel, lot)
            )

    def _attribute_parcels_and_lots(self):
        """Attribute to lots which blocks they are on and to blocks which lots are on them."""
        for lot_plan in self._lots_listing:
            direction = 'NS' if lot_plan[2] == 'W' or lot_plan[2] == 'E' else 'EW'
            actual_block = self._parcels_listing[(lot_plan[0], lot_plan[1], direction)]
            lot_listing = self._lots_listing[lot_plan]
            for lot in lot_listing:
                lot[1].attribute_parcel(
                    parcel=actual_block,
                    number=self._house_numberings[lot_plan][lot[0]],
                    side_of_street=lot_plan[2],
                    position_in_parcel=lot[0]
                )
                actual_block.lots.append(lot[1])

    def _attribute_neighboring_parcels(self):
        """Attribute to each block which other blocks neighbor it."""
        for conn in self._street_connections:
            for neighbor in self._street_connections[conn]:
                dx = neighbor[0] - conn[0]
                dy = neighbor[1] - conn[1]
                if dx != 0:
                    if ((conn[0], conn[1], 'EW') in self._parcels_listing and
                            (neighbor[0], neighbor[1], 'EW') in self._parcels_listing):
                        self._parcels_listing[(conn[0], conn[1], 'EW')].add_neighbor(
                            self._parcels_listing[(neighbor[0], neighbor[1], 'EW')]
                        )
                if dy != 0:
                    if ((conn[0], conn[1], 'NS') in self._parcels_listing and
                            (neighbor[0], neighbor[1], 'NS') in self._parcels_listing):
                        self._parcels_listing[(conn[0], conn[1], 'NS')].add_neighbor(
                            self._parcels_listing[(neighbor[0], neighbor[1], 'NS')]
                        )
        for corner in self._street_corners:
            self._parcels_listing[(corner[0], corner[1], corner[2])].add_neighbor(
                self._parcels_listing[(corner[3], corner[4], corner[5])]
            )
            self._parcels_listing[(corner[3], corner[4], corner[5])].add_neighbor(
                self._parcels_listing[(corner[0], corner[1], corner[2])]
            )

    def _determine_travel_distances_between_parcels(self):
        """Determine travel distances between blocks, given street layouts."""
        travel_distances_between_blocks = {}
        for start in self.parcels:
            for goal in self.parcels:
                if start == goal:
                    travel_distances_between_blocks[(start, goal)] = 0
                elif (start, goal) not in travel_distances_between_blocks:
                    came_from, cost_so_far = self.a_star_search(start, goal)
                    current = goal
                    count = 0
                    while current != start:
                        current = came_from[current]
                        count += 1
                    travel_distances_between_blocks[(start, goal)] = count
                    travel_distances_between_blocks[(goal, start)] = count
        return travel_distances_between_blocks

    def determine_conventional_city_blocks(self):
        """Survey all city lots to instantiate conventional city blocks."""
        for lot in self.lots | self.tracts:
            number, street = lot.parcel_address_is_on.number, lot.parcel_address_is_on.street
            try:
                city_block = next(b for b in self.blocks if b.number == number and b.street is street)
                city_block.lots.append(lot)
                lot.block = city_block
            except StopIteration:
                city_block = Block(number=number, street=street)
                self.blocks.add(city_block)
                city_block.lots.append(lot)
                lot.block = city_block
        for block in self.blocks:
            block.lots.sort(key=lambda lot: lot.house_number)
        # Fill in any missing blocks, which I think gets caused by tracts being so
        # large in some cases; these blocks will not have any lots on them, so they'll
        # never have buildings on them, but it makes city navigation more natural during gameplay
        for street in self.streets:
            street.blocks.sort(key=lambda block: block.number)
            if street.blocks:  # Not sure how it's possible that streets don't have blocks, but this does happen
                current_block_number = min(street.blocks, key=lambda block: block.number).number
                largest_block_number = max(street.blocks, key=lambda block: block.number).number
                while current_block_number != largest_block_number:
                    current_block_number += 100
                    if not any(b for b in street.blocks if b.number == current_block_number):
                        self.blocks.add(Block(number=current_block_number, street=street))
                # Sort one last time to facilitate easy navigation during gameplay
                street.blocks.sort(key=lambda block: block.number)

    @staticmethod
    def heuristic(a, b):
        x1, y1 = a.coords
        x2, y2 = b.coords
        return abs(x1 - x2) + abs(y1 - y2)

    def a_star_search(self, start, goal):
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0
        while not frontier.empty():
            current_block = frontier.get()
            if current_block == goal:
                break
            for next_block in current_block.neighbors:
                new_cost = cost_so_far[current_block] + 1
                if next_block not in cost_so_far or new_cost < cost_so_far[next_block]:
                    cost_so_far[next_block] = new_cost
                    priority = new_cost + self.heuristic(goal, next_block)
                    frontier.put(next_block, priority)
                    came_from[next_block] = current_block
        return came_from, cost_so_far


class Street(object):
    """A street in a city."""

    counter = 0

    def __init__(self, city, number, direction, starting_parcel, ending_parcel):
        """Initialize a Street object."""
        self.id = Street.counter
        Street.counter += 1
        self.city = city
        self.number = number
        self.direction = direction
        self.name = self.generate_name(number=number, direction=direction)
        self.starting_parcel = starting_parcel
        self.ending_parcel = ending_parcel
        self.blocks = []  # Gets appended to by Block.__init__()

    @staticmethod
    def generate_name(number, direction):
        """Generate a street name."""
        number_to_ordinal = {
            1: '1st', 2: '2nd', 3: '3rd', 21: '21st', 22: '22nd', 23: '23rd',
            31: '31st', 32: '32nd', 33: '33rd', 41: '41st', 42: '42nd', 43: '43rd',
        }
        if number in number_to_ordinal:
            ordinal = number_to_ordinal[number]
        else:
            ordinal = str(number) + 'th'
        if direction == 'ew':
            street_type = 'Street'
            if random.random() < CONFIG.chance_street_gets_numbered_name:
                name = ordinal
            else:
                if random.random() < 0.5:
                    name = Names.any_surname()
                else:
                    name = Names.a_place_name()
        else:
            street_type = 'Avenue'
            if random.random() < CONFIG.chance_avenue_gets_numbered_name:
                name = ordinal
            else:
                if random.random() < 0.5:
                    name = Names.any_surname()
                else:
                    name = Names.a_place_name()
        name = "{0} {1}".format(name, street_type)
        return name

    def __str__(self):
        """Return string representation."""
        return self.name


class Parcel(object):
    """A collection of between zero and four contiguous lots in a city."""

    counter = 0

    def __init__(self, street, number, coords):
        """Initialize a Parcel object."""
        self.id = Parcel.counter
        Parcel.counter += 1
        self.street = street
        self.number = number
        self.lots = []
        self.neighbors = []
        self.coords = coords

    @staticmethod
    def determine_house_numbering(parcel_number, side_of_street):
        """Devise an appropriate house numbering scheme given the number of buildings on the parcel."""
        n_buildings = CONFIG.n_buildings_per_parcel+1
        house_numbers = []
        house_number_increment = int(100.0 / n_buildings)
        even_or_odd = 0 if side_of_street == "E" or side_of_street == "N" else 1
        for i in xrange(n_buildings):
            base_house_number = (i * house_number_increment) - 1
            house_number = base_house_number + int(random.random() * house_number_increment)
            if house_number % 2 == (1-even_or_odd):
                house_number += 1
            if house_number < 1+even_or_odd:
                house_number = 1+even_or_odd
            elif house_number > 98+even_or_odd:
                house_number = 98+even_or_odd
            house_number += parcel_number
            house_numbers.append(house_number)
        return house_numbers

    def add_neighbor(self, other):
        self.neighbors.append(other)


class Block(object):
    """A city block in the conventional sense, e.g., the 400 block of Hennepin Ave."""

    def __init__(self, number, street):
        """Initialize a block object."""
        self.number = number
        self.street = street
        self.street.blocks.append(self)
        self.lots = []
        self.type = 'block'

    def __str__(self):
        """Return string representation."""
        return "{} block of {}".format(self.number, str(self.street))

    @property
    def buildings(self):
        """Return all the buildings on this block."""
        return [lot.building for lot in self.lots if lot.building]


class Lot(object):
    """A lot on a block in a city, upon which buildings and houses get erected."""

    counter = 0

    def __init__(self, city):
        """Initialize a Lot object."""
        self.id = Lot.counter
        Lot.counter += 1
        self.city = city
        self.streets = []
        self.parcels = []
        self.sides_of_street = []
        self.house_numbers = []  # In the event a business/landmark is erected here, it inherits this
        self.building = None  # Will always be None for Tract
        self.landmark = None  # Will always be None for Lot
        self.positions_in_parcel = []
        self.neighboring_lots = set()  # Gets set by City call to set_neighboring_lots after all lots have been generated
        # These get set by init_generate_address(), which gets called by City
        self.house_number = None
        self.address = None
        self.street_address_is_on = None
        self.parcel_address_is_on = None
        self.index_of_street_address_will_be_on = None
        self.former_buildings = []

    @property
    def population(self):
        """Return the number of people living/working on the lot."""
        if self.building:
            population = len(self.building.residents)
        else:
            population = 0
        return population

    def attribute_parcel(self, parcel, number, side_of_street, position_in_parcel):
        """Attribute to this lot a parcel that it is incident on."""
        self.streets.append(parcel.street)
        self.parcels.append(parcel)
        self.sides_of_street.append(side_of_street)
        self.house_numbers.append(number)
        self.positions_in_parcel.append(position_in_parcel)

    def set_neighboring_lots(self):
        """Set the lots that neighbor this lot."""
        neighboring_lots = set()
        for parcel in self.parcels:
            for lot in parcel.lots:
                if lot is not self:
                    neighboring_lots.add(lot)
        self.neighboring_lots = neighboring_lots

    def init_generate_address(self):
        """Generate an address for this lot that any building constructed on it will inherit.."""
        self.index_of_street_address_will_be_on = random.randint(0, len(self.streets) - 1)
        house_number = self.house_numbers[self.index_of_street_address_will_be_on]
        house_number = int(house_number)
        street = self.streets[self.index_of_street_address_will_be_on]
        self.address = "{} {}, {}, {}".format(house_number, street.name, self.city.name, self.city.state.name)
        self.street_address_is_on = street
        self.parcel_address_is_on = self.parcels[self.index_of_street_address_will_be_on]


class Tract(Lot):
    """A tract of land on multiple parcels in a city, upon which businesses requiring
    extensive land are established.
    """

    def __init__(self, city):
        """Initialize a Lot object."""
        super(Tract, self).__init__(city)