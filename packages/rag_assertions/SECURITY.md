# Security

This package validates grounding against evidence supplied by the caller.

Important trust boundary:

- Supplied evidence may be wrong, stale, incomplete, or malicious.
- `grounded` does not mean universally true.
- Built-in assertions do not call external LLMs or provider APIs.

Once hosted publicly, use the repository's private security advisory process
for vulnerability reports. No private security email address is defined yet.
