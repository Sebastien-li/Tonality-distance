class Pitch:
    note_names = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    diatonic_dict = {note: i for i, note in enumerate(note_names)}
    chromatic_dict = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
    def __init__(self, name:str):
        name = ''.join([x for x in name if not x.isdigit()])
        self.name = name
        self.name_without_accidental = name[0]
        self.accidental = name[1:].replace('b','-')
        assert self.name_without_accidental in self.diatonic_dict, f'Invalid note name: {name}'
        assert all(['#' == x for x in  self.accidental]) or all(['-' == x for x in  self.accidental]) , f'Invalid accidental: {self.accidental}'
        self.diatonic = self.diatonic_dict[self.name_without_accidental]
        self.chromatic = (self.chromatic_dict[self.name_without_accidental] + sum(x=='#' for x in self.accidental) - sum(x=='-' for x in self.accidental) )%12

    def __repr__(self):
        return f'{self.name}'

    def __eq__(self, other):
        return self.chromatic == other.chromatic and self.diatonic == other.diatonic

    def __add__(self, interval):
        diatonic = (self.diatonic + interval.diatonic)%7
        chromatic = (self.chromatic + interval.chromatic)%12
        return Pitch.from_dia_chro(diatonic, chromatic)

    @classmethod
    def from_dia_chro(cls, diatonic, chromatic):
        diatonic %= 7
        chromatic %= 12
        name_without_accidental = cls.note_names[diatonic]
        accidental_number = (chromatic - cls.chromatic_dict[name_without_accidental])%12
        accidental =  '#' * (accidental_number <=6)*accidental_number  + '-' * (accidental_number > 6) *(12-accidental_number)
        return Pitch(name_without_accidental + accidental)

    def __hash__(self):
        return hash((self.diatonic, self.chromatic))


class Interval:
    def __init__(self, pitchStart:Pitch, pitchEnd:Pitch ):
        self.diatonic = (pitchEnd.diatonic - pitchStart.diatonic)%7
        self.chromatic = (pitchEnd.chromatic - pitchStart.chromatic)%12
        self.interval_number = self.diatonic + 1

    def __repr__(self):
        return f'({self.diatonic}, {self.chromatic})'

    def __eq__(self, other):
        return self.diatonic == other.diatonic and self.chromatic == other.chromatic

    def __hash__(self):
        return hash((self.diatonic, self.chromatic))
