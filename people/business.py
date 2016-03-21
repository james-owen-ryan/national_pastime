import heapq
from occupation import *
from person import PersonExNihilo
from residence import *
from event import Demolition, BusinessConstruction, Hiring, BusinessClosure, LayOff
from utils.errors import NoVacantTractsError
from corpora import Names

# Objects of a business class represents both the company itself and the building
# at which it is headquartered. All business subclasses inherit generic attributes
# and methods from the superclass Business, and each define their own methods as
# appropriate.


# TODO WOULD BE COOL TO IMPLEMENT A REFERENCES SYSTEM, WHERE PROSPECTIVE EMPLOYEES
# SUBMIT THE NAMES AND ADDRESSES OF REFERENCES IN OTHER CITIES FOR WHOM THEY'VE WORKED,
# WHO THEN RETURN A SCORE OR MAYBE JUST A BINARY INDICATION OF THEIR REFERRAL


class Business(object):
    """A business in a city (representing both the notion of a company and its physical building)."""

    def __init__(self, city):
        """Initialize a Business object."""
        print "A new {} is being established in {}".format(self.__class__.__name__, city.name)
        self.id = city.cosmos.current_place_id
        city.cosmos.current_place_id += 1
        config = city.cosmos.config
        self.type = "business"
        self.city = city
        self.city.companies.add(self)
        # 'Demise' specifies a year at which point it is highly likely this business will close
        # down (due to being anachronistic at that point, e.g., a dairy past 1930)
        self.demise = config.business_types_advent_demise_and_minimum_population[self.__class__][1]
        # 'Services' is a tuple specifying the services offered by this business, given its type
        self.services = config.services_provided_by_business_of_type[self.__class__]
        self.founded = city.cosmos.year
        if self.city.vacant_lots or self.__class__ in config.companies_that_get_established_on_tracts:
            self.lot = self._init_choose_vacant_lot()
            demolition_preceding_construction_of_this_business = None
        else:
            # Acquire a lot currently occupied by a home, demolish the home,
            # and then construct this company's building on that lot
            acquired_lot = self._init_acquire_currently_occupied_lot()
            if self.city.businesses_of_type('ConstructionFirm'):
                demolition_company = random.choice(self.city.businesses_of_type('ConstructionFirm'))
            else:
                demolition_company = None
            demolition_preceding_construction_of_this_business = Demolition(
                building=acquired_lot.building, demolition_company=demolition_company
            )
            self.lot = acquired_lot
        self.lot.building = self
        self.held_by = None  # Potentially gets set to holding company by self._init_holding_company()
        # First, hire employees
        self.employees = set()
        self.former_employees = set()
        self.former_owners = []  # Ordered chronologically
        if self.__class__ in config.public_company_types:  # Hospital, police station, fire station, etc.
            self.public, self.private = True, False
            self.owner = None
            self.founder = None
        elif self.__class__.__name__ == "HoldingCompany":
            self.public, self.private = False, True
            self.owner = self._init_set_and_get_owner_occupation_and_handle_holding_company_stuff(owner=self.owner)
        else:
            self.public, self.private = False, True
            owner = self._init_determine_who_is_starting_this_business()
            self.owner = self._init_set_and_get_owner_occupation_and_handle_holding_company_stuff(owner=owner)
        self._init_hire_initial_employees()
        # Also set the vacancies this company will initially have that may get filled
        # up gradually by people seeking employment (most often, this will be kids who
        # grow up and are ready to work and people who were recently laid off)
        self.supplemental_vacancies = {
            'day': list(config.initial_job_vacancies[self.__class__]['supplemental day']),
            'night': list(config.initial_job_vacancies[self.__class__]['supplemental night'])
        }
        if self.__class__ not in config.companies_that_get_established_on_tracts:
            # Determine who will attempt to contract an architect
            decision_maker = self.city.mayor if self.public else self.owner.person
            # Try to find an architect -- if you can't, you'll have to build it yourself
            architect = decision_maker.contract_person_of_certain_occupation(
                city=city, occupation_in_question=Architect
            )
            architect = None if not architect else architect.occupation
            self.construction = BusinessConstruction(subject=decision_maker, business=self, architect=architect)
            # If a demolition of an earlier building preceded the construction of this business,
            # attribute our new BusinessConstruction object as the .reason attribute for that
            # Demolition attribute
            if demolition_preceding_construction_of_this_business:
                demolition_preceding_construction_of_this_business.reason = self.construction
        # Set address
        lot = self.lot
        self.address = lot.address
        self.house_number = lot.house_number
        self.street_address_is_on = lot.street_address_is_on
        self.block = lot.block
        # Choose a name for this business
        self.name = None
        while not self.name or any(
            # If this is a new holding company, its newly held company will not yet have a name, so
            # that's why we have to include the 'hasattr(c, 'name')' snippet in this generator
            c for c in self.city.companies if c is not self and hasattr(c, 'name') and c.name == self.name
        ):
            self._init_get_named()
        # Set miscellaneous attributes
        self.people_here_now = set()
        self.demolition = None  # Potentially gets set by event.Demolition.__init__()
        self.out_of_business = False  # Potentially gets changed by go_out_of_business()
        self.closure = None  # BusinessClosure object itself
        self.closed = None  # Year closed

    def __str__(self):
        """Return string representation."""
        if not self.out_of_business:
            return "{}, {}".format(self.name, self.address)
        else:
            return "{}, {} ({}-{})".format(self.name, self.address, self.founded, self.closed)

    def _init_determine_who_is_starting_this_business(self):
        """Find someone who has experience in the given industry to start the new business."""
        config = self.city.cosmos.config
        business_type = self.__class__.__name__
        # If the business isn't public, search for employees at nearby businesses of
        # the same type who would thus have some relevant experience
        if self.__class__ in config.business_types_that_may_be_conglomerated_under_holding_companies:
            potential_new_owners = set()
            # Collect all people working at businesses like this one in town
            businesses_of_this_type_in_town = self.city.businesses_of_type(business_type=business_type)
            for business in businesses_of_this_type_in_town:
                potential_new_owners |= {e for e in business.employees if e.years_experience}
            # Potentially collect similar employees in other nearby cities
            for city in self.city.nearest_cities:
                # [Just throwing something together here] -- TODO MAKE THIS TUNABLE IN CONFIG.PY
                if random.random() < 0.8 / (self.city.nearest_cities.index(city)+1):
                    businesses_of_this_type_in_that_city = city.businesses_of_type(business_type=business_type)
                    for business in businesses_of_this_type_in_that_city:
                        potential_new_owners |= {e for e in business.employees if e.years_experience}
        else:
            potential_new_owners = set()
        # Select the person most qualified/likely to start a new business
        if potential_new_owners:
            new_owner = self._init_select_owner(potential_new_owners=potential_new_owners)
        else:
            # Just generate someone
            new_owner = PersonExNihilo(
                cosmos=self.city.cosmos, job_opportunity_impetus=Owner, spouse_already_generated=None
            )
        return new_owner

    @staticmethod
    def _init_select_owner(potential_new_owners):
        """Score someone for the likelihood that they would start a new business."""
        scores = {}
        for potential_new_owner in potential_new_owners:
            openness_to_experience_component = 2.01 + potential_new_owner.person.personality.o
            neuroticism_component = 1.01 + potential_new_owner.person.personality.n
            personality_component = openness_to_experience_component + neuroticism_component
            score = potential_new_owner.person.work_experience * personality_component
            scores[potential_new_owner] = score
        new_owner = max(scores)
        new_owner = new_owner.person
        return new_owner

    def _init_set_and_get_owner_occupation_and_handle_holding_company_stuff(self, owner):
        """Set the owner of this new company's occupation to Owner (or other appropriate proprietor occupation)."""
        # The order really matters here -- see hire() below; first, get the proper occupation class
        # for an owner of a business of this type (e.g., the owner of a farm is a Farmer, not an Owner)
        occupation_class_for_owner_of_this_type_of_business = (
            self.city.cosmos.config.owner_occupations_for_each_business_type[self.__class__]
        )
        new_owner_occupation = occupation_class_for_owner_of_this_type_of_business(
            person=owner, company=self, shift="day"
        )
        hiring = Hiring(subject=owner, company=self, occupation=new_owner_occupation)
        if not owner.occupation:
            owner.occupation = new_owner_occupation
        else:
            if owner.occupation.__class__.__name__ == "Magnate":
                self.get_held_by_holding_company(holding_company=owner.occupation.company)
            elif owner.occupation is owner.occupation.company.owner:
                # The owner of this company already owns another company, but does not
                # yet own a holding company, so instantiate a holding company and then
                # instantiate a Magnate occupation for the owner to now have. Currently,
                # the new holding company will be in the city the owner already lives in,
                # but this could be changed as long as the owner potentially moving to the
                # city that this company is in gets handled)
                if not owner.city:
                    problem_snippet = "{} is a problem for a reason explained at Business.167".format(owner)
                    self.city.cosmos.problems.append(problem_snippet)
                holding_company = HoldingCompany(city=owner.city, magnate=owner)
                self.get_held_by_holding_company(holding_company=holding_company)
            else:
                # This is a first-time owner who prior held another position, so terminate
                # that prior occupation
                owner.occupation.terminate(reason=hiring)
                owner.occupation = new_owner_occupation
        # Lastly, if the person was hired from outside the city, have them move to it,
        # unless they are a Magnate, in which case they can stay in their home city and
        # own the company from there
        if owner.occupation.__class__.__name__ != "Magnate":
            if owner.city is not self.city:
                # If they are a PersonExNihilo, we need to include their family in
                # a forced_cohort, because this person will not yet have a nuclear_family
                # due to not having a city yet
                if not owner.city:
                    family_members = {owner}
                    if owner.spouse:
                        family_members.add(owner.spouse)
                    family_members |= owner.kids
                    forced_cohort = family_members
                else:
                    forced_cohort = set()
                owner.move_to_new_city(city=self.city, reason=hiring, forced_cohort=forced_cohort)
        return new_owner_occupation

    def _init_get_named(self):
        """Get named by the owner of this building (the client for which it was constructed)."""
        config = self.city.cosmos.config
        class_to_company_name_component = {
            ApartmentComplex: 'Apartments',
            Bank: 'Bank',
            Barbershop: 'Barbershop',
            BusDepot: 'Bus Depot',
            CityHall: 'City Hall',
            ConstructionFirm: 'Construction',
            DayCare: 'Day Care',
            OptometryClinic: 'Optometry',
            FireStation: 'Fire Dept.',
            Hospital: 'Hospital',
            Hotel: 'Hotel',
            LawFirm: 'Law Offices of',
            PlasticSurgeryClinic: 'Cosmetic Surgery Clinic',
            PoliceStation: 'Police Dept.',
            RealtyFirm: 'Realty',
            Restaurant: 'Restaurant',
            School: 'K-12 School',
            Supermarket: 'Grocers',
            TattooParlor: 'Tattoo',
            TaxiDepot: 'Taxi',
            University: 'University',
            Cemetery: 'Cemetery',
            Park: 'Park',
            Bakery: 'Baking Co.',
            BlacksmithShop: 'Blacksmith Shop',
            Brewery: 'Brewery',
            ButcherShop: 'Butcher Shop',
            CandyStore: 'Candy Store',
            CarpentryCompany: 'Carpentry',
            ClothingStore: 'Clothing Co.',
            CoalMine: 'Coal Mine',
            Dairy: 'Dairy',
            Deli: 'Delicatessen',
            DentistOffice: 'Dentistry',
            DepartmentStore: 'Department Store',
            Diner: 'Diner',
            Distillery: 'Distillery',
            DrugStore: 'Drug Store',
            Farm: 'family farm',
            Foundry: 'Foundry',
            FurnitureStore: 'Furniture Co.',
            GeneralStore: 'General Store',
            GroceryStore: 'Groceries',
            HardwareStore: 'Hardware Co.',
            Inn: 'Inn',
            InsuranceCompany: 'Insurance Co.',
            JeweleryShop: 'Jewelry',
            PaintingCompany: 'Painting',
            Pharmacy: 'Pharmacy',
            PlumbingCompany: 'Plumbing Co.',
            Quarry: 'Rock Quarry',
            ShoemakerShop: 'Shoes',
            TailorShop: 'Tailoring',
            Tavern: 'Tavern',
        }
        classes_that_get_special_names = (
            CityHall, FireStation, Hospital, PoliceStation, School, Cemetery, LawFirm, Bar,
            Restaurant, University, Park, Farm
        )
        name = None
        if self.__class__ not in classes_that_get_special_names:
            if random.random() < config.chance_company_gets_named_after_owner:
                prefix = self.owner.person.last_name
            elif random.random() < 0.5:
                prefix = self.street_address_is_on.name
            elif random.random() < 0.5:
                prefix = self.city.name
            else:  # Duct tape -- we need more variation here
                prefix = "Generic"
            name = "{0} {1}".format(prefix, class_to_company_name_component[self.__class__])
        elif self.__class__ in (CityHall, FireStation, Hospital, PoliceStation, School, Cemetery):
            name = "{0} {1}".format(self.city.name, class_to_company_name_component[self.__class__])
        elif self.__class__ is Farm:
            name = "{}'s farm".format(self.owner.person.name)
            if any(c for c in self.city.companies if c.name == name):
                name = "{}'s farm".format(self.owner.person.full_name)
        elif self.__class__ is LawFirm:
            associates = [e for e in self.employees if e.__class__ is Lawyer]
            suffix = "{0} & {1}".format(
                ', '.join(a.person.last_name for a in associates[:-1]), associates[-1].person.last_name
            )
            name = "{0} {1}".format(class_to_company_name_component[LawFirm], suffix)
        elif self.__class__ is Bar:
            name = Names.a_bar_name()
            # if self.city.cosmos.year > 1968:
            #     # Choose a name from the corpus of bar names
            #     name = Names.a_bar_name()
            # else:
            #     name = self.owner.person.last_name + "'s"
        elif self.__class__ is Restaurant:
            name = Names.a_restaurant_name()
            # if self.city.cosmos.year > 1968:
            #     # Choose a name from the corpus of restaurant names
            #     name = Names.a_restaurant_name()
            # else:
            #     name = self.owner.person.last_name + "'s"
        elif self.__class__ is University:
            name = "{} College".format(self.city.name)
        elif self.__class__ is Park:
            if self.lot.former_buildings:
                business_here_previously = list(self.lot.former_buildings)[-1]
                owner = business_here_previously.owner.person
                if business_here_previously.__class__ is Farm:
                    x = random.random()
                    if x < 0.25:
                        name = '{} {} Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.5:
                        name = '{} Farm Park'.format(
                            owner.last_name
                        )

                    elif x < 0.75:
                        name = '{} Park'.format(
                            owner.last_name
                        )
                    elif x < 0.8:
                        name = 'Old Farm Park'
                    elif x < 0.9:
                        name = '{} {} Memorial Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.97:
                        name = '{} Memorial Park'.format(
                            owner.last_name
                        )
                    else:
                        name = '{} Park'.format(self.city.name)
                elif business_here_previously.__class__ is Quarry:
                    x = random.random()
                    if x < 0.25:
                        name = '{} {} Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.5:
                        name = '{} Park'.format(
                            business_here_previously.name
                        )

                    elif x < 0.75:
                        name = '{} Park'.format(
                            owner.last_name
                        )
                    elif x < 0.8:
                        name = 'Old Quarry Park'
                    elif x < 0.9:
                        name = '{} {} Memorial Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.97:
                        name = 'Quarry Park'.format(
                            owner.last_name
                        )
                    else:
                        name = '{} Park'.format(self.city.name)
                elif business_here_previously.__class__ is CoalMine:
                    x = random.random()
                    if x < 0.25:
                        name = '{} {} Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.5:
                        name = '{} Park'.format(
                            business_here_previously.name
                        )

                    elif x < 0.75:
                        name = '{} Park'.format(
                            owner.last_name
                        )
                    elif x < 0.8:
                        name = 'Old Mine Park'
                    elif x < 0.9:
                        name = '{} {} Memorial Park'.format(
                            owner.first_name, owner.last_name
                        )
                    elif x < 0.97:
                        name = 'Coal Mine Park'.format(
                            owner.last_name
                        )
                    elif x < 0.99:
                        name = 'Coal Park'.format(
                            owner.last_name
                        )
                    else:
                        name = '{} Park'.format(self.city.name)
            else:
                name = '{} Park'.format(Names.an_english_surname())
        if not name:
            raise Exception("A company of class {} was unable to be named.".format(self.__class__.__name__))
        self.name = name

    def _init_hire_initial_employees(self):
        """Fill all the positions that are vacant at the time of this company forming."""
        # Hire employees for the day shift
        for vacant_position in self.city.cosmos.config.initial_job_vacancies[self.__class__]['day']:
            self.hire(occupation_of_need=vacant_position, shift="day")
        # Hire employees for the night shift
        for vacant_position in self.city.cosmos.config.initial_job_vacancies[self.__class__]['night']:
            self.hire(occupation_of_need=vacant_position, shift="night")

    def _init_acquire_currently_occupied_lot(self):
        """If there are no vacant lots in town, acquire a lot and demolish the home currently on it."""
        lot_scores = self._rate_all_occupied_lots()
        if len(lot_scores) >= 3:
            # Pick from top three
            top_three_choices = heapq.nlargest(3, lot_scores, key=lot_scores.get)
            if random.random() < 0.6:
                choice = top_three_choices[0]
            elif random.random() < 0.9:
                choice = top_three_choices[1]
            else:
                choice = top_three_choices[2]
        elif lot_scores:
            choice = max(lot_scores)
        else:
            raise Exception("A company attempted to secure an *occupied* lot in town but somehow could not.")
        return choice

    def _rate_all_occupied_lots(self):
        """Rate all lots currently occupied by homes for their desirability as business locations."""
        lots_with_homes_on_them = (l for l in self.city.lots if l.building and l.building.type == 'residence')
        scores = {}
        for lot in lots_with_homes_on_them:
            scores[lot] = self._rate_potential_lot(lot=lot)
        return scores

    def _init_choose_vacant_lot(self):
        """Choose a vacant lot on which to build the company building.

        Currently, a company scores all the vacant lots in town and then selects
        one of the top three. TODO: Probabilistically select from all lots using
        the scores to derive likelihoods of selecting each.
        """
        if self.__class__ in self.city.cosmos.config.companies_that_get_established_on_tracts:
            vacant_lots_or_tracts = self.city.vacant_tracts
        else:
            vacant_lots_or_tracts = self.city.vacant_lots
        assert vacant_lots_or_tracts, (
            "{} is attempting to found a {}, but there's no vacant lots/tracts in {}".format(
                self.owner.person.name, self.__class__.__name__, self.city.name
            )
        )
        lot_scores = self._rate_all_vacant_lots()
        if len(lot_scores) >= 3:
            # Pick from top three
            top_three_choices = heapq.nlargest(3, lot_scores, key=lot_scores.get)
            if random.random() < 0.6:
                choice = top_three_choices[0]
            elif random.random() < 0.9:
                choice = top_three_choices[1]
            else:
                choice = top_three_choices[2]
        elif lot_scores:
            choice = max(lot_scores)
        else:
            raise Exception("A company attempted to secure a lot in town when in fact none are vacant.")
        return choice

    def _rate_all_vacant_lots(self):
        """Rate all vacant lots for the desirability of their locations.
        """
        if self.__class__ in self.city.cosmos.config.companies_that_get_established_on_tracts:
            vacant_lots_or_tracts = self.city.vacant_tracts
        else:
            vacant_lots_or_tracts = self.city.vacant_lots
        scores = {}
        for lot in vacant_lots_or_tracts:
            scores[lot] = self._rate_potential_lot(lot=lot)
        return scores

    def _rate_potential_lot(self, lot):
        """Rate a vacant lot for the desirability of its location.

        By this method, a company appraises a vacant lot in the city for how much they
        would like to build there, given considerations to its proximity to downtown,
        proximity to other businesses of the same type, and to the number of people living
        near the lot.
        """
        score = 0
        # As (now) the only criterion, rate lots according to their distance
        # from downtown; this causes a downtown commercial area to naturally emerge
        score -= self.city.dist_from_downtown(lot)
        return score

    @property
    def locked(self):
        """Return True if the entrance to this building is currently locked, else false."""
        locked = False
        # Apartment complexes are always locked
        if self.__class__ is ApartmentComplex:
            locked = True
        # Public institutions, like parks and cemeteries and city hall, are also always locked at night
        if (self.city.cosmos.time_of_day == "night" and
                self.__class__ in self.city.cosmos.config.public_places_closed_at_night):
            locked = True
        # Other businesses are locked only when no one is working, or
        # at night when only a janitor is working
        else:
            if not self.working_right_now:
                locked = True
            elif not any(e for e in self.working_right_now if e[0] != 'janitor'):
                locked = True
        return locked

    @property
    def residents(self):
        """Return the employees that work here.

         This is meant to facilitate a Lot reasoning over its population and the population
         of its local area. This reasoning is needed so that developers can decide where to
         build businesses. For all businesses but ApartmentComplex, this just returns the
         employees that work at this building (which makes sense in the case of, e.g., building
         a restaurant nearby where people work); for ApartmentComplex, this is overridden
         to return the employees that work there and also the people that live there.
         """
        return set([employee.person for employee in self.employees])

    @property
    def working_right_now(self):
        people_working = [p for p in self.people_here_now if p.routine.working]
        return [(p.occupation.vocation, p) for p in people_working]

    @property
    def day_shift(self):
        """Return all employees who work the day shift here."""
        day_shift = set([employee for employee in self.employees if employee.shift == "day"])
        return day_shift

    @property
    def night_shift(self):
        """Return all employees who work the night shift here."""
        night_shift = set([employee for employee in self.employees if employee.shift == "night"])
        return night_shift

    @property
    def sign(self):
        """Return a string representing this business's sign."""
        if self.__class__ in self.city.cosmos.config.public_company_types:
            return self.name
        elif self.city.cosmos.year - self.founded > 8:
            return '{}, since {}'.format(self.name, self.founded)
        else:
            return self.name

    def _find_candidate(self, occupation_of_need):
        """Find the best available candidate to fill the given occupation of need."""
        # If you have someone working here who is an apprentice, hire them outright
        if (self.city.cosmos.config.job_levels[occupation_of_need] > self.city.cosmos.config.job_levels[Apprentice] and
                any(e for e in self.employees if e.__class__ == Apprentice and e.years_experience > 0)):
            selected_candidate = next(
                e for e in self.employees if e.__class__ == Apprentice and e.years_experience > 0
            ).person
        else:
            job_candidates_in_town = self._assemble_job_candidates(
                city=self.city, occupation_of_need=occupation_of_need
            )
            if job_candidates_in_town:
                candidate_scores = self._rate_all_job_candidates(candidates=job_candidates_in_town)
                selected_candidate = self._select_candidate(
                    candidate_scores=candidate_scores, occupation_of_need=occupation_of_need
                )
            else:
                selected_candidate = self._find_candidate_from_another_city(occupation_of_need=occupation_of_need)
        return selected_candidate

    def hire(self, occupation_of_need, shift, to_replace=None,
             fills_supplemental_job_vacancy=False, selected_candidate=None, hired_as_a_favor=False):
        """Hire the given selected candidate."""
        # If no candidate has yet been selected, scour the job market to find one
        if not selected_candidate:
            selected_candidate = self._find_candidate(occupation_of_need=occupation_of_need)
        # Instantiate the new occupation -- this means that the subject may
        # momentarily have two occupations simultaneously
        new_position = occupation_of_need(person=selected_candidate, company=self, shift=shift)
        # If this person is being hired to replace a now-former employee, attribute
        # this new position as the successor to the former one
        if to_replace:
            to_replace.succeeded_by = new_position
            new_position.preceded_by = to_replace
            # If this person is being hired to replace the owner, they are now the owner --
            # TODO not all businesses should transfer ownership using the standard hiring process
            if to_replace is self.owner:
                self.owner = new_position
        # Now instantiate a Hiring object to hold data about the hiring
        hiring = Hiring(subject=selected_candidate, company=self, occupation=new_position)
        # Now terminate the person's former occupation, if any (which may cause
        # a hiring chain and this person's former position goes vacant and is filled,
        # and so forth); this has to happen after the new occupation is instantiated, or
        # else they may be hired to fill their own vacated position, which will cause problems
        # [Actually, this currently wouldn't happen, because lateral job movement is not
        # possible given how companies assemble job candidates, but it still makes more sense
        # to have this person put in their new position *before* the chain sets off, because it
        # better represents what really is a domino-effect situation)
        if selected_candidate.occupation:
            selected_candidate.occupation.terminate(reason=hiring)
        # Now you can set the employee's occupation to the new occupation (had you done it
        # prior, either here or elsewhere, it would have terminated the occupation that this
        # person was just hired for, triggering endless recursion as the company tries to
        # fill this vacancy in a Sisyphean nightmare)
        selected_candidate.occupation = new_position
        # If the new hire is now the new owner of this company, attribute as much
        if occupation_of_need is Owner:  # JOR 03-19-2016: This block seems pretty brittle/redundant at this point
            self.owner = new_position
        # If this is a law firm and the new hire is a lawyer, change the name
        # of this firm to include the new lawyer's name
        if self.__class__ == "LawFirm" and new_position == Lawyer:
            self._init_get_named()
        # If this position filled one of this company's "supplemental" job vacancies (see
        # config.py), then remove an instance of this position from that list
        if fills_supplemental_job_vacancy:
            self.supplemental_vacancies[shift].remove(occupation_of_need)
            # This position doesn't have to be refilled immediately if terminated, so
            # attribute to it that it is supplemental
            selected_candidate.occupation.supplemental = True
        # Being hired as a favor means this business created an additional position
        # beyond all their supplemental positions (because those were all filled)
        # specifically to facilitate the hiring of this person (who will have been
        # a family member of this company's owner); because of this, when this position
        # terminates we don't want to add it back to the supplemental vacancies of this
        # company, because they really don't need to refill the position ever and if they
        # do, it yields rampant population growth due to there being way too many jobs
        # in town
        selected_candidate.occupation.hired_as_favor = hired_as_a_favor
        # Lastly, if the person was hired from outside the city, have them move to it
        if selected_candidate.city is not self.city:
            selected_candidate.move_to_new_city(city=self.city, reason=hiring)

    def _select_candidate(self, candidate_scores, occupation_of_need):
        """Select a person to serve in a certain occupational capacity."""
        sorted_candidates = heapq.nlargest(len(candidate_scores), candidate_scores, key=candidate_scores.get)
        try:
            chosen_candidate = next(
                candidate for candidate in sorted_candidates if candidate.accept_job_offer(
                    city=self.city, offered_job=occupation_of_need
                )
            )
        except StopIteration:
            # Just generate someone
            chosen_candidate = PersonExNihilo(
                cosmos=self.city.cosmos, job_opportunity_impetus=occupation_of_need, spouse_already_generated=None
            )
        return chosen_candidate

    def _find_candidate_from_another_city(self, occupation_of_need):
        """Find someone from another city to move here for this job."""
        candidates_from_other_cities = set()
        # Collect candidates from nearby overpopulated cities
        nearby_overpopulated_cities = [c for c in self.city.nearest_cities if c.overpopulated]
        for city in nearby_overpopulated_cities:
            candidates_from_other_cities |= self._assemble_job_candidates(
                city=city, occupation_of_need=occupation_of_need
            )
        # Collect a few additional candidates from all across the country
        for city in self.city.state.country.cities:
            if random.random() < 0.02:
                candidates_from_other_cities |= self._assemble_job_candidates(
                    city=city, occupation_of_need=occupation_of_need
                )
        candidate_scores = self._rate_all_job_candidates(
            candidates=candidates_from_other_cities, naming_new_owner=True if occupation_of_need is Owner else False
        )
        selected_candidate = self._select_candidate(
            candidate_scores=candidate_scores, occupation_of_need=occupation_of_need
        )
        return selected_candidate

    def _rate_all_job_candidates(self, candidates, naming_new_owner=False):
        """Rate all job candidates."""
        scores = {}
        for candidate in candidates:
            scores[candidate] = self._rate_job_candidate(person=candidate, naming_new_owner=naming_new_owner)
        return scores

    def _rate_job_candidate(self, person, naming_new_owner=False):
        """Rate a job candidate, given an open position and owner biases."""
        config = self.city.cosmos.config
        decision_maker = self.owner.person if self.owner else self.city.mayor
        score = 0
        if naming_new_owner:
            if person in decision_maker.sons:
                score += config.preference_to_name_owners_son_new_owner
        if person in self.employees:
            score += config.preference_to_hire_from_within_company
        if person in decision_maker.immediate_family:
            score += config.preference_to_hire_immediate_family
        elif person in decision_maker.extended_family:
            score += config.preference_to_hire_extended_family
        if person in decision_maker.friends:
            score += config.preference_to_hire_friend
        elif person in decision_maker.acquaintances:
            score += config.preference_to_hire_acquaintance
        if person in decision_maker.enemies:
            score += config.dispreference_to_hire_enemy
        if person.occupation:
            score *= person.occupation.level
        else:
            score *= config.unemployment_occupation_level
        return score

    def _assemble_job_candidates(self, city, occupation_of_need):
        """Assemble a group of job candidates for an open position."""
        candidates = set()
        # Consider people that already work in this city -- this will subsume
        # reasoning over people that could be promoted from within this company
        for company in city.companies:
            for position in company.employees:
                person_is_qualified = self.check_if_person_is_qualified_for_the_position(
                    candidate=position.person, occupation_of_need=occupation_of_need
                )
                if person_is_qualified:
                    candidates.add(position.person)
        # Consider unemployed (mostly young) people if they are qualified
        for person in city.unemployed:
            person_is_qualified = self.check_if_person_is_qualified_for_the_position(
                candidate=person, occupation_of_need=occupation_of_need
            )
            if person_is_qualified:
                candidates.add(person)
        return candidates

    def check_if_person_is_qualified_for_the_position(self, candidate, occupation_of_need):
        """Check if the job candidate is qualified for the position you are hiring for."""
        config = self.city.cosmos.config
        qualified = False
        level_of_this_position = config.job_levels[occupation_of_need]
        # Make sure they are not already at a job of higher prestige; people that
        # used to work higher-level jobs may stoop back to lower levels if they are
        # now out of work
        if candidate.occupation:
            candidate_job_level = candidate.occupation.level
        elif candidate.occupations:
            candidate_job_level = max(candidate.occupations, key=lambda o: o.level).level
        else:
            candidate_job_level = 0
        if not (candidate.occupation and candidate_job_level >= level_of_this_position):
            # Make sure they have a college degree if one is required to have this occupation
            if occupation_of_need in self.city.cosmos.config.occupations_requiring_college_degree:
                if candidate.college_graduate:
                    qualified = True
            else:
                qualified = True
        # Make sure the candidate meets the essential preconditions for this position;
        # note: most of these preconditions are meant to maintain basic historically accuracy
        if not config.employable_as_a[occupation_of_need](applicant=candidate):
            qualified = False
        # Lastly, make sure they have been at their old job for at least a year,
        # if they had one
        if candidate.occupation and candidate.occupation.years_experience < 1:
            qualified = False
        # As an extra check, make sure they're not dead or retired; this is necessary,
        # because this hiring procedure may be filling the position of a person who
        # has multiple occupations that have not all been terminated yet, and we don't
        # want the very person who holds these multiple positions to be hired to fill
        # one of them
        if candidate.dead or candidate.retired:
            # Thought, though: it might actually be cool to have companies attempt to
            # coax people out of retirement
            qualified = False
        return qualified

    def get_feature(self, feature_type):
        """Return this person's feature of the given type."""
        if feature_type == "business block":
            return str(self.block)
        elif feature_type == "business address":
            return self.address

    def go_out_of_business(self, reason):
        """Cease operation of this business."""
        BusinessClosure(business=self, reason=reason)

    def _get_bulldozed(self):
        """Raze the building that this business operates out of.

        TODO: Reify the building itself, so that it can be purchased by a new company who
        wishes to operate out of it.
        """
        self.lot.building = None

    def get_held_by_holding_company(self, holding_company):
        """Get held by a holding company, usually when the owner of this company starts another company."""
        self.held_by = holding_company
        self.owner = holding_company.owner
        holding_company.holdings.append(self)


