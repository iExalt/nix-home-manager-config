#!/usr/bin/env python3
"""Validated private friction JSONL. Stdlib only; use log, check, latest or port."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

KINDS = ('instructions', 'tool', 'environment', 'workflow', 'other')
STATUSES = ('open', 'resolved', 'unverified')
FIELDS = {'v', 'event_id', 'incident_id', 'previous_event_id', 'logged_at', 'date',
          'source', 'repo', 'thread_id', 'harness', 'model', 'origin', 'kind', 'status',
          'subject', 'summary', 'evidence', 'workaround', 'resolution', 'suggestion', 'migration'}
REQUIRED = {'v', 'event_id', 'incident_id', 'previous_event_id', 'logged_at', 'date',
            'source', 'repo', 'thread_id', 'origin', 'kind', 'status', 'summary',
            'evidence', 'suggestion'}
MAX_BYTES = 256 * 1024


def encode(record):
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                       allow_nan=False) + '\n').encode('utf-8')


def utc_now():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def exact_keys(value, required, allowed):
    return isinstance(value, dict) and required <= value.keys() <= allowed


def references(value, required=True):
    return isinstance(value, list) and (bool(value) or not required) and all(
        exact_keys(x, {'ref', 'note'}, {'ref', 'note'}) and
        nonempty(x['ref']) and nonempty(x['note']) for x in value)


def validate(rec):
    if not isinstance(rec, dict):
        raise ValueError('record must be an object')
    if rec.keys() - FIELDS or REQUIRED - rec.keys():
        raise ValueError(f'unknown fields {sorted(rec.keys() - FIELDS)}; missing {sorted(REQUIRED - rec.keys())}')
    ported = rec.get('source') == 'md-port'
    if type(rec['v']) is not int or rec['v'] != 1 or rec['source'] not in ('live', 'md-port'):
        raise ValueError('v must be 1 and source live or md-port')
    for key in ('event_id', 'incident_id', 'summary'):
        if not nonempty(rec[key]):
            raise ValueError(f'{key} must be a nonempty string')
    for key in ('repo', 'thread_id', 'kind', 'status', 'suggestion', 'date'):
        if rec[key] is None and (ported or key == 'repo'):
            continue
        if not nonempty(rec[key]):
            raise ValueError(f'{key} must be a nonempty string')
    for key in ('previous_event_id', 'harness', 'model', 'subject', 'workaround'):
        if rec.get(key) is not None and not nonempty(rec[key]):
            raise ValueError(f'{key} must be a nonempty string or null')
    if rec['kind'] is not None and rec['kind'] not in KINDS:
        raise ValueError('invalid kind')
    if rec['status'] is not None and rec['status'] not in STATUSES:
        raise ValueError('invalid status')
    if rec['date'] is not None:
        dt.date.fromisoformat(rec['date'])
    if not isinstance(rec['logged_at'], str) or not rec['logged_at'].endswith('Z'):
        raise ValueError('logged_at must be an ISO 8601 UTC timestamp ending in Z')
    timestamp = dt.datetime.fromisoformat(rec['logged_at'].replace('Z', '+00:00'))
    if timestamp.tzinfo is None:
        raise ValueError('logged_at requires a time and UTC timezone')
    origin = rec['origin']
    if (not exact_keys(origin, {'thread_id', 'event_ref'}, {'thread_id', 'event_ref'})
            or not nonempty(origin['event_ref'])
            or not (nonempty(origin['thread_id']) or
                    (origin['thread_id'] is None and (ported or rec['previous_event_id'] is not None)))):
        raise ValueError('origin requires thread_id and event_ref')
    if not references(rec['evidence'], required=not ported):
        raise ValueError('evidence requires ref/note objects')
    resolution = rec.get('resolution')
    if resolution is not None and (not exact_keys(resolution, {'summary', 'evidence'}, {'summary', 'evidence'})
                                  or not nonempty(resolution['summary'])
                                  or not references(resolution['evidence'])):
        raise ValueError('resolution requires summary and nonempty evidence')
    if rec['status'] == 'resolved' and resolution is None and not ported:
        raise ValueError('resolved requires verified fix evidence in resolution')
    if rec['source'] == 'live' and 'migration' in rec:
        raise ValueError('migration is only allowed for md-port')
    if ported:
        m = rec.get('migration')
        keys = {'file', 'line_start', 'line_end', 'original_text', 'notes'}
        if not exact_keys(m, keys, keys) or not nonempty(m['file']) or not nonempty(m['original_text']):
            raise ValueError('md-port requires original text and source location')
        if (type(m['line_start']) is not int or type(m['line_end']) is not int
                or not 1 <= m['line_start'] <= m['line_end']):
            raise ValueError('invalid migration line range')
        if not isinstance(m['notes'], list) or not all(nonempty(x) for x in m['notes']):
            raise ValueError('migration notes must be strings')
    if len(encode(rec)) > MAX_BYTES:
        raise ValueError('record exceeds 256 KiB')


def check_records(records):
    events, latest = {}, {}
    for n, rec in enumerate(records, 1):
        try:
            validate(rec)
            if rec['event_id'] in events:
                raise ValueError('duplicate event_id')
            prior = latest.get(rec['incident_id'])
            if rec['previous_event_id'] != (prior['event_id'] if prior else None):
                raise ValueError('previous_event_id is not the current incident head')
            if not prior and rec['source'] == 'live' and not nonempty(rec['origin']['thread_id']):
                raise ValueError('new live incident requires original thread identity')
            if prior and prior['origin'] != rec['origin']:
                raise ValueError('origin must be preserved across follow-ups')
            events[rec['event_id']] = rec
            latest[rec['incident_id']] = rec
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f'record {n}: {exc}') from exc
    return events, latest


def read_log(path):
    if not path.exists():
        return []
    data = path.read_bytes()
    if data and not data.endswith(b'\n'):
        raise ValueError('log has a truncated final line; preserve and repair before appending')
    records = []
    for n, line in enumerate(data.splitlines(), 1):
        try:
            records.append(json.loads(line))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f'line {n}: invalid JSON') from exc
    check_records(records)
    return records


@contextlib.contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path) + '.lock', os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def append(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, 'ab', closefd=False) as out:
            out.write(data)
            out.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def log_record(path, rec):
    if not isinstance(rec, dict):
        raise ValueError('record must be an object')
    # Callers retry with the printed, completed snapshot, including event_id.
    rec.setdefault('v', 1)
    rec.setdefault('source', 'live')
    rec.setdefault('logged_at', utc_now())
    rec.setdefault('date', rec['logged_at'][:10])
    rec.setdefault('event_id', str(uuid.uuid4()))
    rec.setdefault('previous_event_id', None)
    if rec['source'] != 'live':
        raise ValueError('log accepts live reports only; use port for historical records')
    validate(rec)
    with locked(path):
        records = read_log(path)
        events, _ = check_records(records)
        if rec['event_id'] in events:
            if rec != events[rec['event_id']]:
                raise ValueError('event_id already exists with a different payload')
            return rec
        check_records(records + [rec])
        append(path, encode(rec))
    return rec


# Recognize only explicit IDs, never merge incidents on similar wording.
ID_LINE = re.compile(
    r'^\s*(?:[-*]\s*)?(?:\*\*)?(?:Follow-up\s+(?:to\s+)?)?'
    r'(?:Incident\s*ID|Friction\s*ID|Incident|ID)'
    r'(?:\s*:\s*(?:\*\*)?\s*`?([A-Za-z0-9][A-Za-z0-9_.-]*)'
    r'|\s+`?([A-Za-z0-9][A-Za-z0-9_.]*[-0-9][A-Za-z0-9_.-]*))', re.I)
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
LABEL_START = r'(?:^|[.;]\s*)\s*(?:[-*]\s*)?(?:\*\*)?'


def explicit_id(line):
    match = ID_LINE.match(line)
    return (match.group(1) or match.group(2)).rstrip('.') if match else None

HEADING = re.compile(r'^#{1,6}\s+')
META = re.compile(r'^\s*[-*]?\s*(?:ID|Incident|Agent|Reporter|Status|Evidence|Suggestion|Original|What happened|Fix|Resolution|Conversation|Thread)', re.I)


def chunks(text):
    """Contiguous, complete line partition; split explicit incidents and independent bullets."""
    lines = text.splitlines(keepends=True)
    headings = [i for i, line in enumerate(lines) if HEADING.match(line)]
    boundaries = sorted(set([0, len(lines)] + headings))
    result = []
    for start, end in zip(boundaries, boundaries[1:]):
        section = lines[start:end]
        if not section:
            continue
        ids = [start + i for i, line in enumerate(section) if ID_LINE.match(line)]
        # Heading and leading whitespace belong to the first incident.
        split = ids[1:]
        if not ids and not any(META.match(line) for line in section):
            bullets = [start + i for i, line in enumerate(section) if re.match(r'^[-*] ', line)]
            split = bullets[1:]
        points = [start] + split + [end]
        for a, b in zip(points, points[1:]):
            raw = ''.join(lines[a:b])
            # Fold whitespace-only preambles into the next record.
            if not raw.strip() and b < len(lines):
                if result:
                    old_a, _, old_raw, heading = result.pop()
                    result.append((old_a, b, old_raw + raw, heading))
                else:
                    continue
            else:
                heading = next((line.strip() for line in section if HEADING.match(line)), '')
                if not result and a and not ''.join(lines[:a]).strip():
                    raw = ''.join(lines[:a]) + raw
                    a = 0
                result.append((a, b, raw, heading))
    if ''.join(x[2] for x in result) != text:
        raise ValueError('internal port error: source partition lost text')
    return result


def port_records(source, data, logged_at, previous=()):
    text = data.decode('utf-8')
    records = list(previous)
    _, heads = check_records(records)
    prefix = ''.join(r['migration']['original_text'] for r in records)
    if not text.startswith(prefix):
        raise ValueError('source is not an unchanged byte prefix of the previous import')
    offset = len(prefix.splitlines())
    suffix = text[len(prefix):]
    if prefix and not prefix.endswith('\n') and suffix:
        raise ValueError('previous archive ended mid-line; reconcile explicitly before importing appended text')
    for start, end, raw, heading in chunks(suffix):
        start += offset
        end += offset
        explicit = next((explicit_id(line) for line in raw.splitlines() if explicit_id(line)), None)
        digest = hashlib.sha256(f'{start + 1}\n'.encode() + raw.encode()).hexdigest()
        incident = explicit or 'md-' + digest[:24]
        prior = heads.get(incident)
        date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', heading)
        date = date_match.group() if date_match else None
        # Unknown facts stay null; verbatim text remains available for later curation.
        status_match = re.search(LABEL_START + r'Status(?:\*\*)?\s*:?\s*(?:\*\*)?\s*(open|resolved|unverified)\b', raw, re.I | re.M)
        suggestion = re.search(LABEL_START + r'(?:Suggestion|Suggested fix)(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.+)', raw, re.I | re.M)
        thread = re.search(r'(?:conversation(?:/thread)?(?:\s*ID)?|(?:Reporting )?thread(?:\s*ID)?)'
                           r'\s*:?\s*`?(' + UUID + r')\b', raw, re.I)
        repo = re.search(r'(?<![\w/])[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*(?![\w/])', heading)
        notes = ['Conservative Markdown import; unextracted facts remain in original_text.',
                 'kind and origin not inferred; evidence/fix claims retained verbatim, not independently verified.']
        if not heading:
            notes.append('No heading in this fragment; date and repository context are unknown.')
        if explicit is None:
            notes.append('No explicit incident ID; generated a deterministic ID. Possible duplicate not merged.')
        rec = dict(v=1, event_id='md-' + digest, incident_id=incident,
                   previous_event_id=prior['event_id'] if prior else None,
                   logged_at=logged_at, date=date, source='md-port',
                   repo=repo.group() if repo else None, thread_id=thread.group(1) if thread else None,
                   origin=prior['origin'] if prior else {'thread_id': None, 'event_ref': f'{source}:{start + 1}'}, kind=None, status=status_match.group(1).lower() if status_match else None,
                   summary=raw.strip(), evidence=[], suggestion=suggestion.group(1).strip() if suggestion else None,
                   migration={'file': str(source), 'line_start': start + 1, 'line_end': end,
                              'original_text': raw, 'notes': notes})
        records.append(rec)
        heads[incident] = rec
    check_records(records)
    return records


def atomic_write(path, data):
    fd, temp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def port(path, source, archive_dir, reconcile=False):
    if source.resolve() == path.resolve():
        raise ValueError('source and destination must differ')
    with locked(path):
        data = source.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        existing = read_log(path)
        old_imports = [r for r in existing if r['source'] == 'md-port']
        stamp = old_imports[0]['logged_at'] if old_imports else utc_now()
        if any(r['migration']['file'] != str(source) for r in old_imports):
            raise ValueError('source path differs from existing imports')
        imported = port_records(source, data, stamp, old_imports)
        old_source = ''.join(r['migration']['original_text'] for r in old_imports).encode('utf-8')
        if not data.startswith(old_source):
            raise ValueError('source is not an unchanged byte prefix of the previous import')
        if existing and not reconcile:
            if existing == imported:
                return {'records': len(existing), 'added': 0, 'sha256': digest}
            raise ValueError('destination exists; use --reconcile to preserve it and append a verified source suffix')
        additions = imported[len(old_imports):]
        combined = existing + additions
        check_records(combined)  # Also refuses follow-ups to an incident with a newer live head.
        archive_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        archive = archive_dir / (digest + '.md')
        if archive.exists() and archive.read_bytes() != data:
            raise ValueError('archive hash collision or corruption')
        if not archive.exists():
            fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
        if source.read_bytes() != data:
            raise ValueError('source changed during port; retry against the new source')
        if combined != existing or not path.exists():
            atomic_write(path, b''.join(encode(r) for r in combined))
        return {'records': len(combined), 'imported': len(imported), 'added': len(additions),
                'sha256': digest, 'archive': str(archive)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', type=Path, default=Path(os.environ.get('FRICTION_LOG',
                        str(Path.home() / '.local/state/agent-friction.jsonl'))))
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('log', help='validate and append one JSON object from stdin; print the complete retryable snapshot')
    sub.add_parser('check', help='validate records and incident chains')
    sub.add_parser('latest', help='print latest snapshot per incident; follow-ups are not new incidents')
    p = sub.add_parser('port', help='losslessly import Markdown, preserving original source bytes')
    p.add_argument('source', type=Path)
    p.add_argument('--archive-dir', type=Path, required=True)
    p.add_argument('--reconcile', action='store_true', help='preserve existing events and append only an unchanged-source suffix')
    args = parser.parse_args()
    try:
        if args.command == 'log':
            result = log_record(args.log, json.load(sys.stdin))
        elif args.command == 'port':
            result = port(args.log, args.source, args.archive_dir, args.reconcile)
        else:
            with locked(args.log):
                records = read_log(args.log)
            _, latest = check_records(records)
            result = list(latest.values()) if args.command == 'latest' else {
                'records': len(records), 'incidents': len(latest),
                'imports': sum(r['source'] == 'md-port' for r in records)}
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(1, f'not written: {exc}\n')


if __name__ == '__main__':
    main()
