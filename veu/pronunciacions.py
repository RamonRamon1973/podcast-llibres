#!/usr/bin/env python3
"""Diccionari de pronunciacions per a les veus Azure en català i castellà.

Les veus Joana (ca-ES) i Elvira (es-ES) no són "multilingües": llegeixen
qualsevol paraula amb les regles fonètiques del seu propi idioma, també els
noms propis i termes en anglès. Per això aquest mòdul reescriu foneticament
(amb ortografia catalana/castellana) els termes anglesos ABANS d'enviar el
text a Azure, sense tocar mai el guió original que es desa com a transcripció.

Ampliació: cada episodi pot afegir el seu propi diccionari puntual (per al
títol del llibre, l'autor, etc.) a través del camp opcional "pron" del JSON
pendent. Els termes d'aquest mòdul són els que es repeteixen sovint d'un
episodi a l'altre (empreses, conceptes de negoci en anglès...).
"""
import re

# Terme tal com apareix al guió -> aproximació fonètica amb ortografia catalana
DICCIONARI_CA = {
    "Silicon Valley": "Sàilicon Vàli",
    "Harvard": "Hàrvard",
    "Stanford": "Stànford",
    "Massachusetts": "Massatxússets",
    "startup": "estàrtap",
    "startups": "estàrtaps",
    "feedback": "fídbac",
    "marketing": "màrqueting",
    "business": "bíznes",
    "management": "mànagement",
    "leadership": "lídership",
    "mindset": "màindset",
    "benchmark": "bènxmarc",
    "brainstorming": "brènstorming",
    "coworking": "co-uòrquing",
    "freelance": "frílans",
    "machine learning": "maixín lérning",
    "blockchain": "blòcxein",
    "podcast": "pòdcast",
    "streaming": "estríming",
    "Google": "Gúgol",
    "Amazon": "Àmazon",
    "Netflix": "Nètflix",
    "Apple": "Àpol",
    "iPhone": "Àifon",
    "Airbnb": "Erbienbí",
    "Uber": "Úber",
    "LinkedIn": "Línktin",
    "Facebook": "Féisbuc",
    "Twitter": "Tuíter",
    "Microsoft": "Màicrosoft",
    "Excel": "Èxel",
    "Zoom": "Zum",
    "Wharton": "Uòrton",
    "Berkeley": "Bércli",
    "Yale": "Ieil",
    "Princeton": "Prínsston",
    "Silicon": "Sàilicon",
}

DICCIONARI_ES = {
    "Silicon Valley": "Sáilicon Váli",
    "Harvard": "Járvard",
    "Stanford": "Stánford",
    "Massachusetts": "Masachúsets",
    "startup": "estartap",
    "startups": "estartaps",
    "feedback": "fídbac",
    "marketing": "márquetin",
    "business": "bísnes",
    "management": "mánagement",
    "leadership": "lídership",
    "mindset": "máindset",
    "benchmark": "bénchmarc",
    "brainstorming": "brenstorming",
    "coworking": "cowórquin",
    "freelance": "frílans",
    "machine learning": "machín lérnin",
    "blockchain": "blóckchéin",
    "podcast": "pódcast",
    "streaming": "estríming",
    "Google": "Gúgol",
    "Amazon": "Ámazon",
    "Netflix": "Nétflix",
    "Apple": "Ápol",
    "iPhone": "Áifon",
    "Airbnb": "Erbienbí",
    "Uber": "Úber",
    "LinkedIn": "Línktin",
    "Facebook": "Féisbuc",
    "Twitter": "Tuíter",
    "Microsoft": "Máicrosoft",
    "Excel": "Éxel",
    "Zoom": "Zum",
    "Wharton": "Uárton",
    "Berkeley": "Bércli",
    "Yale": "Iéil",
    "Princeton": "Prínston",
    "Silicon": "Sáilicon",
}


def aplica(text, lang="ca", extra=None):
    """Retorna una còpia del text amb els termes anglesos reescrits
    foneticament, per fer-la servir NOMÉS a l'entrada de la veu (mai es
    desa enlloc). `extra` és un diccionari opcional propi de l'episodi
    (p.ex. títol del llibre o nom de l'autor) que té prioritat."""
    base = dict(DICCIONARI_CA if lang.startswith("ca") else DICCIONARI_ES)
    if extra:
        base.update(extra)
    # Les entrades de diverses paraules es substitueixen abans que les
    # paraules soltes, per evitar substitucions parcials incorrectes.
    for original in sorted(base, key=len, reverse=True):
        replacement = base[original]
        pattern = re.compile(r'\b' + re.escape(original) + r'\b')

        def repl(m, replacement=replacement):
            if m.group(0)[0].isupper():
                return replacement[0].upper() + replacement[1:]
            return replacement

        text = pattern.sub(repl, text)
    return text
