# Testing

Most tests in this project were generated with the assistance of AI tools and later reviewed, adjusted, and integrated manually.

The goal of these tests is to improve reliability, reduce regressions, and validate expected behavior across retention strategies and backup workflows.

As with any generated code, some tests may evolve over time as the project architecture and implementation details change.

## Running Tests

Install test dependencies:

```bash
python -m pip install pytest
```

Run the test suite:

```bash
python -m pytest tests/ -v
```

## Notes
The current test coverage is still evolving alongside the project itself.

As retention logic and backup strategies expand, additional tests will be added to improve long-term reliability and maintainability.


## Test Scope

Current tests primarily focus on:

- retention strategy behavior and correctness
- backup selection and filtering logic
- edge-case handling (invalid, empty, or partial inputs)
- configuration parsing and environment variable resolution
- consistency of policy outputs across scenarios