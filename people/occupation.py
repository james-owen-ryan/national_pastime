import string
import events.major_event
from baseball.manager import Manager as LiteralBaseballManager  # Don't want to squash Manager object here
from baseball.owner import Owner as LiteralBaseballTeamOwner  # Don't want to squash Owner object here
from baseball.scout import Scout
from baseball.commissioner import Commissioner
from baseball.umpire import Umpire


class Occupation(object):
    """An occupation at a business in a city."""

    def __init__(self, person, company, shift):
        """Initialize an Occupation object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        @param shift: Whether this position is for the day or night shift.
        """
        self.person = person
        self.company = company
        self.shift = shift
        self.company.employees.add(self)
        self.start_date = person.cosmos.year
        self.hiring = None  # event.Hiring object holding data about the hiring; gets set by that object's __init__()
        self.end_date = None  # Changed by self.terminate
        self.terminus = None  # Changed by self.terminate
        self.preceded_by = None  # Employee that preceded this one in its occupation -- gets set by Business.hire()
        self.succeeded_by = None  # Employee that succeeded this one in its occupation -- gets set by Business.hire()
        self.supplemental = False  # Whether this position must be immediately refilled if terminated -- Business.hire()
        self.hired_as_favor = False  # Whether this position must ever be refilled if terminated -- Business.hire()
        self.vocation = self._init_generate_vocation_string()
        # Note: self.person.occupation gets set by Business.hire(), because there's
        # a really tricky pipeline that has to be maintained
        person.occupations.append(self)
        self.level = person.cosmos.config.job_levels[self.__class__]
        # Update the .coworkers attribute of this person and their new coworkers
        self._init_update_coworker_listings()
        # Update relevant salience values for this person and their new coworkers
        self._init_update_coworker_salience_values()
        # Update all relationships this person has to reflect the new job-level difference
        # between this person and the respective other person
        for other_person in self.person.relationships:
            self.person.relationships[other_person].update_spark_and_charge_increments_for_job_level_difference()

    def __str__(self):
        """Return string representation."""
        if not self.terminus:
            return "{} at {} since {}".format(
                self.__class__.__name__, self.company.name, self.start_date
            )
        else:
            return "{} at {} {}-{}".format(
                self.__class__.__name__, self.company.name, self.start_date, self.end_date
            )

    def _init_generate_vocation_string(self):
        """Generate a properly formatted vocation string for this occupation."""
        class_name = self.__class__.__name__
        try:
            camel_case_char = next(letter for letter in class_name[1:] if letter in string.uppercase)
            index_of_camel_case_char = class_name.index(camel_case_char)
            if index_of_camel_case_char == 0:
                index_of_camel_case_char = class_name[1:].index(camel_case_char) + 1
            return "{} {}".format(
                class_name[:index_of_camel_case_char].lower(),
                class_name[index_of_camel_case_char:].lower()
            )
        except StopIteration:
            return class_name.lower()

    def _init_update_coworker_listings(self):
        """Update the .coworkers attribute of this person and their new coworkers."""
        new_coworkers = {employee.person for employee in self.company.employees} - {self.person}
        # If they're (becoming) a magnate, this works differently (as explained below), so
        # check for whether they're (becoming) a magnate, i.e., already have an
        # ownership-level occupation
        person_owns_or_now_owns_multiple_businesses = (
            self.person.occupation and self.person.occupation is self.person.occupation.company.owner
        )
        if not person_owns_or_now_owns_multiple_businesses:
            # If they're not a magnate, wash out their former coworkers, if any; we don't do
            # this if they are a magnate, because they are still retaining their positions at
            # the various companies they now hold, and thus are still coworkers with all the
            # employees at those held companies
            self.person.coworkers = set()
        self.person.coworkers |= new_coworkers
        for coworker in new_coworkers:
            coworker.coworkers.add(self.person)

    def _init_update_coworker_salience_values(self):
        """Update relevant salience values for this person and their new coworkers."""
        # Update the salience values that this person holds towards their new coworkers
        # and vice versa
        person = self.person
        salience_change_for_new_coworker = (
            person.cosmos.config.salience_increment_from_relationship_change['coworker']
        )
        for coworker in self.person.coworkers:
            person.update_salience_of(entity=coworker, change=salience_change_for_new_coworker)
            coworker.update_salience_of(entity=person, change=salience_change_for_new_coworker)
        # Update the salience value for this person held by everyone else in their city to
        # reflect their new job level
        boost_in_salience_for_this_job_level = self.person.cosmos.config.salience_job_level_boost(
            job_level=self.level
        )
        for resident in self.company.city.residents:
            resident.update_salience_of(entity=self.person, change=boost_in_salience_for_this_job_level)

    @property
    def years_experience(self):
        """Return the number of years this person has had this occupation."""
        return self.person.cosmos.year - self.start_date

    @property
    def experience(self):
        """Return the number of days this person has had this occupation."""
        if self.hiring:
            experience = self.person.cosmos.ordinal_date-self.hiring.ordinal_date
        else:
            experience = 0
        return experience

    @property
    def has_a_boss(self):
        """Return whether the person with this occupation has a boss."""
        return True if self.company.owner is not self else False

    @property
    def scheduled_to_work_this_timestep(self):
        """Return whether the person with this occupation is scheduled to work on the current timestep."""
        return self.shift == self.person.cosmos.time_of_day

    def terminate(self, reason, replacement_already_hired=False):
        """Terminate this occupation, due to another hiring, lay off, retirement, departure, or death."""
        config = self.person.cosmos.config
        self.end_date = self.person.cosmos.year
        self.terminus = reason
        self.company.employees.remove(self)
        self.company.former_employees.add(self)
        if self is self.company.owner:
            self.company.former_owners.append(self)
        # If this isn't an in-house promotion, update a bunch of attributes
        in_house_promotion = (isinstance(reason, events.major_event.Hiring) and reason.promotion)
        if not in_house_promotion:
            # Update the .coworkers attribute of the person's now former coworkers (the
            # person's attribute has already been updated by their new occupation's
            # '_init_update_coworker_listings()' method
            company_of_new_occupation = None if not isinstance(reason, events.major_event.Hiring) else reason.company
            for employee in self.company.employees:
                # As a solution to the '.coworkers' bug of March 2016, we need to add
                # a check here to make sure that we don't remove this person as a coworker
                # from any employee who also works at the new company, since that will
                # incorrectly remove this person from that employee's .coworkers listing
                # (when of course they are indeed coworkers); currently, this only happens
                # when a person is hired to a new position at a company that is owned by
                # the same person who owns the company they are departing (i.e., a magnate)
                this_person_also_works_at_my_new_company = (
                    company_of_new_occupation and
                    employee.person in {e.person for e in company_of_new_occupation.employees}
                )
                if not this_person_also_works_at_my_new_company:
                    try:
                        employee.person.coworkers.remove(self.person)
                    except KeyError:
                        raise Exception(
                            "{} ({}) could not be removed from {} ({}?) coworkers".format(
                                self.person.name, self.vocation, employee.person.name, employee.vocation
                            )
                        )
            # Update the .former_coworkers attribute of everyone involved to reflect this change
            for employee in self.company.employees:
                self.person.former_coworkers.add(employee.person)
                employee.person.former_coworkers.add(self.person)
            # Update all relevant salience values for everyone involved
            change_in_salience_for_former_coworker = (
                config.salience_increment_from_relationship_change["former coworker"] -
                config.salience_increment_from_relationship_change["coworker"]
            )
            for employee in self.company.employees:
                employee.person.update_salience_of(
                    entity=self.person, change=change_in_salience_for_former_coworker
                )
                self.person.update_salience_of(
                    entity=employee.person, change=change_in_salience_for_former_coworker
                )
        # This position is now vacant, so now have the company that this person worked
        # for fill that now vacant position (which may cause a hiring chain) unless
        # this position is supplemental (i.e., not vital to this businesses' basic
        # operation), in which case we add it back into the business's listing of
        # supplemental positions that may be filled at some point that someone really
        # needs work; if this person was hired as a favor by a family member who owned
        # the associated company, we don't even do that much, since that company doesn't
        # ever need to refill that position (i.e., the position was more supplemental than
        # even supplemental positions and was created solely for the purpose of helping out
        # a family member seeking work)
        if not self.company.out_of_business:
            position_that_is_now_vacant = self.__class__
            if position_that_is_now_vacant is BaseballPlayer:
                # This baseball player will be replaced through the team's established signing process
                self.person.player.career.retire()
            elif not self.supplemental:
                self.company.hire(
                    occupation_of_need=position_that_is_now_vacant, shift=self.shift, to_replace=self
                )
            elif not self.hired_as_favor:
                self.company.supplemental_vacancies[self.shift].append(position_that_is_now_vacant)
        # If the person hasn't already been hired to a new position, set their occupation
        # attribute to None
        if self.person.occupation is self:
            self.person.occupation = None
        # If this person is retiring, set their .coworkers to the empty set
        if isinstance(reason, events.major_event.Retirement):
            self.person.coworkers = set()
        else:
            # If they're not retiring, decrement their salience to everyone else
            # commensurate to the job level of this position
            change_in_salience_for_this_job_level = self.person.cosmos.config.salience_job_level_boost(
                job_level=self.level
            )
            for resident in self.company.city.residents:
                # Note the minus sign here prefixing 'change_in_salience_for_this_job_level'
                resident.update_salience_of(
                    entity=self.person, change=-change_in_salience_for_this_job_level
                )
        # Finally, if this was a Lawyer position, have the law firm rename itself to
        # no longer include this person's name
        if self.__class__ is Lawyer:
            self.company.rename_due_to_lawyer_change()
        # If this is a baseball occupation, and this termination is not occurring because
        # of a team folding, we also need to update league or team personnel attributes
        if not self.company.out_of_business:
            if self.__class__ in config.baseball_league_occupations:
                self.company.league.set_league_personnel()
            elif self.__class__ in config.baseball_franchise_occupations:
                self.company.team.set_team_personnel()