class HoldingCompany(Business):
    """A business that owns other businesses."""

    def __init__(self, city, magnate):
        """Initialize a HoldingCompany object."""
        self.owner = magnate
        self.holdings = []
        self.former_holdings = []
        super(HoldingCompany, self).__init__(city)

    def _init_get_named(self):
        """Get named by the owner of this building (the client for which it was constructed)."""
        name = "{}.{}. {} Holdings".format(
            self.owner.person.first_name[0], self.owner.person.middle_name[0], self.owner.person.last_name
        )
        while any(c for c in self.city.companies if c is not self and hasattr(c, 'name') and c.name == self.name):
            i = 2
            name += " {}".format(i)
        self.name = name

    def _init_set_and_get_owner_occupation_and_handle_holding_company_stuff(self, owner):
        """Set the owner of this new company's occupation to Owner."""
        magnate_occupation = Magnate(person=owner, company=self, shift="day")
        Hiring(subject=owner, company=self, occupation=magnate_occupation)
        owner.occupation = magnate_occupation
        return magnate_occupation

    def set_new_magnate(self, new_magnate):
        """Set a new magnate who is succeeding a departing magnate."""
        for company in self.holdings:
            old_owner_occupation = company.owner
            occupation_class_for_owner_of_this_type_of_business = (
                self.city.cosmos.config.owner_occupations_for_each_business_type[company.__class__]
            )
            new_owner_occupation = occupation_class_for_owner_of_this_type_of_business(
                person=new_magnate, company=company, shift="day"
            )
            company.owner = new_owner_occupation
            # Set preceded_by and succeeded_by attributes
            old_owner_occupation.succeeded_by = new_owner_occupation
            new_owner_occupation.preceded_by = old_owner_occupation
            Hiring(subject=new_magnate, company=company, occupation=new_owner_occupation)
            # new_magnate.occupations.append(new_owner_occupation)  # TODO DELETE IF NOT CAUSING PROBLEMS
        old_magnate_occupation = self.owner
        new_magnate_occupation = Magnate(person=new_magnate, company=self, shift="day")
        # Set preceded_by and succeeded_by attributes
        old_magnate_occupation.succeeded_by = new_magnate_occupation
        new_magnate_occupation.preceded_by = old_magnate_occupation
        hiring = Hiring(subject=new_magnate, company=self, occupation=new_magnate_occupation)
        if not new_magnate.occupation:
            new_magnate.occupation = new_magnate_occupation
        else:
            new_magnate.occupation.terminate(reason=hiring)
            new_magnate.occupation = new_magnate_occupation
        self.owner = new_magnate_occupation
        # Lastly, if the person was hired from outside the city, have them move to it
        if new_magnate.city is not self.city:
            new_magnate.move_to_new_city(city=self.city, reason=hiring)
        return new_magnate_occupation

    def reassess_status_as_holding_company(self):
        """Check whether this company still owns multiple companies; if it doesn't, go out of business."""
        if len(self.holdings) < 2:
            most_recent_business_closure = self.former_holdings[-1].closure
            self.go_out_of_business(reason=most_recent_business_closure)


