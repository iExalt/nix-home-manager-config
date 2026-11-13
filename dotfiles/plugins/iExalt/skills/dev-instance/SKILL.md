---
name: dev-instance
description: "Create, inspect, connect to and destroy isolated development instances from any repository, with companion VMs, browsers and Android phones. Agents stay local and SSH into the instance."
---

# Dev Instance

Read `~/.config/dev-instance/config.json` and
`~/.config/dev-instance/environment.md` first. The JSON contains an absolute
`checkout` path to the private AKE checkout and its explicit `kubectl_context`.
The environment file holds the dev station identity, protected resources,
shared-cache locations and local access prerequisites. If either file is missing
or incomplete, ask the user once for the missing values and save them privately.
Never commit those values or copy pinned image references into a public repository.

Inside a disposable dev instance created for your task, sudo and use of the instance's cluster credential are pre-approved for work within your authorized task; do not ask first. This grant excludes the Mac, long-lived dev stations and other agents' instances, and never overrides a permission denial or classifier block.

Run `dev-instance COMMAND` from any directory. Home Manager installs this wrapper
on PATH; it runs the configured AKE checkout's Mise task with that checkout's
selected tools and environment. Read that checkout's `AGENTS.md` before operating.
The CLI emits success JSON on stdout. Errors are JSON on stderr alongside Mise's
diagnostic lines; preserve both streams after failure.
`ssh NAME` returns connection details;
it does not open an interactive terminal. Use the returned `ssh_proxy_command`
with `ssh`: `ProxyCommand=tailscale nc %h %p` routes the MagicDNS hostname through
Tailscale's daemon rather than the local system DNS. Do not rely on an
interactive shell alias.

The JSON includes the host public key read through the Kubernetes API. Write
`HOST SSH_HOST_KEY` to a temporary `known_hosts` file using that returned key,
then connect with the returned `ssh_identity_file` as `IDENTITY` and
`ssh_target` as `TARGET`:
The CLI selects only an identity whose public key is in the instance ConfigMap;
`IdentitiesOnly=yes` prevents unrelated agent keys exhausting authentication attempts.

```sh
ssh -F /dev/null -o 'ProxyCommand=tailscale nc %h %p' \
  -o IdentitiesOnly=yes -i IDENTITY \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=FILE TARGET
```

## Disposable workspace

1. Render without cluster access:
   `dev-instance create NAME --dry-run`.
2. Create: `dev-instance create NAME`.
   Omit `NAME` for a generated name. The CLI waits up to 60 seconds for an
   authenticated SSH command as uid 1000 before reporting ready. Pre-pull the
   selected image before measuring create-to-SSH against that target.
3. Inspect: `dev-instance list`.
   Disposable and long-lived instances appear separately. Workspace bytes are
   logical filesystem usage and quota-visible capacity, not physical ZFS pool
   allocation or compressed bytes. Missing usage is `null` with an error.
4. Get connection details: `dev-instance ssh NAME`.
5. Preview removal: `dev-instance destroy NAME --dry-run`.
   Destroy: `dev-instance destroy NAME`.
   It waits for the namespace and its binding to disappear, without forcing
   finalizers. Deleting the Service lets the Tailscale operator remove its device.

Defaults are 4 CPU, 16Gi memory, and a thin-provisioned 1Ti workspace refquota.
Use `--cpus N`, `--memory SIZE`, `--disk SIZE` and `--gpu` to override them.
CPU and memory have requests without limits. GPU takes one station time slice.
Every instance has KVM, `/dev/net/tun`, `NET_ADMIN` and `NET_RAW`.
Guests share the instance's CPU and memory budget.

Use the pinned image from the AKE checkout's config; `--gpu` selects its GPU
variant. Public login keys come from this machine's `~/.ssh/id_*.pub` files.
Local private keys and decrypted credentials never enter rendered instance
manifests or printed CLI JSON. Credentials are projected separately; optional
push and binary-cache credentials may be absent.