class Magnate(Occupation):
    """An owner of a holding company that owns multiple companies."""

    def __init__(self, person, company, shift):
        """Initialize a Magnate object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Magnate, self).__init__(person=person, company=company, shift=shift)
        for company in self.company.holdings:
            # TODO this is wrong right? needs business-specific owner class?? or why
            # TODO does this even happen at all actually???
            company.owner = Owner(person=self.person, company=company, shift="day")

    def terminate(self, reason, replacement_already_hired=False):
        """Terminate this position."""
        self.end_date = self.person.cosmos.year
        self.terminus = reason
        self.company.employees.remove(self)
        self.company.former_employees.add(self)
        replacement_already_hired = False
        # If this position isn't terminating as part of a company's go_out_of_business
        # procedure, then it means this person is retiring or has died, and so we need
        # to determine who will succeed them as magnate
        if not self.company.out_of_business:
            replacement_already_hired = self.determine_successor(reason=reason)
        # Terminate all active occupations held by this magnate
        for occupation in self.person.occupations:
            if not occupation.terminus:
                occupation.terminate(reason=reason, replacement_already_hired=replacement_already_hired)
        # If the person hasn't already been hired to a new position, set their
        # occupation attribute to None
        self.person.occupation = None

    def determine_successor(self, reason):
        """Determine and instate successor to this magnate position."""
        # If this person has any sons, they will be given this position; if this person
        # has no sons, or none of the sons accept the position, the company will go
        # out of business
        potential_heirs = [
            # TODO heirs who are already magnates just add these new holdings in, and ones who
            # are already owners become magnates and add the company they owned to the holdings
            # of this company
            s for s in self.person.sons if s.adult and s.occupation.__class__.__name__ not in ('Owner', 'Magnate')
        ]
        if potential_heirs:
            scores = {}
            for son in self.person.sons:
                score = son.work_experience
                if son.city is self.person.city:
                    score *= 2
                scores[son] = score
            potential_heirs.sort(key=lambda x: scores[x], reverse=True)
        try:
            son_who_will_take_over = next(
                s for s in potential_heirs if s.accept_job_offer(city=self.company.city, offered_job=Magnate)
            )
            self.company.set_new_magnate(new_magnate=son_who_will_take_over)
            found_successor = True  # Signal that needs to be sent to Magnate.terminate()
        except StopIteration:  # No potential heirs, or none accepted the position, so shut this company down
            self.company.go_out_of_business(reason=reason)
            found_successor = False
        return found_successor

    @property
    def ownerships(self):
        """Return the Owner occupations that this Magnate occupation subsumes."""
        ownerships = [c.owner for c in self.company.holdings]
        return ownerships


class Cashier(Occupation):
    """A cashier at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Cashier object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Cashier, self).__init__(person=person, company=company, shift=shift)