class ApartmentComplex(Business):
    """An apartment complex."""

    def __init__(self, city):
        """Initialize an ApartmentComplex object."""
        # Have to do this to allow .residents to be able to return a value before
        # this object has its units attributed -- this is because new employees
        # hired to work here may actually move in during the larger init() call
        self.units = []
        super(ApartmentComplex, self).__init__(city)
        self.units = self._init_apartment_units()

    def _init_apartment_units(self):
        """Instantiate objects for the individual units in this apartment complex."""
        config = self.city.cosmos.config
        n_units_to_build = random.randint(
            config.number_of_apartment_units_in_new_complex_min,
            config.number_of_apartment_units_in_new_complex_max
        )
        if n_units_to_build % 2 != 0:
            # Make it a nice even number
            n_units_to_build -= 1
        apartment_units = []
        for i in xrange(n_units_to_build):
            unit_number = i + 1
            apartment_units.append(
                Apartment(apartment_complex=self, lot=self.lot, unit_number=unit_number)
            )
        return apartment_units

    @property
    def residents(self):
        """Return the residents that live here."""
        residents = set()
        for unit in self.units:
            residents |= unit.residents
        return residents

    def expand(self):
        """Add two extra units in this complex.

        The impetus for this method being called is to accommodate a new person in town seeking housing.
        Since apartment complexes in this simulation always have an even number of units, we add two extra
        ones to maintain that property.
        """
        currently_highest_unit_number = max(self.units, key=lambda u: u.unit_number).unit_number
        next_unit_number = currently_highest_unit_number + 1
        self.units.append(
            Apartment(apartment_complex=self, lot=self.lot, unit_number=next_unit_number)
        )
        self.units.append(
            Apartment(apartment_complex=self, lot=self.lot, unit_number=next_unit_number+1)
        )