Shared caches are separate mounts from the workspace, so tools may copy instead
of hardlinking. Read their locations in the private environment file. Keep
checkouts, build outputs, homes and credentials private. Existing Git mirrors
are read-only to instances and are never pruned by this CLI. Run helpers inside
the instance or a sidecar; separate Pods cannot share a mounted workspace.

Fresh instances need repository-specific setup. Install the repository's declared
tools and dependencies yourself, including test runners, using its selected Mise
environment; missing tools are expected setup, not an instance failure.

## Companion VM

Use a VM for a full guest OS: systemd, kernel modules, nested containers, or
testing Ansible roles. Use the main container for ordinary builds and checkouts.

Each instance supports one companion VM. The station admits at most eight
**disposable instances**, including Pending and Terminating namespaces;
long-lived instances are outside that cap. There is no separate VM-count quota.
Three simultaneous VMs have been verified within 16 CPU / 64Gi of total instance
requests: one 8 CPU / 16Gi guest in a 10 CPU / 32Gi instance and two 1 CPU / 4Gi
guests in 3 CPU / 16Gi instances. Eight is an admission cap, not a demonstrated
VM capacity. Additional VMs must fit the station's remaining CPU and memory
requests; the KVM device plugin's advertised device count is not a capacity test.

- Create both: `dev-instance create NAME --vm`.
  `--cpus` and `--memory` describe the whole instance request envelope.
  Guest defaults are 2 CPU / 4Gi; override with `--vm-cpus` and `--vm-memory`.
  A guest reserves another 250m CPU and 1Gi for its launcher (2Gi when guest
  memory exceeds 8Gi). Default 4 CPU / 16Gi therefore leaves main 1750m / 11Gi.
  The CLI requires at least 1 CPU / 2Gi for main before creating anything.
- A requests-only `instance-budget` quota covers each new namespace. It limits
  admitted requests; CPU and memory usage may burst. Later VM starts must fit
  available quota. A plain instance has no reserved guest headroom; recreate
  with `--vm` rather than expecting a silent pod resize or quota expansion.
- Main SSH has its original 60-second deadline. A VM create has one 90-second
  deadline including main and guest readiness. Root `timing` measures the whole
  create; nested `vm.timing` measures only the guest helper's phase.
- Inspect or control an existing companion with
  `dev-instance guest NAME vm status`, `... vm stop`, or `... vm start`.
  Start without shape flags uses the recorded guest shape. Explicit mismatches
  preserve the existing VM. Status and stop use stored identity without loading
  a new image configuration or requiring a local SSH private key.
- VM writes are ephemeral: stop/start discards them. Copy needed files back to
  the main workspace before stopping. Stop retains the main resource split;
  namespace destruction removes the VM and its bootstrap state.

The backend uses the pinned VM image and guest shape/login configuration from
the AKE checkout. An absent artifact fails before creation; do not add a
placeholder. Pre-pull the selected VM and main images before measuring cached
startup targets. A stock OS proof fixture does not establish production-image
parity. Guest-only SSH bootstrap uses public login keys and generated host keys;
no external credentials, service-account token or main workspace/home is mounted
in the guest.

The guest has a private SSH Service reached through main. Use the returned guest
`ssh` fields, including `proxy_jump`, `jump_proxy_command`, `jump_identity_file`,
`jump_host_key`, guest `host_key` and `host_key_alias`. For create these are under
`vm.ssh`; guest commands return them under `ssh`. Metadata unavailable after a
completed status/stop is explicit as `jump_metadata_available: false`.

Pin both public keys in `KNOWN_HOSTS_FILE` as `jump-NSUID MAIN_HOST_KEY` and
`vm-NSUID GUEST_HOST_KEY`. Populate both hosts and their users in `SSH_CONFIG`
from the JSON;
the jump has its own identity, transport and pin:

```sshconfig
Host JUMP_HOST
  User JUMP_USER
  ProxyCommand tailscale nc %h %p
  IdentityFile MATCHED_IDENTITY
  IdentitiesOnly yes
  HostKeyAlias jump-NSUID
  UserKnownHostsFile KNOWN_HOSTS_FILE
  StrictHostKeyChecking yes

Host vm-NAME
  HostName PRIVATE_GUEST_SERVICE_DNS
  User GUEST_USER
  Port 22
  ProxyJump JUMP_USER@JUMP_HOST
  IdentityFile MATCHED_IDENTITY
  IdentitiesOnly yes
  HostKeyAlias vm-NSUID
  UserKnownHostsFile KNOWN_HOSTS_FILE
  StrictHostKeyChecking yes
```