class Janitor(Occupation):
    """A janitor at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Janitor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Janitor, self).__init__(person=person, company=company, shift=shift)


class Manager(Occupation):
    """A manager at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Manager object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Manager, self).__init__(person=person, company=company, shift=shift)


class Secretary(Occupation):
    """A secretary at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Secretary object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Secretary, self).__init__(person=person, company=company, shift=shift)


class Proprietor(Occupation):
    """A proprietor of a business."""

    def __init__(self, person, company, shift):
        """Initialize a Proprietor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Proprietor, self).__init__(person=person, company=company, shift=shift)


class Owner(Occupation):
    """An owner of a business."""

    def __init__(self, person, company, shift):
        """Initialize an Owner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Owner, self).__init__(person=person, company=company, shift=shift)


class Bottler(Occupation):
    """A bottler at a brewery, dairy, or distillery."""

    def __init__(self, person, company, shift):
        """Initialize a Bottler object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Bottler, self).__init__(person=person, company=company, shift=shift)


class Groundskeeper(Occupation):
    """A groundskeeper at a cemetery or park."""

    def __init__(self, person, company, shift):
        """Initialize a Groundskeeper object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Groundskeeper, self).__init__(person=person, company=company, shift=shift)


class Nurse(Occupation):
    """A nurse at a hospital, optometry clinic, plastic-surgery clinic, or school."""

    def __init__(self, person, company, shift):
        """Initialize a Nurse object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Nurse, self).__init__(person=person, company=company, shift=shift)