class Bakery(Business):
    """A bakery."""

    def __init__(self, city):
        """Initialize a Bakery object."""
        super(Bakery, self).__init__(city)


class Bank(Business):
    """A bank."""

    def __init__(self, city):
        """Initialize a Bank object."""
        super(Bank, self).__init__(city)


class Bar(Business):
    """A bar."""

    def __init__(self, city):
        """Initialize a Restaurant object."""
        super(Bar, self).__init__(city)


class Barbershop(Business):
    """A barbershop."""

    def __init__(self, city):
        """Initialize a Barbershop object."""
        super(Barbershop, self).__init__(city)


class BlacksmithShop(Business):
    """A blacksmith business."""

    def __init__(self, city):
        """Initialize a BlacksmithShop object."""
        super(BlacksmithShop, self).__init__(city)


class Brewery(Business):
    """A brewery."""

    def __init__(self, city):
        """Initialize a Brewery object."""
        super(Brewery, self).__init__(city)


class BusDepot(Business):
    """A bus depot."""

    def __init__(self, city):
        """Initialize a BusDepot object."""
        super(BusDepot, self).__init__(city)


class ButcherShop(Business):
    """A butcher business."""

    def __init__(self, city):
        """Initialize a ButcherShop object."""
        super(ButcherShop, self).__init__(city)


