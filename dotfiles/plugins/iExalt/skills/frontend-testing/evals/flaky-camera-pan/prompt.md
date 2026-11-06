You're working in DIR, a small web app (an org map: nodes on a pannable map, with an inspector panel) and its Playwright journey test `test_select.py` (`conftest.py` serves the app with its production-like backend).

CI reports that this journey is flaky on the phone profile: roughly 1 run in 3 fails, with either
`Locator expected to have text 'Bravo'` / `Actual value: Alpha` or
`Locator expected to have text 'Open Bravo'` / `Actual value: None`.

Find the root cause and fix it so the journey is reliable. You may change the app and the test. Work only inside DIR.
Run the test with: `cd DIR && mise exec -- uv run -q --with playwright --with pytest pytest -q test_select.py`

When you're done, reply with: the root cause, what you changed (and why), and the evidence that it's fixed.