class Apprentice(Occupation):
    """An apprentice at a blacksmith shop."""

    def __init__(self, person, company, shift):
        """Initialize an Apprentice object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Apprentice, self).__init__(person=person, company=company, shift=shift)


class Architect(Occupation):
    """An architect at a construction firm."""

    def __init__(self, person, company, shift):
        """Initialize an Architect object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Architect, self).__init__(person=person, company=company, shift=shift)
        # Work accomplishments
        self.building_constructions = set()
        self.house_constructions = set()


class BankTeller(Occupation):
    """A bank teller at a bank."""

    def __init__(self, person, company, shift):
        """Initialize a BankTeller object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(BankTeller, self).__init__(person=person, company=company, shift=shift)


class Bartender(Occupation):
    """A bartender at a bar."""

    def __init__(self, person, company, shift):
        """Initialize a Bartender object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Bartender, self).__init__(person=person, company=company, shift=shift)


class BusDriver(Occupation):
    """A bus driver at a bus depot."""

    def __init__(self, person, company, shift):
        """Initialize a BusDriver object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(BusDriver, self).__init__(person=person, company=company, shift=shift)


class CityPlanner(Occupation):
    """A city planner at a city hall."""

    def __init__(self, person, company, shift):
        """Initialize a CityPlanner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the city hall that person works for in this capacity.
        """
        super(CityPlanner, self).__init__(person=person, company=company, shift=shift)


class Concierge(Occupation):
    """A concierge at a hotel."""

    def __init__(self, person, company, shift):
        """Initialize a Concierge object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Concierge, self).__init__(person=person, company=company, shift=shift)


class Builder(Occupation):
    """A builder at a construction firm."""

    def __init__(self, person, company, shift):
        """Initialize a Builder object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Builder, self).__init__(person=person, company=company, shift=shift)


class DaycareProvider(Occupation):
    """A person who works at a day care."""

    def __init__(self, person, company, shift):
        """Initialize a DaycareProvider object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(DaycareProvider, self).__init__(person=person, company=company, shift=shift)


class Doctor(Occupation):
    """A doctor at a hospital."""

    def __init__(self, person, company, shift):
        """Initialize a Doctor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Doctor, self).__init__(person=person, company=company, shift=shift)
        # Work accomplishments
        self.baby_deliveries = set()

    def deliver_baby(self, mother):
        """Instantiate a new Birth object."""
        events.major_event.Birth(mother=mother, doctor=self)


class FireChief(Occupation):
    """A fire chief at a fire station."""

    def __init__(self, person, company, shift):
        """Initialize a FireChief object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(FireChief, self).__init__(person=person, company=company, shift=shift)


class Firefighter(Occupation):
    """A firefighter at a fire station."""

    def __init__(self, person, company, shift):
        """Initialize a Firefighter object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Firefighter, self).__init__(person=person, company=company, shift=shift)


class Barber(Occupation):
    """A barber at a barbershop."""

    def __init__(self, person, company, shift):
        """Initialize a Barber object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Barber, self).__init__(person=person, company=company, shift=shift)