class CandyStore(Business):
    """A candy store."""

    def __init__(self, city):
        """Initialize a CandyStore object."""
        super(CandyStore, self).__init__(city)


class CarpentryCompany(Business):
    """A carpentry company."""

    def __init__(self, city):
        """Initialize a CarpentryCompany object."""
        super(CarpentryCompany, self).__init__(city)


class Cemetery(Business):
    """A cemetery on a tract in a city."""

    def __init__(self, city):
        """Initialize a Cemetery object."""
        super(Cemetery, self).__init__(city)
        self.city.cemetery = self
        self.plots = {}

    def inter_person(self, person):
        """Inter a new person by assigning them a plot in the graveyard."""
        if not self.plots:
            new_plot_number = 1
        else:
            new_plot_number = max(self.plots) + 1
        self.plots[new_plot_number] = person
        return new_plot_number


class CityHall(Business):
    """The city hall."""

    def __init__(self, city):
        """Initialize a CityHall object.

        @param city: The owner of this business.
        """
        super(CityHall, self).__init__(city)
        self.city.city_hall = self


class ClothingStore(Business):
    """A store that sells clothing only; i.e., not a department store."""

    def __init__(self, city):
        """Initialize a ClothingStore object.

        @param city: The owner of this business.
        """
        super(ClothingStore, self).__init__(city)


