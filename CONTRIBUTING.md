# Contributing to 389ds-log-analyser

First off, thank you for considering contributing to this project! We welcome any contributions, from bug reports to new features.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/theoweiss/389ds-log-analyser.git
    cd 389ds-log-analyser
    ```
3.  **Set up the development environment:**
    ```bash
    # Create and activate a virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install the project in editable mode with development dependencies
    pip install -e '.[dev]'
    ```

## Running Tests

To ensure that your changes don't break anything, please run the test suite before submitting a pull request:

```bash
pytest
```

## Submitting a Pull Request

1.  Create a new branch for your changes:
    ```bash
    git checkout -b your-feature-or-bugfix-branch
    ```
2.  Make your changes and commit them with a clear, descriptive message.
3.  Push your branch to your fork on GitHub:
    ```bash
    git push origin your-feature-or-bugfix-branch
    ```
4.  Open a pull request from your fork to the main repository.

Thank you for your contribution!
