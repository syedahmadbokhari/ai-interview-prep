# Release Checklist

- Verify package name availability.
- Run parent and package tests.
- Run configured lint/type checks.
- Build wheel and sdist.
- Run `python -m twine check dist/*`.
- Clean-install the wheel in a fresh environment.
- Verify README rendering.
- Verify license.
- Verify version.
- Verify changelog.
- Create a Git tag.
- Publish to TestPyPI.
- Verify TestPyPI installation.
- Publish to PyPI.
- Create a GitHub release.

Phase 6 stops before external publication.
