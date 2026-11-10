---
name: create-dev-station
description: "Create a Brev CPU development station, bootstrap it with machine-init through Ansible, and verify the tools needed for remote agent build, test and browser workloads. Use for new or additional dev stations; excludes cluster provisioning and resident agent authentication."
---

# Create Dev Station

Deliver a station with proven workload readiness and a concrete handoff. Default to a 512-GB disk.
Creation needs authorization covering the instance count and spending; this skill is not standing
permission to spend. Reuse authorization already given in the session.

## Local configuration and scope

Read `~/.config/create-dev-station/config.json`. It holds `brev_bin`, `brev_source`, `bootstrap_repo`,
`provider`, `instance_type`, `ssh_user`, and `protected_names`. Optional `org` selects the Brev account
scope; otherwise inspect the active organization. These are local paths and deployment choices, not
secrets. If the file is missing or incomplete, ask once for the missing values and save them privately.
Never commit its contents, inventories, instance IDs or provisioning logs to a public repository.

Establish the requested name/count, workload, per-instance compute and storage caps, and whether the
station is persistent or should be removed after the work. Suggested caps are $0.35/hour compute and
$0.10/hour storage, separately; confirm them only if the session has not already set spending limits.
Record who owns cleanup. Do not infer a shutdown timer from the existence of a spending cap.

Read the bootstrap repository's instructions and inspect its `dev-init` task and role before running
them. The intended path is development setup only, with no cluster join or tailnet enrollment.
Check how the playbook supplies credentials: the established role uses a SOPS-managed read-only
GitHub token for bootstrap and `gh`. Keep that mechanism private; do not print decrypted values or
copy personal publishing or agent-login credentials. If the current playbook would exceed the agreed
credential or host scope, resolve that before applying it.

## Quote and create

1. Inspect live Brev inventory in the selected organization. Reject a name collision; record immutable
   IDs for protected instances and leave them untouched. A failed create must be reconciled against
   inventory before retrying, so an ambiguous response cannot create a second paid instance.
2. Check the configured binary and the binary resolved by `command -v brev`. Inspect `create --help`
   for `--disk-size` and `--dry-run`. Use the installed custom build when it supports both. If it does
   not, inspect the configured source checkout, preserve its changes, and build with its mise-pinned
   Go version into a private artifact directory. Do not silently fall back to the provider's disk
   default, install a competing package, or change the global CLI as a provisioning side effect.
3. Query current CPU offerings with `search cpu --provider ... --json`. Verify type, CPU/RAM, disk
   bounds, compute price and per-GB-month storage price. Estimate hourly storage as
   `disk_GB * price_per_GB_month / 730`, stating that conversion assumption; check both caps separately.
   Do not treat an old quote as current or claim account credit eligibility from an offering price.
   If a price is absent or exceeds a cap, stop before creation and present the concrete alternative.
4. Dry-run the exact selection, then create only after it passes. For zsh, with values read from the
   config and request:

   ```zsh
   args=(create "$station" --type "$instance_type" --provider "$provider" --disk-size "$disk_gb")
   # If configured, append: args+=(--org "$org")
   "$brev_bin" "${args[@]}" --dry-run
   "$brev_bin" "${args[@]}"
   ```

   Record the immutable ID, requested disk, rates and billing start. Bound creation and all readiness
   waits with deadlines; on failure report the instance's actual state and continuing cost. Run each
   long wait as one watcher you own by PID that writes a completion marker on exit, as the user's
   waiting rules and `working-conventions` › Waiting describe; never start a second watcher on the
   same job.

## Connect and bootstrap

Wait for `status=RUNNING`, `build_status=COMPLETED` and `shell_status=READY`, then run `brev refresh`
in the same organization. `HEALTHY` alone can precede SSH readiness.

Use the regular station alias through Brev's gateway. `brev exec --host` and the `-host` alias select
the provider-IP route, which can time out even while the gateway works. Inspect `ssh -G` and use a
bounded BatchMode SSH probe to distinguish endpoint failure from authentication failure. Do not change
firewalls or try stronger credentials to work around a failed probe. Never stop NetBird: Brev's gateway
depends on it. For remote scripts, use `brev exec "$station" @local-script` when supported, or explicitly
pipe to `bash -s`; the remote login shell may be zsh.

Create a private one-host inventory whose host key is the regular gateway alias and whose
`ansible_user` is the configured SSH user. Do not add the station to shared production inventory.
From the bootstrap repository root, select both the play's host pattern and its limit:

```zsh
args=(-i "$inventory" -e "dev_init_hosts=$station" --limit "$station")
mise run dev-init -- --list-hosts "${args[@]}"
# Continue only if the listing contains exactly the intended new host.
mise run dev-init -- "${args[@]}"
```

`--list-hosts` proves selection only; the role does not support Ansible check mode. Require passwordless
sudo and the role's supported OS. Run only the development play, never cluster bring-up. The role
installs Nix, Home Manager and the base CLI environment. Its prerequisites must include `libatomic1`
before Home Manager activation because mise's Node can require `libatomic.so.1`.

## Validate the assigned workload

Verify CPU/RAM, guest-visible disk capacity, OS, and zero failed/unreachable bootstrap tasks.
Confirm Nix, mise and required commands resolve in a fresh noninteractive SSH shell; explicitly load
the installed environment if necessary.

The base role is not a complete compiler or browser image. Before installing project tools, install
`build-essential` for native builds; add `cmake`, `pkg-config`, `libssl-dev`, `zlib1g-dev` only when the
project requires them. Use project-pinned mise tools. Install required tools first; optional Cargo
helpers must not delay a workload that does not use them. Derive the install set from the assigned
tasks' commands and name those tools (`mise install <tool>...`) before any bare `mise install`;
install optional tools only after the readiness checks pass, if the work needs them.

Clone an authorized project revision and record its commit/tree. Prefer anonymous clones for public
source. Transfer only an explicit source allowlist when a patch is needed, checking its hash and
resulting revision; exclude private plans, credentials, ignored artifacts and dependency directories.
Give workers their own source directories and writable caches. Keep the validated baseline clean.
Install locked dependencies into each worker's own writable tree, reusing the package manager's
warm store; symlinking another checkout's mutable `node_modules` does not isolate a worker.
Preserve project workspace links through its normal install command.

Check the tools and configuration the assigned work uses, beyond the compiler:

- If the project uses a tracker, put its supported CLI on PATH and verify the checkout resolves to
  the intended tracker with a read-only query. Supply only the authorized mapping; an installed
  binary with `no-tracker` is not ready for tracked work.
- For browser QA, verify the browser configuration, helper dependencies and current application
  build. Use the supported runner for one representative case, including its result artifact,
  before handing off a batch. A cached binary must match the recorded source revision.
- If committing or publishing is assigned, inspect repository rules, required signing and the
  bootstrap credential's capabilities before the first commit. Verify required signing works in a
  disposable local repository. A read-only bootstrap token does not grant push access. Arrange an
  authorized publication route without copying private keys or trying stronger credentials after
  denial; build/test readiness can be handed off with publication explicitly unproven. Include
  any private pre-push guard the repository requires, such as a deny-list for private details,
  without copying private configuration unless authorized.

Prove each capability separately:

- **Build:** a small compile/link/run smoke for the required native toolchain, then a representative
  project check on the recorded revision. A tool's version output alone does not establish readiness.
- **Browser, when requested:** use the project's pinned browser dependency/install tasks, then launch
  each required engine against local synthetic content and close all contexts/processes. Keep browser
  caches outside source. A smoke does not prove full application journeys passed.
- **Resident agents, when requested separately:** arrange the supported authentication flow with the
  user. Remote build readiness does not imply a logged-in agent or running orchestration daemon.

Track long jobs by their own PID and exit marker, including failures, with a deadline. Stop only owned
processes. Before a long batch, inspect current CPU count/load, memory/swap and other assigned heavy
jobs. Defer or use already authorized quiet capacity when contention would invalidate results; do not
provision extra capacity implicitly. Assign heavy work per validated host; keep cold and warm timings
separate and establish new baselines before making speedup claims. Timings on different hosts do not
by themselves prove a code speedup.

## Handoff and lifecycle

Return the station alias/ID, source revision, installed environment and cache paths, proven capabilities,
remaining checks, hourly cost, elapsed setup time, and cleanup owner/policy. State whether a real
shutdown timer exists. Report partial readiness precisely so a worker can use an accepted capability
without assuming every tool or suite passed.

Retain one private invocation wrapper or environment configuration for task-owned runtime resources.
Use it for creation, workload commands and teardown, including scoped config paths, endpoints and
credentials; cleanup must not fall back to the user's defaults. Record the resource IDs it owns and
capture the relevant default configuration's checksum/state before setup and after teardown. Without
a baseline, leave preservation unproven. This does not authorize cluster provisioning or changes
outside the station's agreed scope.

At authorized cleanup, retain source/evidence first, recheck target and protected IDs in live inventory,
delete only the authorized immutable ID, and poll until it is absent while protected IDs remain.
If deletion is not authorized, hand back the running station and continuing cost explicitly.
