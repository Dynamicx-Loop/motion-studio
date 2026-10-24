"""Check authored report translation coverage without a browser dependency."""
from html.parser import HTMLParser
import re


class TranslationAudit(HTMLParser):
    def __init__(self, translations, identifiers):
        super().__init__()
        self.translations = translations
        self.identifiers = identifiers
        self.stack = []
        self.missing = set()
        self.checked = set()

    def check(self, text):
        text = text.strip()
        if not re.search('[a-zA-Z]', text) or text in self.identifiers:
            return
        self.checked.add(text)
        if text not in self.translations:
            self.missing.add(text)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('aria-label', 'alt'):
                self.check(value)
        if tag not in {'meta', 'link', 'br', 'img', 'input', 'hr'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, text):
        if not set(self.stack) & {'script', 'style', 'code', 'pre'}:
            self.check(text)


def validate_translation(document, translations, arm_labels):
    identifiers = set(arm_labels) | {'EN / 中', 'SMPL-X', 'SMPL-X + SOMA',
                                     'PiPlusPro', 'Booster K1', 'G1', 'T800', 'H2', 'MimicKit ‡'}
    audit = TranslationAudit(translations, identifiers)
    audit.feed(document)
    assert not audit.missing, 'Missing Chinese translations: ' + repr(sorted(audit.missing))
    return len(audit.checked)
