"""Synthetic contracts at the actual CLI entry point; no private log fixtures."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'friction.py'


def record(event='e1', incident='i1', previous=None):
    return dict(v=1, event_id=event, incident_id=incident, previous_event_id=previous,
                logged_at='2026-01-01T12:00:00Z', date='2026-01-01', source='live',
                repo=None, thread_id='reporter', origin={'thread_id': 'origin', 'event_ref': 'call:1'},
                kind='tool', status='open', summary='An unsupported option failed.',
                evidence=[{'ref': 'call:1', 'note': 'Unknown option returned.'}],
                suggestion='Show supported options in help.')


class CLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / 'friction.jsonl'
        self.source = self.root / 'old.md'
        self.archive = self.root / 'archive'

    def run_cli(self, *args, rec=None, ok=True):
        proc = subprocess.run([sys.executable, '-I', str(SCRIPT), '--log', str(self.log), *args],
                              input=json.dumps(rec) if rec is not None else None,
                              text=True, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode == 0, ok, proc.stdout + proc.stderr)
        return json.loads(proc.stdout) if ok else proc.stderr

    def port(self, reconcile=False, ok=True):
        args = ['port', str(self.source), '--archive-dir', str(self.archive)]
        if reconcile:
            args.append('--reconcile')
        return self.run_cli(*args, ok=ok)

    def test_live_followup_and_latest(self):
        self.run_cli('log', rec=record())
        update = record('e2', previous='e1')
        update.update(status='resolved', resolution={'summary': 'Help fixed.', 'evidence': [
            {'ref': 'commit:example', 'note': 'Help now lists supported options.'}]})
        self.run_cli('log', rec=update)
        self.assertEqual(self.run_cli('check'), {'records': 2, 'incidents': 1, 'contexts': 0,
                                               'chains': 1, 'imports': 0})
        self.assertEqual(self.run_cli('latest'), [update])
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)

    def test_idempotent_retry_and_conflicting_id(self):
        self.run_cli('log', rec=record())
        before = self.log.read_bytes()
        self.run_cli('log', rec=record())
        self.assertEqual(before, self.log.read_bytes())
        bad = record()
        bad['summary'] = 'Different payload.'
        self.run_cli('log', rec=bad, ok=False)
        self.assertEqual(before, self.log.read_bytes())

    def test_canceled_incident_retains_history_and_can_reopen(self):
        initial = record()
        initial['status'] = 'unverified'
        self.run_cli('log', rec=initial)
        prefix = self.log.read_bytes()
        canceled = record('e2', previous='e1')
        canceled.update(status='canceled', cancellation={
            'reason': 'Verification abandoned because the original receipt is unavailable.',
            'evidence': [{'ref': 'audit:receipt', 'note': 'Known archive paths were checked.'}]})
        self.run_cli('log', rec=canceled)
        self.run_cli('log', rec=canceled)
        self.assertTrue(self.log.read_bytes().startswith(prefix))
        self.assertEqual(self.run_cli('latest'), [canceled])
        self.assertEqual(self.run_cli('check', '--actionable'), {
            'records': 2, 'incidents': 1, 'contexts': 0, 'chains': 1, 'imports': 0})
        reopened = record('e3', previous='e2')
        self.run_cli('log', rec=reopened)
        self.assertEqual(self.run_cli('latest'), [reopened])
        self.assertEqual(self.run_cli('check', '--actionable')['records'], 3)

    def test_cancellation_requires_evidence_and_cannot_claim_resolution(self):
        proof = {'reason': 'Original evidence unavailable.',
                 'evidence': [{'ref': 'audit:1', 'note': 'Retention checked.'}]}
        canceled = {**record(), 'status': 'canceled', 'cancellation': proof}
        for edit in ({'cancellation': None}, {'cancellation': {}},
                     {'cancellation': {**proof, 'reason': ' '}},
                     {'cancellation': {**proof, 'evidence': []}},
                     {'cancellation': {**proof, 'extra': True}},
                     {'resolution': {'summary': 'Fixed.', 'evidence': proof['evidence']}},
                     {'status': 'open'}, {'status': 'unverified'},
                     {'record_type': 'context', 'context_of': [], 'status': None, 'kind': 'other'}):
            with self.subTest(edit=edit):
                self.run_cli('log', rec={**canceled, **edit}, ok=False)
        self.assertFalse(self.log.exists())

    def test_stale_and_origin_changes_rejected(self):
        self.run_cli('log', rec=record())
        self.run_cli('log', rec=record('e2', previous='e1'))
        self.assertIn('current incident head', self.run_cli('log', rec=record('e3', previous='e1'), ok=False))
        rec = record('e3', previous='e2')
        rec['origin']['thread_id'] = 'different'
        self.assertIn('origin', self.run_cli('log', rec=rec, ok=False))

    def test_live_validation(self):
        for edit in ({'status': 'resolved'}, {'kind': 'tools'}, {'unexpected': True},
                     {'origin': None}, {'evidence': []}, {'logged_at': '2026-01-01Z'},
                     {'source': 'md-port'}, {'suggestion': None}, {'v': True}):
            with self.subTest(edit=edit):
                rec = record()
                rec.update(edit)
                self.run_cli('log', rec=rec, ok=False)
        self.assertFalse(self.log.exists())

    def test_corrupt_log_never_extended(self):
        for raw in (b'{broken}\n', b'{"partial":', b'\n'):
            self.log.write_bytes(raw)
            self.run_cli('log', rec=record(), ok=False)
            self.assertEqual(self.log.read_bytes(), raw)

    def test_concurrent_writers(self):
        def write(n):
            return self.run_cli('log', rec=record(f'e{n}', f'i{n}'))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(write, range(12)))
        self.assertEqual(self.run_cli('check')['records'], 12)

    def test_port_lossless_deterministic_and_preserves_unknowns(self):
        raw = '\n## 2026-01-01 UTC — example/project\n\nOld prose with no status.\n\n## 2026-01-02 UTC\n- ID: old-1\n- Status: resolved\n- Suggestion: improve help.\n\n## 2026-01-03 UTC\n- ID: old-1\n- Status: open\n'
        self.source.write_text(raw)
        result = self.port()
        records = [json.loads(x) for x in self.log.read_text().splitlines()]
        self.assertEqual(''.join(r['migration']['original_text'] for r in records), raw)
        self.assertIsNone(records[0]['status'])
        self.assertIsNone(records[0]['thread_id'])
        self.assertEqual(records[-1]['previous_event_id'], records[-2]['event_id'])
        self.assertEqual(records[1]['status'], 'resolved')
        self.assertNotIn('resolution', records[1])
        digest = hashlib.sha256(raw.encode()).hexdigest()
        self.assertEqual(result['sha256'], digest)
        self.assertEqual((self.archive / (digest + '.md')).read_bytes(), raw.encode())
        before = self.log.read_bytes()
        self.assertEqual(self.port()['added'], 0)
        self.assertEqual(before, self.log.read_bytes())
        for r in records:
            lines = raw.splitlines(keepends=True)
            m = r['migration']
            self.assertEqual(''.join(lines[m['line_start']-1:m['line_end']]), m['original_text'])

    def test_independent_incidents_are_split(self):
        self.source.write_text('## 2026-01-01\n- First independent issue.\n- Second independent issue.\n\n## 2026-01-01\nIncident: one\nStatus: open\n\nIncident: two\nStatus: unverified\n')
        self.port()
        self.assertEqual(self.run_cli('check')['incidents'], 4)

    def test_explicit_inline_labels(self):
        self.source.write_text('## 2026-01-01 — example/project\n'
            'Incident EXAMPLE-01; reporting conversation/threadID:00000000-0000-0000-0000-000000000001; '
            'status open. Suggestion: improve the contract.\n'
            '## 2026-01-02\nFollow-up ID EXAMPLE-01; Status: unverified.\n')
        self.port()
        records = [json.loads(x) for x in self.log.read_text().splitlines()]
        self.assertEqual(records[0]['incident_id'], 'EXAMPLE-01')
        self.assertEqual(records[0]['status'], 'open')
        self.assertEqual(records[0]['repo'], 'example/project')
        self.assertEqual(records[0]['thread_id'], '00000000-0000-0000-0000-000000000001')
        self.assertEqual(records[0]['suggestion'], 'improve the contract.')
        self.assertEqual(records[1]['previous_event_id'], records[0]['event_id'])
        self.assertEqual(records[1]['status'], 'unverified')

    def test_reconcile_preserves_live_and_rejects_changed_history(self):
        self.source.write_text('## 2026-01-01\nOld report.\n')
        self.port()
        self.run_cli('log', rec=record())
        prefix = self.log.read_bytes()
        with self.source.open('a') as out:
            out.write('## 2026-01-02\nAnother report.\n')
        self.port(ok=False)
        self.assertEqual(self.port(reconcile=True)['added'], 1)
        self.assertTrue(self.log.read_bytes().startswith(prefix))
        self.source.write_text(self.source.read_text().replace('Old report', 'Changed report'))
        before = self.log.read_bytes()
        self.port(reconcile=True, ok=False)
        self.assertEqual(before, self.log.read_bytes())

    def test_reconcile_preserves_old_boundary_for_appended_prose(self):
        self.source.write_text('## 2026-01-01\nOld report.\n')
        self.port()
        before = self.log.read_bytes()
        with self.source.open('a') as out:
            out.write('\nContinuation without a heading.\n')
        self.assertEqual(self.port(reconcile=True)['added'], 1)
        self.assertTrue(self.log.read_bytes().startswith(before))
        records = [json.loads(x) for x in self.log.read_text().splitlines()]
        self.assertEqual(''.join(r['migration']['original_text'] for r in records), self.source.read_text())

    def test_followup_to_import_and_stale_legacy_update(self):
        self.source.write_text('## 2026-01-01\nID: shared\nStatus: open\n')
        self.port()
        old = self.run_cli('latest')[0]
        rec = record('live-update', 'shared', old['event_id'])
        rec['origin'] = old['origin']
        self.run_cli('log', rec=rec)
        with self.source.open('a') as out:
            out.write('## 2026-01-02\nID: shared\nStatus: open\n')
        self.assertIn('current incident head', self.port(reconcile=True, ok=False))

    def test_context_keeps_history_and_links_without_counting_as_incident(self):
        self.source.write_text('## 2026-01-01\nFollow-up fragment.\n')
        self.port()
        old = self.run_cli('latest')[0]
        self.run_cli('log', rec=record())
        prefix = self.log.read_bytes()
        context = record('context', old['incident_id'], old['event_id'])
        context.update(origin=old['origin'], record_type='context', context_of=['i1'],
                       status=None, kind='other', summary='Additional context for i1.')
        self.run_cli('log', rec=context)
        self.assertTrue(self.log.read_bytes().startswith(prefix))
        self.assertEqual(self.run_cli('latest'), [record()])
        self.assertEqual(len(self.run_cli('latest', '--include-context')), 2)
        self.assertEqual(self.run_cli('check', '--actionable'), {
            'records': 3, 'incidents': 1, 'contexts': 1, 'chains': 2, 'imports': 1})

    def test_context_links_and_types_are_checked(self):
        self.run_cli('log', rec=record())
        context = record('c1', 'context')
        context.update(record_type='context', context_of=[], status=None, kind='other')
        for edit in ({'context_of': ['missing']}, {'context_of': ['context']},
                     {'context_of': ['i1', 'i1']}, {'context_of': None},
                     {'context_of': [False]}, {'record_type': 'fragment'},
                     {'status': 'open'}, {'kind': 'tool'}):
            with self.subTest(edit=edit):
                self.run_cli('log', rec={**context, **edit}, ok=False)
        self.run_cli('log', rec=context)
        other = {**context, 'incident_id': 'another', 'event_id': 'c2', 'context_of': ['context']}
        self.run_cli('log', rec=other, ok=False)
        self.run_cli('log', rec={**record('e2', previous='e1'), 'context_of': []}, ok=False)
        linked = {**context, 'incident_id': 'linked', 'event_id': 'c3', 'context_of': ['i1']}
        self.run_cli('log', rec=linked)
        # A target cannot become context while a current context still links to it.
        target = {**context, 'incident_id': 'i1', 'event_id': 'e2', 'previous_event_id': 'e1'}
        self.run_cli('log', rec=target, ok=False)

    def test_actionable_checks_current_heads_without_rewriting_imports(self):
        self.source.write_text('## 2026-01-01\nID: old\nStatus: resolved.\n')
        self.port()
        old = self.run_cli('latest')[0]
        prefix = self.log.read_bytes()
        self.assertIn('resolution', self.run_cli('check', '--actionable', ok=False))
        fixed = record('normalized', 'old', old['event_id'])
        fixed['origin'] = old['origin']
        self.run_cli('log', rec=fixed)
        self.assertTrue(self.log.read_bytes().startswith(prefix))
        self.assertEqual(self.run_cli('check', '--actionable')['incidents'], 1)
        heading = {**fixed, 'event_id': 'heading', 'previous_event_id': 'normalized',
                   'summary': '## Imported heading\nOld report.'}
        self.run_cli('log', rec=heading)
        self.assertIn('complaint summary', self.run_cli('check', '--actionable', ok=False))


if __name__ == '__main__':
    unittest.main()