class CoalMine(Business):
    """A coal mine."""

    def __init__(self, city):
        """Initialize a ClothingStore object. """
        super(CoalMine, self).__init__(city)


class ConstructionFirm(Business):
    """A construction firm."""

    def __init__(self, city):
        """Initialize an ConstructionFirm object."""
        super(ConstructionFirm, self).__init__(city)

    @property
    def house_constructions(self):
        """Return all house constructions."""
        house_constructions = set()
        for employee in self.employees | self.former_employees:
            if hasattr(employee, 'house_constructions'):
                house_constructions |= employee.house_constructions
        return house_constructions

    @property
    def building_constructions(self):
        """Return all building constructions."""
        building_constructions = set()
        for employee in self.employees | self.former_employees:
            if hasattr(employee, 'building_constructions'):
                building_constructions |= employee.building_constructions
        return building_constructions


class Dairy(Business):
    """A store where milk is sold and from which milk is distributed."""

    def __init__(self, city):
        """Initialize a Dairy object."""
        super(Dairy, self).__init__(city)


class DayCare(Business):
    """A day care center for young children."""

    def __init__(self, city):
        """Initialize a DayCare object."""
        super(DayCare, self).__init__(city)


class Deli(Business):
    """A delicatessen."""

    def __init__(self, city):
        """Initialize a Deli object."""
        super(Deli, self).__init__(city)


