
class Match:
    def __init__(self, rest):
        self.rest = rest if rest else Null()

    def match(self, text):
        result = self._match(text, 0)
        return result == len(text)

class Any(Match):
    def __init__(self, rest=None):
        super().__init__(rest)

    def _match(self, text, start):
        for i in range(start, len(text) + 1):
            end = self.rest._match(text, i)
            if end == len(text):
                return end
        return None


class Null(Match):
    def __init__(self):
        self.rest = None

    def _match(self, text, start):
        return start


class Lit(Match):
    def __init__(self, chars, rest=None):
        super().__init__(rest)
        self.chars = chars

    def _match(self, text, start):
        end = start + len(self.chars)
        if text[start:end] != self.chars:
            return None
        return self.rest._match(text, end)


class Charset(Match):

    def __init__(self, charset, rest=None):
        super().__init__(rest)
        self.charset = set(charset)

    def _match(self, text, start):
        char = text[start]
        if char in self.charset:
            return self.rest._match(text, start + 1)
        return None

def test_charset_as_string():
    assert Charset("abc").match("a")
    assert not Charset("abc").match("z")

def test_charset_chained():
    assert Charset("ab", Charset("bc")).match("ac")
    assert Charset("ab", Charset("bc")).match("bb")

def test_charset_as_set():
    assert Charset({'A', 'B'}).match("B")
    assert not Charset({'A', 'B'}).match("b")

class Range(Match):

    def __init__(self, start, end, rest=None):
        super().__init__(rest)
        self.start = ord(start)
        self.end = ord(end)
        if self.end < self.start:
            raise ValueError("End must be a character at or after Start")

    def _match(self, text, start):
        char = text[start]
        if self.start <= ord(char) <= self.end:
            return self.rest._match(text, start + 1)
        return None

def test_range_end_before_start():
    try:
        Range("z", "a").match("a")
    except ValueError:
        pass
    else:
        assert False

def test_range():
    assert Range("b", "c").match("b")
    assert Range("b", "c").match("c")
    assert not Range("b", "c").match("a")
    assert not Range("b", "c").match("d")


def test_range_case_sensitivity():
    assert not Range("b", "c").match("B")
    assert not Range("b", "c").match("C")


class Not(Match):
    def __init__(self, literal, rest=None):
        super().__init__(rest)
        self.not_lit = literal

    def _match(self, text, start):
        lit_len = len(self.not_lit.chars)
        if self.not_lit.match(text[start:lit_len]):
            return None
        return self.rest._match(text, start + lit_len)

class Not(Match):
    def __init__(self, pattern, rest=None):
        super().__init__(rest if rest else Any())
        self.not_pattern = pattern

    def _match(self, text, start):
        end = self.not_pattern._match(text, start)
        if end is not None:
            return None
        return self.rest._match(text, start)


def test_not_literal():
    assert Not(Lit("a")).match("a") is False
    assert Not(Lit("a")).match("c") is True


def test_not_with_rest():
    assert Not(Lit("a"), Charset("ab")).match("a") is False
    assert Not(Lit("a"), Charset("ab")).match("b") is True
    assert Not(Lit("a"), Charset("ab")).match("c") is False

    assert Not(Lit("a", Any(Lit("b"))), Lit("art")).match("artb") is False
    assert Not(Lit("a", Any(Lit("b"))), Lit("art")).match("abrt") is False
    assert Not(Lit("a", Any(Lit("b"))), Lit("art")).match("art") is True


class Either(Match):
    def __init__(self, *patterns, rest=None):
        super().__init__(rest)
        self.patterns = patterns
        if not self.patterns:
            raise ValueError("At least one pattern must be passed in")

    def _match(self, text, start):
        for pat in self.patterns:
            end = pat._match(text, start)
            if end is not None:
                end = self.rest._match(text, end)
                if end == len(text):
                    return end
        return None

def test_either_one():
    assert Either(Lit("a")).match("a")
    assert not Either(Lit("a")).match("A")

def test_either_two():
    assert Either(Lit("a"), Lit("b")).match("a")
    assert Either(Lit("a"), Lit("b")).match("b")
    assert not Either(Lit("a"), Lit("b")).match("A")

def test_either_none():
    try:
        Either()
    except ValueError:
        pass
    else:
        assert False

def test_either_rest():
    assert Either(Lit("a"), rest=Lit("b")).match("ab")
    assert not Either(Lit("a"), rest=Lit("b")).match("ac")

# Support returning the matching values

class Match:
    def __init__(self, rest):
        self.rest = rest if rest else Null()

    def match(self, text):
        result, matches = self._match(text, 0)
        if result == len(text):
            return True, matches
        return False, []


class Any(Match):
    def __init__(self, rest=None):
        super().__init__(rest)

    def _match(self, text, start):
        # Swap the params to do greedy matching
        for i in range(len(text), start - 1, -1):
            end, matches = self.rest._match(text, i)
            if end == len(text):
                return end, [text[start:i]] + matches
        return None, []


class Null(Match):
    def __init__(self):
        self.rest = None

    def _match(self, text, start):
        return start, []


class Lit(Match):
    def __init__(self, chars, rest=None):
        super().__init__(rest)
        self.chars = chars

    def _match(self, text, start):
        end = start + len(self.chars)
        if text[start:end] != self.chars:
            return None, []
        end, matches = self.rest._match(text, end)
        return end, [self.chars] + matches


class Charset(Match):

    def __init__(self, charset, rest=None):
        super().__init__(rest)
        self.charset = set(charset)

    def _match(self, text, start):
        char = text[start]
        if char in self.charset:
            end, matches = self.rest._match(text, start + 1)
            return end, [char] + matches
        return None, []


class Either(Match):
    def __init__(self, *patterns, rest=None):
        super().__init__(rest)
        self.patterns = patterns
        if not self.patterns:
            raise ValueError("At least one pattern must be passed in")

    def _match(self, text, start):
        for pat in self.patterns:
            end, pat_matches = pat._match(text, start)
            if end is not None:
                end, matches = self.rest._match(text, end)
                if end == len(text):
                    return end, pat_matches + matches
        return None, []


def test_returned_matches_any():
    assert Any().match("text") == (True, ["text"])

def test_returned_matches_any_suffixed():
    assert Any(Lit(".txt")).match("text.txt") == (True, ["text", ".txt"])

def test_returned_matches_any_wrapped():
    assert Lit("te", Any(Lit(".txt"))).match("text.txt") == (True, ["te", "xt", ".txt"])

def test_returned_matches_either_injects_patterns():
    assert Lit("te", Either(Lit("x", Lit("t")), rest=Lit(".txt"))).match("text.txt") == (True, ["te", "x", "t", ".txt"])
