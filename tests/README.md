# Testing

Most tests in this project were generated with the assistance of AI tools and later reviewed, adjusted, and integrated manually.

The goal of these tests is to improve reliability, reduce regressions, and validate expected behavior across retention strategies and backup workflows.

As with any generated code, some tests may evolve over time as the project architecture and implementation details change.

## Running Tests

It is recommended to create and activate a virtual environment (**venv**) before installing dependencies to ensure an isolated and reproducible setup.

### Create a Virtual Environment
Linux / macOS:

```bash
python -m venv venv
```

Windows (PowerShell):
```bash
python -m venv venv
```

### Activate the Virtual Environment
Linux / macOS:

```bash
source venv/bin/activate
```

Windows (PowerShell):
```bash
venv\Scripts\Activate.ps1
```

Windows (CMD):
```bash
venv\Scripts\activate.bat
```

### Upgrade pip
Before installing dependencies, ensure that `pip` is up to date:

```bash
python -m pip install --upgrade pip
```

### Install Project and Test Dependencies
Install all required runtime and development dependencies defined in `pyproject.toml`:

```bash
python -m pip install ".[dev]"
```

### Run the test suite:

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