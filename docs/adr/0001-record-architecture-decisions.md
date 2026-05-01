# ADR 0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2025-01-01
- **Deciders:** Maintainers

## Context

The project needs a lightweight, versioned way to capture **why** significant technical choices were made, separate from day-to-day implementation details.

## Decision

We use [Architecture Decision Records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) in `docs/adr/`, created and linked with `adr-tools` when available, following the workflow in the `manage-adr` skill.

## Consequences

- New contributors can read past decisions in one place.
- We accept the overhead of maintaining ADR files and status when decisions evolve.

## Alternatives considered

- **Design docs only:** Rejected; ADRs are smaller and decision-first.
- **Issue-only tracking:** Rejected; issues are transient compared to `main` history.

## References

- [Michael Nygard: Documenting architecture decisions](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
- [adr-tools](https://github.com/npryce/adr-tools)