class HotelMaid(Occupation):
    """A hotel maid at a hotel."""

    def __init__(self, person, company, shift):
        """Initialize a HotelMaid object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(HotelMaid, self).__init__(person=person, company=company, shift=shift)


class LandSurveyor(Occupation):
    """A land surveyor at a city hall."""

    def __init__(self, person, company, shift):
        """Initialize a LandSurveyor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the city hall that person works for in this capacity.
        """
        super(LandSurveyor, self).__init__(person=person, company=company, shift=shift)


class Lawyer(Occupation):
    """A lawyer at a law firm."""

    def __init__(self, person, company, shift):
        """Initialize a Lawyer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Lawyer, self).__init__(person=person, company=company, shift=shift)
        # Work accomplishments
        self.filed_divorces = set()
        self.filed_name_changes = set()
        # Have the law firm rename itself to include your name
        self.company.rename_due_to_lawyer_change()

    def file_divorce(self, clients):
        """File a name change on behalf of person."""
        events.major_event.Divorce(subjects=clients, lawyer=self)

    def file_name_change(self, person, new_last_name, reason):
        """File a name change on behalf of person."""
        events.major_event.NameChange(subject=person, new_last_name=new_last_name, reason=reason, lawyer=self)


class Mayor(Occupation):
    """A mayor at the city hall."""

    def __init__(self, person, company, shift):
        """Initialize a Mayor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Mayor, self).__init__(person=person, company=company, shift=shift)


class Mortician(Occupation):
    """A mortician at a cemetery."""

    def __init__(self, person, company, shift):
        """Initialize a Mortician object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Mortician, self).__init__(person=person, company=company, shift=shift)
        # Work accomplishments
        self.body_interments = set()

    def inter_body(self, deceased, cause_of_death):
        """Inter a body in a cemetery."""
        events.major_event.Death(subject=deceased, mortician=self, cause_of_death=cause_of_death)


class Optometrist(Occupation):
    """An optometrist at an optometry clinic."""

    def __init__(self, person, company, shift):
        """Initialize an Optometrist object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Optometrist, self).__init__(person=person, company=company, shift=shift)


class PlasticSurgeon(Occupation):
    """A plastic surgeon at a plastic-surgery clinic."""

    def __init__(self, person, company, shift):
        """Initialize a PlasticSurgeon object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(PlasticSurgeon, self).__init__(person=person, company=company, shift=shift)


class PoliceChief(Occupation):
    """A police chief at a police station."""

    def __init__(self, person, company, shift):
        """Initialize a PoliceChief object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(PoliceChief, self).__init__(person=person, company=company, shift=shift)


class PoliceOfficer(Occupation):
    """A police officer at a police station."""

    def __init__(self, person, company, shift):
        """Initialize a PoliceOfficer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(PoliceOfficer, self).__init__(person=person, company=company, shift=shift)


class Principal(Occupation):
    """A principal at a school."""

    def __init__(self, person, company, shift):
        """Initialize a Principal object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Principal, self).__init__(person=person, company=company, shift=shift)


class Realtor(Occupation):
    """A realtor at a realty firm."""

    def __init__(self, person, company, shift):
        """Initialize an Realtor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Realtor, self).__init__(person=person, company=company, shift=shift)
        # Work accomplishments
        self.home_sales = set()

    def sell_home(self, clients, home):
        """Return a sold home."""
        home_sales = events.major_event.HomePurchase(subjects=clients, home=home, realtor=self)
        return home_sales.home


class Professor(Occupation):
    """A professor at the university."""

    def __init__(self, person, company, shift):
        """Initialize a Professor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Professor, self).__init__(person=person, company=company, shift=shift)


class TattooArtist(Occupation):
    """A tattoo artist at a tattoo parlor."""

    def __init__(self, person, company, shift):
        """Initialize a TattooArtist object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(TattooArtist, self).__init__(person=person, company=company, shift=shift)


class TaxiDriver(Occupation):
    """A taxi driver at a taxi depot."""

    def __init__(self, person, company, shift):
        """Initialize a TaxiDriver object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(TaxiDriver, self).__init__(person=person, company=company, shift=shift)


class Teacher(Occupation):
    """A teacher at the K-12 school."""

    def __init__(self, person, company, shift):
        """Initialize a Teacher object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Teacher, self).__init__(person=person, company=company, shift=shift)