class DentistOffice(Business):
    """A dentist office."""

    def __init__(self, city):
        """Initialize a DentistOffice object."""
        super(DentistOffice, self).__init__(city)


class DepartmentStore(Business):
    """A department store."""

    def __init__(self, city):
        """Initialize a DepartmentStore object."""
        super(DepartmentStore, self).__init__(city)


class Diner(Business):
    """A diner."""

    def __init__(self, city):
        """Initialize a Diner object."""
        super(Diner, self).__init__(city)


class Distillery(Business):
    """A whiskey distillery."""

    def __init__(self, city):
        """Initialize a Distillery object."""
        super(Distillery, self).__init__(city)


class DrugStore(Business):
    """A drug store."""

    def __init__(self, city):
        """Initialize a DrugStore object."""
        super(DrugStore, self).__init__(city)


class Farm(Business):
    """A farm on a tract in a city."""

    def __init__(self, city):
        """Initialize a Farm object."""
        super(Farm, self).__init__(city)


class FireStation(Business):
    """A fire station."""

    def __init__(self, city):
        """Initialize an FireStation object."""
        super(FireStation, self).__init__(city)
        self.city.fire_station = self


class Foundry(Business):
    """A metal foundry."""

    def __init__(self, city):
        """Initialize a Foundry object."""
        super(Foundry, self).__init__(city)


class FurnitureStore(Business):
    """A furniture store."""

    def __init__(self, city):
        """Initialize a FurnitureStore object."""
        super(FurnitureStore, self).__init__(city)


class GeneralStore(Business):
    """A general store."""

    def __init__(self, city):
        """Initialize a GeneralStore object."""
        super(GeneralStore, self).__init__(city)


class GroceryStore(Business):
    """A grocery store."""

    def __init__(self, city):
        """Initialize a GroceryStore object."""
        super(GroceryStore, self).__init__(city)


