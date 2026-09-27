# Local CLI namespace feasibility observation

Observed on 2026-09-27 in the development workspace. `bubblewrap 0.9.0` and `codex-cli 0.157.1` are installed. The resolved Codex executable is a statically linked binary. The following credential-free command exited 0 and printed `codex-cli 0.157.1`:

```sh
bwrap --unshare-all --share-net --die-with-parent --new-session --clearenv \
  --setenv PATH /usr/bin:/bin --dir /usr --dir /usr/bin \
  --ro-bind /path/to/resolved/codex /usr/bin/codex \
  --proc /proc --dev /dev --tmpfs /tmp --chdir /tmp /usr/bin/codex --version
```

The actual probe substituted the local resolved executable for `/path/to/resolved/codex`. No repository, credential, model request, source data, or output artifact was mounted; no model call was made. This proves only that this host can start that CLI binary in a minimal mount/user/PID namespace. `--share-net` retained unrestricted host networking. It does **not** prove a usable Codex model session inside the namespace, a per-job worker, network egress limits, process/output attestation, an independent `execution_verifier`, a signed thermal release, or G1/G4 acceptance. Those remain pending architecture review with the required `gpt-6-sol`/`xhigh` CLI and subsequent implementation/evidence.
