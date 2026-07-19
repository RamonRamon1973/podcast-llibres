#!/usr/bin/env python3
"""Doblar la erra vibrant inicial perquè la veu Ona medium la pronunciï bé.
Regla: R/r a principi de paraula -> Rr/rr. També després de prefixos (l', d', etc.)
NO toca la erra entre vocals (ja sona bé) ni la de final de paraula."""
import re, sys

def fix(text):
    # R inicial de paraula (precedida d'espai, principi de línia, o apòstrof/guió)
    # Preserva majúscula/minúscula
    def repl(m):
        pre, r = m.group(1), m.group(2)
        return pre + ('Rr' if r == 'R' else 'rr')
    # (^|inici de paraula) + R/r seguida de vocal, dins d'una paraula que comença per R
    return re.sub(r"(^|[\s'’\-–—\"«(])([Rr])(?=[aeiouàèéíòóúïü])", repl, text, flags=re.MULTILINE)

if __name__ == '__main__':
    t = sys.stdin.read()
    sys.stdout.write(fix(t))