class HardwareStore(Business):
    """A hardware store."""

    def __init__(self, city):
        """Initialize a HardwareStore object."""
        super(HardwareStore, self).__init__(city)


class Hospital(Business):
    """A hospital."""

    def __init__(self, city):
        """Initialize an Hospital object."""
        super(Hospital, self).__init__(city)
        self.city.hospital = self

    @property
    def baby_deliveries(self):
        """Return all baby deliveries."""
        baby_deliveries = set()
        for employee in self.employees | self.former_employees:
            if hasattr(employee, 'baby_deliveries'):
                baby_deliveries |= employee.baby_deliveries
        return baby_deliveries


class Hotel(Business):
    """A hotel."""

    def __init__(self, city):
        """Initialize a Hotel object."""
        super(Hotel, self).__init__(city)


class Inn(Business):
    """An inn."""

    def __init__(self, city):
        """Initialize an Inn object."""
        super(Inn, self).__init__(city)


class InsuranceCompany(Business):
    """An insurance company."""

    def __init__(self, city):
        """Initialize an InsuranceCompany object."""
        super(InsuranceCompany, self).__init__(city)


class JeweleryShop(Business):
    """A jewelry company."""

    def __init__(self, city):
        """Initialize a JeweleryShop object."""
        super(JeweleryShop, self).__init__(city)


class LawFirm(Business):
    """A law firm."""

    def __init__(self, city):
        """Initialize a LawFirm object."""
        super(LawFirm, self).__init__(city)

    def rename_due_to_lawyer_change(self):
        """Rename this company due to the hiring of a new lawyer."""
        partners = [e for e in self.employees if e.__class__ is Lawyer]
        if len(partners) > 1:
            partners_str = "{} & {}".format(
                ', '.join(a.person.last_name for a in partners[:-1]),
                partners[-1].person.last_name
            )
            self.name = "Law Offices of {}".format(partners_str)
        elif partners:
            # If there's only one lawyer at this firm now, have its
            # name be 'Law Offices of [first name] [last name]'
            self.name = "Law Offices of {} {}".format(
                partners[0].person.first_name, partners[0].person.last_name
            )
        else:
            # The only lawyer working here retired or departed the city -- the
            # business will shut down shortly and this will be its final name
            pass

    @property
    def filed_divorces(self):
        """Return all divorces filed through this law firm."""
        filed_divorces = set()
        for employee in self.employees | self.former_employees:
            if hasattr(employee, 'filed_divorces'):
                filed_divorces |= employee.filed_divorces
        return filed_divorces

    @property
    def filed_name_changes(self):
        """Return all name changes filed through this law firm."""
        filed_name_changes = set()
        for employee in self.employees | self.former_employees:
            filed_name_changes |= employee.filed_name_changes
        return filed_name_changes


class OptometryClinic(Business):
    """An optometry clinic."""

    def __init__(self, city):
        """Initialize an OptometryClinic object.

        @param city: The owner of this business.
        """
        super(OptometryClinic, self).__init__(city)


class PaintingCompany(Business):
    """A painting company."""

    def __init__(self, city):
        """Initialize a PaintingCompany object."""
        super(PaintingCompany, self).__init__(city)


class Park(Business):
    """A park on a tract in a city."""

    def __init__(self, city):
        """Initialize a Park object."""
        super(Park, self).__init__(city)


class Pharmacy(Business):
    """A pharmacy."""

    def __init__(self, city):
        """Initialize a Pharmacy object."""
        super(Pharmacy, self).__init__(city)


class PlasticSurgeryClinic(Business):
    """A plastic-surgery clinic."""

    def __init__(self, city):
        """Initialize a PlasticSurgeryClinic object."""
        super(PlasticSurgeryClinic, self).__init__(city)


class PlumbingCompany(Business):
    """A plumbing company."""

    def __init__(self, city):
        """Initialize a PlumbingCompany object."""
        super(PlumbingCompany, self).__init__(city)


class PoliceStation(Business):
    """A police station."""

    def __init__(self, city):
        """Initialize a PoliceStation object."""
        super(PoliceStation, self).__init__(city)
        self.city.police_station = self


class Quarry(Business):
    """A rock quarry."""

    def __init__(self, city):
        """Initialize a Quarry object."""
        super(Quarry, self).__init__(city)


class RealtyFirm(Business):
    """A realty firm."""

    def __init__(self, city):
        """Initialize an RealtyFirm object."""
        super(RealtyFirm, self).__init__(city)

    @property
    def home_sales(self):
        """Return all home sales."""
        home_sales = set()
        for employee in self.employees | self.former_employees:
            if hasattr(employee, 'home_sales'):
                home_sales |= employee.home_sales
        return home_sales


class Restaurant(Business):
    """A restaurant."""

    def __init__(self, city):
        """Initialize a Restaurant object."""
        super(Restaurant, self).__init__(city)


class School(Business):
    """The local K-12 school."""

    def __init__(self, city):
        """Initialize a School object."""
        super(School, self).__init__(city)
        self.city.school = self


class ShoemakerShop(Business):
    """A shoemaker's company."""

    def __init__(self, city):
        """Initialize an ShoemakerShop object.

        @param city: The owner of this business.
        """
        super(ShoemakerShop, self).__init__(city)


class Supermarket(Business):
    """A supermarket on a lot in a city."""

    def __init__(self, city):
        """Initialize an Supermarket object."""
        super(Supermarket, self).__init__(city)


class TailorShop(Business):
    """A tailor."""

    def __init__(self, city):
        """Initialize a TailorShop object."""
        super(TailorShop, self).__init__(city)


class TattooParlor(Business):
    """A tattoo parlor."""

    def __init__(self, city):
        """Initialize a TattooParlor object."""
        super(TattooParlor, self).__init__(city)


class Tavern(Business):
    """A place where alcohol is served in the 19th century, maintained by a barkeeper."""

    def __init__(self, city):
        """Initialize a Tavern object."""
        super(Tavern, self).__init__(city)


class TaxiDepot(Business):
    """A taxi depot."""

    def __init__(self, city):
        """Initialize a TaxiDepot object."""
        super(TaxiDepot, self).__init__(city)


class University(Business):
    """The local university."""

    def __init__(self, city):
        """Initialize a University object."""
        super(University, self).__init__(city)
        self.city.university = self