#!/usr/bin/env python3
"""Bounded, lossless navigation of saved JSON; full evidence stays on disk."""
import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_LIMIT = 8000  # Unicode characters, NOT model tokens.
MAX_LIMIT = 24000


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def escape(value):
    return str(value).replace('~', '~0').replace('/', '~1')


def resolve(document, pointer):
    if pointer and not pointer.startswith('/'):
        raise ValueError('Use an RFC 6901 JSON pointer, e.g. /visual_style_groups')
    value = document
    for part in pointer.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def view(path, pointer='', cursor=0, limit=DEFAULT_LIMIT, expected_hash=None):
    if not 2000 <= limit <= MAX_LIMIT or cursor < 0:
        raise ValueError('limit must be 2000..24000 characters; cursor must be nonnegative')
    path = Path(path).resolve()
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_hash and digest != expected_hash:
        raise ValueError('Evidence changed; restart pagination against the new file hash')
    value = resolve(json.loads(raw), pointer)
    result = {'file':str(path), 'sha256':digest, 'pointer':pointer,
              'budget_unit':'unicode_characters', 'limit':limit,
              'cursor':cursor, 'total':None, 'next_cursor':None, 'items':[]}
    if isinstance(value, str):
        # Leaf strings can be continued explicitly, never silently truncated.
        result['total'] = len(value)
        if cursor > len(value):
            raise ValueError('Cursor is outside this value')
        take = max(1, (limit-len(encode(result))-300)//6)
        result['items'] = [{'pointer':pointer, 'text_offset':cursor,
                            'text':value[cursor:cursor+take]}]
        result['next_cursor'] = cursor+take if cursor+take < len(value) else None
    else:
        entries = list(value.items()) if isinstance(value, dict) else (
            list(enumerate(value)) if isinstance(value, list) else [(None, value)])
        result['total'] = len(entries)
        for index in range(cursor, len(entries)):
            key, item = entries[index]
            ref = pointer+'/'+escape(key) if key is not None else pointer
            record = {'pointer':ref, 'value':item}
            # An oversized record remains discoverable at its exact pointer.
            if len(encode(record)) > limit-len(encode(result))-300 and not result['items']:
                record = {'pointer':ref, 'deferred':True, 'type':type(item).__name__,
                          'characters':len(encode(item)),
                          'children':len(item) if isinstance(item, (dict,list,str)) else 0}
            if len(encode({**result,'items':[*result['items'],record]}))+100 > limit:
                if not result['items']:
                    raise ValueError('Record reference exceeds budget; use a shorter path or larger limit')
                result['next_cursor'] = index
                break
            result['items'].append(record)
        if cursor > result['total']:
            raise ValueError('Cursor is outside this value')
    if len(encode(result)) > limit:
        raise ValueError('Metadata exceeds output budget; use a shorter file path')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--file', type=Path, required=True)
    p.add_argument('--pointer', default='')
    p.add_argument('--cursor', type=int, default=0)
    p.add_argument('--limit', type=int, default=DEFAULT_LIMIT)
    p.add_argument('--sha256', help='Required identity when continuing a previous response')
    a = p.parse_args()
    try:
        if a.cursor and not a.sha256:
            raise ValueError('Continuation requires --sha256 from the first response')
        print(encode(view(a.file,a.pointer,a.cursor,a.limit,a.sha256)))
        return 0
    except (ValueError, OSError, KeyError, IndexError, TypeError) as exc:
        print(encode({'status':'EVIDENCE_ERROR','error':str(exc)[:500]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