class Waiter(Occupation):
    """A waiter at a restaurant."""

    def __init__(self, person, company, shift):
        """Initialize a Waiter object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Waiter, self).__init__(person=person, company=company, shift=shift)


class Baker(Occupation):
    """A baker at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Baker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Baker, self).__init__(person=person, company=company, shift=shift)


class Barkeeper(Occupation):
    """A barkeeper at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Barkeeper object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Barkeeper, self).__init__(person=person, company=company, shift=shift)


class Blacksmith(Occupation):
    """A blacksmith at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Blacksmith object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Blacksmith, self).__init__(person=person, company=company, shift=shift)


class Brewer(Occupation):
    """A brewer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Brewer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Brewer, self).__init__(person=person, company=company, shift=shift)


class Bricklayer(Occupation):
    """A bricklayer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Bricklayer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Bricklayer, self).__init__(person=person, company=company, shift=shift)


class Busboy(Occupation):
    """A busboy at a restaurant."""

    def __init__(self, person, company, shift):
        """Initialize a Busboy object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Busboy, self).__init__(person=person, company=company, shift=shift)


class Butcher(Occupation):
    """A butcher at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Butcher object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Butcher, self).__init__(person=person, company=company, shift=shift)


class Carpenter(Occupation):
    """A carpenter at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Carpenter object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Carpenter, self).__init__(person=person, company=company, shift=shift)


class Clothier(Occupation):
    """A clothier at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Clothier object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Clothier, self).__init__(person=person, company=company, shift=shift)


class Cook(Occupation):
    """A cook at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Cook object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Cook, self).__init__(person=person, company=company, shift=shift)


class Cooper(Occupation):
    """A cooper at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Cooper object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Cooper, self).__init__(person=person, company=company, shift=shift)


class Dentist(Occupation):
    """A dishwasher at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Dentist object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Dentist, self).__init__(person=person, company=company, shift=shift)


class Dishwasher(Occupation):
    """A dishwasher at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Dishwasher object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Dishwasher, self).__init__(person=person, company=company, shift=shift)


class Distiller(Occupation):
    """A distiller at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Distiller object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Distiller, self).__init__(person=person, company=company, shift=shift)


class Dressmaker(Occupation):
    """A dressmaker at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Dressmaker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Dressmaker, self).__init__(person=person, company=company, shift=shift)


class Druggist(Occupation):
    """A druggist at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Druggist object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Druggist, self).__init__(person=person, company=company, shift=shift)


class Engineer(Occupation):
    """An engineer at a coal mine or quarry."""

    def __init__(self, person, company, shift):
        """Initialize a Engineer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Engineer, self).__init__(person=person, company=company, shift=shift)


class Farmer(Occupation):
    """A farmer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Farmer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Farmer, self).__init__(person=person, company=company, shift=shift)


class Farmhand(Occupation):
    """A farmhand at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Farmhand object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Farmhand, self).__init__(person=person, company=company, shift=shift)


class Grocer(Occupation):
    """A grocer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Grocer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Grocer, self).__init__(person=person, company=company, shift=shift)


class Innkeeper(Occupation):
    """A innkeeper at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Innkeeper object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Innkeeper, self).__init__(person=person, company=company, shift=shift)


class InsuranceAgent(Occupation):
    """A insuranceagent at a business."""

    def __init__(self, person, company, shift):
        """Initialize a InsuranceAgent object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(InsuranceAgent, self).__init__(person=person, company=company, shift=shift)


class Jeweler(Occupation):
    """A jeweler at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Jeweler object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Jeweler, self).__init__(person=person, company=company, shift=shift)


class Joiner(Occupation):
    """A joiner at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Joiner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Joiner, self).__init__(person=person, company=company, shift=shift)


class Laborer(Occupation):
    """A laborer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Laborer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Laborer, self).__init__(person=person, company=company, shift=shift)


class Landlord(Occupation):
    """A landlord at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Landlord object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Landlord, self).__init__(person=person, company=company, shift=shift)


class Milkman(Occupation):
    """A milkman at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Milkman object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Milkman, self).__init__(person=person, company=company, shift=shift)


class Miner(Occupation):
    """A miner at a coal mine."""

    def __init__(self, person, company, shift):
        """Initialize a Miner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Miner, self).__init__(person=person, company=company, shift=shift)


class Molder(Occupation):
    """A molder at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Molder object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Molder, self).__init__(person=person, company=company, shift=shift)


