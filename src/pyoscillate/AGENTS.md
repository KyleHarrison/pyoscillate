# pyoscillate Code Standards

These rules apply to all Python code under `src/pyoscillate/`. The
architecture and runtime contracts are detailed in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md),
[`patches/CLAUDE.md`](patches/CLAUDE.md), and the nearest project or patch
instructions. Those documents add domain-specific rules; they do not relax
the scope and ownership rules below.

## Scope and ownership

- Keep authored values and behavior inside the class that owns them. Use
  class attributes for class-level configuration/constants and methods for
  behavior; keep instance state on `self`.
- Do not add module-level variables, constants, mutable state, or functions.
  This includes private helpers and callbacks. Define callbacks as methods on
  their owning class and pass the unbound/static method where a callable is
  required.
- At module scope, use the module docstring, imports, and class definitions.
  Do not add other assignments or function definitions; a framework-required
  exception must be documented at its use site.
- Put shared behavior on the existing class that owns the concept. Do not
  introduce free functions or shared global state as a shortcut for reuse.
- Prefer the narrowest owner: rack-level data and composition belong to its
  `Rack` subclass; patch graph, controls, and runtime state belong to its
  `Patch` subclass; UI behavior belongs under `src/flet/`.

## General implementation rules

- Preserve the layer boundaries in [`../ARCHITECTURE.md`](../ARCHITECTURE.md):
  `pyoscillate/` contains runtime/DSP code and no UI; `flet/` contains UI
  wiring and no DSP implementation.
- Reuse existing abstractions and follow the nearest nested instructions
  before creating a new module, family, or pattern.
- Keep rack modules declarative: subclass `Rack`, configure it with class
  attributes, and compose existing patch instances in `build_groups()`.
- Follow the patch lifecycle, graph ownership, parameter, and timing rules in
  [`patches/CLAUDE.md`](patches/CLAUDE.md); never create or mutate Pyo graph
  nodes outside the lifecycle they specify.
- Use type annotations for public and cross-layer contracts, and keep
  functions and methods focused on one owned responsibility.
- Add or update focused tests for behavioral changes, then run the narrowest
  relevant test and lint checks available.