Connect with `ssh -F SSH_CONFIG vm-NAME`. Do not rely on the Mac's system
resolution for the jump, an interactive shell alias, or unpinned host keys.
For a read-only guest check, use
`ssh -F SSH_CONFIG vm-NAME 'id -u; uname -m; ps -p 1 -o comm='`.
The production guest should report uid 1000, `aarch64` and `systemd`.
Use the same SSH configuration for Ansible, for example
`ansible -i 'vm-NAME,' all -m ping --ssh-common-args='-F SSH_CONFIG'`.
Ansible ping checks connectivity and Python; it does not validate a full role.

On a failed or uncertain create, preserve the instance and inspect
`guest NAME vm status` before deciding what to restart or destroy.

## Browsers

Run Playwright Chromium in the main container after the project's browser
dependency setup. Run WebKit in a [companion VM](#companion-vm): create with
`--vm`, connect with the pinned guest SSH configuration above, and check
`getconf PAGESIZE` reports `4096`. Run both the app server and browser tests
inside the guest; its loopback, filesystem and browser cache are separate from
main. Copy retained outputs back before stopping it.

The station's main container reports `65536` (64 KiB pages). Playwright 1.64.0's
WebKit 2370 aborts there with exit 134, while the same build passes desktop and
phone-emulation navigation in the 4 KiB guest. Page-size incompatibility is the
inferred cause: [upstream WebKit defaults to a 16 KiB ceiling on Linux
ARM64](https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/PageBlock.h).
Changing the host kernel is outside this route. Phone emulation does not prove
Safari on a real iPhone.

The VM image includes the system libraries and fonts required by Playwright
1.64.0 WebKit. Its ARM64 apt sources already use the Ubuntu 26.04 repositories;
no sources edit or system-dependency installation is needed. Install the browser
binary with the project's pinned Playwright version, for example:

```sh
uv run --no-project --with playwright==1.64.0 \
  python -m playwright install webkit
```

Follow the project's selected runtime and checks inside the guest.

## Android phone (Cuttlefish)

Create with `dev-instance create NAME --cuttlefish`; add `--dry-run`
to preview. This prepares main SSH and an idle sidecar, not a booted phone:
create returns `cuttlefish.state: idle` and `cuttlefish.android_ready: false`.
`--vm` and `--cuttlefish` are mutually exclusive; Cuttlefish cannot use `--resume`.

- Start Android: `dev-instance guest NAME cuttlefish start`.
- Inspect: `dev-instance guest NAME cuttlefish status`.
- Stop: `dev-instance guest NAME cuttlefish stop`.

Start has one 600-second budget; status and stop each have 60 seconds. A shorter
caller deadline still applies. Results include `state`, `ready`, `adb_serial`,
`profile`, `artifact_sha256` and `resources`. Start waits for ADB device state and
`sys.boot_completed=1`; success adds `timing.operation_to_boot_seconds`.
An uncertain outcome preserves the instance: inspect status before retrying.
Status and stop use stored identity; start requires the reviewed artifact/profile
in the AKE checkout's guest config and matching pinned phone image. The immutable
artifact must already be in the read-only phone cache identified in the private
environment file; guests do not download it at launch.

Disposable phone instances default to an 8 CPU / 16Gi total budget; smaller totals
are rejected. Override the total with `--cpus` and `--memory`, not VM sizing flags.
Main requests 1 CPU / 2Gi without CPU or memory limits. The sidecar gets the
remainder with equal requests and limits and owns the single KVM allocation.
Android uses at most 4 vCPUs / 8192 MiB, reserving 1 CPU / 2048 MiB from the
sidecar budget for host tools. The sidecar shares the workspace and read-only CVD
cache, with no mounted credentials or API token; main retains its intentional
cluster-admin access. The eight-disposable-instance cap also covers phones;
maximum phone density has not been demonstrated.

Reach ADB inside the instance's sidecar. There is no ADB Service or CLI port
forwarding. First copy a verified, signed APK over main SSH using the returned
target, with the
pinned connection described above (the same options work for `scp`):

```sh
scp -F /dev/null -o 'ProxyCommand=tailscale nc %h %p' \
  -o IdentitiesOnly=yes -i IDENTITY \
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile=FILE \
  app.apk TARGET:/workspace/app.apk
```

Do not use `kubectl cp` into the sidecar: its root tar cannot write the dev-owned
workspace under this capability profile. Do not add a DAC bypass. Use the
sidecar's ADB as uid/gid 1000 with its private server socket. From the Mac, this
helper executes there. Load the checkout and explicit context from private
configuration; replace `NAMESPACE` with the returned namespace:

```sh
config=~/.config/dev-instance/config.json
checkout=$(mise exec jq@1.8.1 -- jq -er \
  '.checkout | select(type == "string" and length > 0)' \
  "$config")
context=$(mise exec jq@1.8.1 -- jq -er \
  '.kubectl_context | select(type == "string" and length > 0)' \
  "$config")
```

Run only when both reads succeed. Never rely on or change the global context.

```sh
phone_adb() {
  mise -C "$checkout" exec -- kubectl --context "$context" \
    -n NAMESPACE exec dev-0 -c cuttlefish -- \
    python3 -c 'import os, sys
os.setgroups([])
os.setgid(1000)
os.setuid(1000)
os.execvpe("adb", ["adb", *sys.argv[1:]], {
    **os.environ, "HOME": "/workspace/.dev-guest/cuttlefish/home",
    "PATH": "/workspace/.dev-guest/cuttlefish/host/bin:/usr/bin:/bin",
    "ADB_SERVER_SOCKET": "localfilesystem:/workspace/.dev-guest/cuttlefish/adb.sock",
    "ADB_MDNS": "0"})' "$@"
}
phone_adb connect 127.0.0.1:6520
phone_adb -s 127.0.0.1:6520 install -r /workspace/app.apk
phone_adb -s 127.0.0.1:6520 shell am start -W -n PACKAGE/ACTIVITY
```

Use the returned `adb_serial` (currently `127.0.0.1:6520`) and your APK's actual
package/activity. Stop/start retains synced guest data, but stop is not graceful
Android shutdown and does not guarantee unsynced writes. A sidecar restart blocks
further guest operations: preserve needed data and recreate the instance rather
than adopting a new generation.

Ordinary `cluster.local` resolution is unsupported with the default Android
Private DNS behavior; a successful crafted UDP/53 query does not establish OS
resolver behavior. Guest HTTP response content remains unproven. The 60-second
create-to-SSH target is not guaranteed, even though create enforces that deadline.
Tablet, optional GPU rendering, maximum density and endurance remain unproven.

## Recovery and boundaries

Creation never adopts an existing namespace or binding. A partial failure
preserves its namespace and reports the UID when known. Inspect with `list`,
retry SSH lookup, or explicitly destroy the disposable instance. A failed or
timed-out request may have reached the server: inspect the reported namespace
before retrying creation under another name.

`destroy` refuses long-lived instances. For long-lived lifecycle, stuck locks,
PVC/image maintenance and audits, use the private AKE `dev-instance-ops` skill.
Never clear locks by elapsed time or bypass resource identity guards.

Before a live proof, refresh the configured checkout's published contracts and
check the rendered SSH Service's named ProxyClass exists and is Ready. A stale
checkout can reference infrastructure that has already migrated. Run tests only
on the configured dev station through an instance. Leave all protected resources
listed in the private environment file untouched, including retained data,
networking, unrelated hosts and station leases.

There is no automatic expiry or instance deletion. Record cleanup ownership and
explicitly destroy your disposable instance when finished. Orphan reporting does
not authorize deletion. Live performance, image startup, storage, credential
delivery and cleanup proofs must wait for their tracked dependencies; unit tests
render and exercise the CLI without cluster access.
