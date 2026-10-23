"""Carry the text editor's hidden table/row UUIDs through mutable form edits."""
import json
from difflib import SequenceMatcher

from .ar_typeset_keys import invalid_key


def align_section_keys(previous_json, blocks, hidden):
    try:
        previous = json.loads(previous_json)
        identities = json.loads(hidden)
        if not isinstance(identities, list) or any(not isinstance(item, dict) for item in identities):
            invalid_key()
        tables = [(position, block) for position, block in enumerate(previous) if block['type'] == 'table']
        new_tables = [(position, block) for position, block in enumerate(blocks) if block['type'] == 'table']
        indexed = {item['position']: item for item in identities}
        result, used = [], set()
        for ordinal, (position, block) in enumerate(new_tables):
            match = next(((p, b) for p, b in tables if p not in used and b == block), None)
            if match is None and len(tables) == len(new_tables) and tables[ordinal][0] not in used:
                match = tables[ordinal]
            if match is None:
                continue
            old_position, old = match
            used.add(old_position)
            identity = indexed.get(old_position)
            if identity is None:
                continue
            if len(identity['rows']) != len(old['rows']):
                invalid_key()
            row_keys = [None] * len(block['rows'])
            diff = SequenceMatcher(a=[tuple(r) for r in old['rows']], b=[tuple(r) for r in block['rows']], autojunk=False)
            for tag, a, b, c, d in diff.get_opcodes():
                if tag == 'equal' or (tag == 'replace' and b-a == d-c):
                    row_keys[c:d] = identity['rows'][a:b]
                elif tag == 'replace':
                    # A single label may keep a row identifiable while another
                    # row is inserted. Duplicate labels deliberately do not match.
                    for index in range(c, d):
                        label = block['rows'][index][0]
                        old_matches = [i for i in range(a, b) if old['rows'][i][0] == label]
                        new_matches = [i for i in range(c, d) if block['rows'][i][0] == label]
                        if len(old_matches) == len(new_matches) == 1:
                            row_keys[index] = identity['rows'][old_matches[0]]
            result.append({'position': position, 'stable_key': identity['stable_key'], 'rows': row_keys})
        return result
    except (ValueError, TypeError, KeyError, IndexError):
        invalid_key()