class Painter(Occupation):
    """A painter at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Painter object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Painter, self).__init__(person=person, company=company, shift=shift)


class Pharmacist(Occupation):
    """A pharmacist at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Pharmacist object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Pharmacist, self).__init__(person=person, company=company, shift=shift)


class Plasterer(Occupation):
    """A plasterer at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Plasterer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Plasterer, self).__init__(person=person, company=company, shift=shift)


class Plumber(Occupation):
    """A plumber at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Plumber object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Plumber, self).__init__(person=person, company=company, shift=shift)


class Puddler(Occupation):
    """A puddler at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Puddler object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Puddler, self).__init__(person=person, company=company, shift=shift)


class Quarryman(Occupation):
    """A quarryman at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Quarryman object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Quarryman, self).__init__(person=person, company=company, shift=shift)


class Seamstress(Occupation):
    """A seamstress at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Seamstress object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Seamstress, self).__init__(person=person, company=company, shift=shift)


class Shoemaker(Occupation):
    """A shoemaker at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Shoemaker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Shoemaker, self).__init__(person=person, company=company, shift=shift)


class Stocker(Occupation):
    """A stocker at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Stocker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Stocker, self).__init__(person=person, company=company, shift=shift)


class Stonecutter(Occupation):
    """A stonecutter at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Stonecutter object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Stonecutter, self).__init__(person=person, company=company, shift=shift)


class Tailor(Occupation):
    """A tailor at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Tailor object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Tailor, self).__init__(person=person, company=company, shift=shift)


class Turner(Occupation):
    """A turner at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Turner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Turner, self).__init__(person=person, company=company, shift=shift)


class Whitewasher(Occupation):
    """A whitewasher at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Whitewasher object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Whitewasher, self).__init__(person=person, company=company, shift=shift)


class Woodworker(Occupation):
    """A woodworker at a business."""

    def __init__(self, person, company, shift):
        """Initialize a Woodworker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: The Company object for the company that person works for in this capacity.
        """
        super(Woodworker, self).__init__(person=person, company=company, shift=shift)


class BaseballTeamOwner(Occupation):
    """An owner of a baseball team."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballTeamOwner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        # A team owner can actually work a regular shift schedule, since they don't
        # need to travel to games, etc.
        super(BaseballTeamOwner, self).__init__(person=person, company=company, shift=shift)


class BaseballManager(Occupation):
    """A professional baseball manager."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballManager object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(BaseballManager, self).__init__(person=person, company=company, shift=shift)


class BaseballScout(Occupation):
    """A professional baseball manager."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballScout object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(BaseballScout, self).__init__(person=person, company=company, shift=shift)


class BaseballCommissioner(Occupation):
    """A professional baseball commissioner."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballCommissioner object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball league.
        """
        # A commissioner can actually work a regular shift schedule, since they don't
        # need to travel to games, etc.
        super(BaseballCommissioner, self).__init__(person=person, company=company, shift=shift)


class BaseballUmpire(Occupation):
    """A professional baseball umpire."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballUmpire object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball league.
        """
        super(BaseballUmpire, self).__init__(person=person, company=company, shift=shift)


class BaseballPlayer(Occupation):
    """A professional baseball player."""

    def __init__(self, person, company, shift):
        """Initialize a BaseballPlayer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(BaseballPlayer, self).__init__(person=person, company=company, shift=shift)


class PublicAddressAnnouncer(Occupation):
    """A public-address announcer at a ballpark."""

    def __init__(self, person, company, shift):
        """Initialize a PublicAddressAnnouncer object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(PublicAddressAnnouncer, self).__init__(person=person, company=company, shift=shift)


class StadiumGroundskeeper(Occupation):
    """A groundskeeper at a ballpark."""

    def __init__(self, person, company, shift):
        """Initialize a StadiumGroundskeeper object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(StadiumGroundskeeper, self).__init__(person=person, company=company, shift=shift)


class StadiumUsher(Occupation):
    """An usher at a ballpark."""

    def __init__(self, person, company, shift):
        """Initialize a ConcessionWorker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(StadiumUsher, self).__init__(person=person, company=company, shift=shift)


class ConcessionWorker(Occupation):
    """A concession worker at a ballpark."""

    def __init__(self, person, company, shift):
        """Initialize a ConcessionWorker object.

        @param person: The Person object for the person whose occupation this is.
        @param company: A baseball team.
        """
        super(ConcessionWorker, self).__init__(person=person, company=company, shift=shift)
