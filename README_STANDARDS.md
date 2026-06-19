# README Standards Overlay (organvm-vii-kerygma)

This file defines local README standards for this organ and acts as an overlay
on top of the system-wide canonical policy.

## Canonical Upstream

Canonical full standards are maintained in:
- `meta-organvm/.github/README_STANDARDS.md`

Overlay rules may add stricter checks but must not weaken canonical
requirements.

## Local Minimum

Every active repository should have:
- a clear README title and purpose/problem section
- setup/usage guidance
- context links where applicable
- contributing and license context

## Enforcement

Run this org's local standards audit script from the superproject root:

`./tools/audit_platform_standards.sh`

Any exception should be tracked with owner and due date.
