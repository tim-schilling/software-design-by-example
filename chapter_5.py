def parse_lists(text):
    start = 0
    end = len(text)-1
    has_lead, has_end = False, False
    while not has_lead or not has_end:
        if text[start] == "[":
            has_lead = True
        else:
            start += 1

        if text[end] == "]":
            has_end = True
        else:
            end -= 1

        if start > end:
            break
    if has_lead and has_end:
        return [*parse_values(text[start+1:end])]
    else:
        return text


def parse_values(text):
    try:
        return [parse_lists(value.strip()) for value in text.split(',')]
    except IndexError:
        return []

print(parse_lists("[1, 2, 3]"))
print(parse_lists("[[1], [2, 4, [5, 6]], 3]"))


def parse(text):
    result = []
    current = None
    current_text = ""
    while text:
        char, text = text[0], text[1:]
        if char == "[":
            current = []
        elif char == "]":
            if current_text:
                current.append(current_text)
                current_text = ""
            result.append(current)
            current = None
        elif char == " ":
            pass
        elif char == ",":
            current.append(current_text)
            current_text = ""
        else:
            current_text += char
    return result

#print(parse("[1]"))
print(parse("[1, [2], 3]"))


import string

# [class]
CHARS = set(string.digits)

class Tokenizer:
    def __init__(self):
        self._setup()

    def _setup(self):
        self.result = []
        self.current = ""

    def tok(self, text):
        self._setup()
        for ch in text:
            if ch == "[":
                self._add("Start")
            elif ch == ",":
                self._add(None)
            elif ch == "]":
                self._add("End")
            elif ch in CHARS:
                self.current += ch
            else:
                continue
        self._add(None)
        return self.result

    def _add(self, thing):
        if len(self.current) > 0:
            self.result.append(["Lit", self.current])
            self.current = ""
        if thing is not None:
            self.result.append([thing])


class Parser:
    def parse(self, text):
        tokens = Tokenizer().tok(text)
        return self._parse(tokens)

    def _parse(self, tokens):
        if not tokens:
            return None

        result = []
        front, back = tokens[0], tokens[1:]
        if front[0] == "Start":
            result.append(self._parse(back))
        elif front[0] == "End":
            return result
        elif front[0] == "Lit":
            result.append(int(front[1]))
        else:
            assert False, f"Unknown token type {front}"
        return result


p = Parser()
print(p.parse("[1, 3]"))
