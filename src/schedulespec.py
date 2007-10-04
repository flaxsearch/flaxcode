import itertools

class ScheduleSpec(object):
    """
    Specifies the options for sceduling the indexing of a document collection

    """


    def __init__(self, **kwargs):

        self.update(**kwargs)


    _wildcard = '*'
    _empty = ""

    def parse_string_spec(self, spec):
        if not isinstance(spec, str):
            return spec
        stripped = spec.strip()
        if (stripped == self._wildcard) or (stripped == self._empty):
            return stripped
        return [int(x) for x in stripped.split(',')]
    
    def update(self,
               mins = _empty,
               hours = _empty,
               monthdays = _empty,
               weekdays = _empty,
               months = _empty,
               **kwargs):

        self.mins = self.parse_string_spec(mins)
        self.hours = self.parse_string_spec(hours)
        self.monthdays = self.parse_string_spec(monthdays)
        self.weekdays = self.parse_string_spec(weekdays)
        self.months = self.parse_string_spec(months)


    def wildcarded(self, prop):
        return prop == self._wildcard

    def _matches(self, candidate, prop):
        return not (prop == self._empty) and (self.wildcarded(prop) or (candidate in prop))

    def matching_time(self, date_time):
        """ Determines whether the datetime.datetime object provided
        matches the filespec."""

        return all(itertools.starmap(self._matches,
                                     ((date_time.month, self.months), 
                                      (date_time.day, self.monthdays),
                                      (date_time.weekday, self.weekdays),
                                      (date_time.hour, self.hours),
                                      (date_time.minute, self.mins))))

