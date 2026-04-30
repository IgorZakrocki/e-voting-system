# Secure Homomorphic E-Voting System

A terminal-based electronic voting system that protects voter privacy by using homomorphic encryption. The application allows eligible voters to cast encrypted yes/no votes for multiple questions or candidates, while the final election results are computed without revealing any individual ballot.

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Contribution](#contribution)
- [License](#license)

## Description

This project implements a secure electronic voting system based on the Paillier cryptosystem. Paillier is an additive homomorphic encryption scheme, which means that encrypted votes can be combined directly, and only the aggregated result needs to be decrypted. As a result, the system can count election results without accessing or exposing the content of individual votes.

The application is designed as a simple terminal program. It uses a lightweight JSON or CSV file as its data storage layer, making it easy to run locally without configuring a full database server. The system supports multiple voting questions or candidates, where each answer is represented as a Boolean value: `yes` or `no`.

A list of authorized voters is maintained by the system. Only voters included in this list are allowed to vote, and each authorized voter can submit a ballot only once. This prevents both unauthorized participation and duplicate voting.

The main goal of the project is to demonstrate how cryptographic mechanisms can be applied to electronic voting in order to improve privacy, integrity, and trust in the vote-counting process.

## Features

- Homomorphic vote encryption using the Paillier cryptosystem.
- Terminal-based application interface.
- Lightweight data storage using JSON or CSV files.
- Support for multiple voting questions or candidates.
- Boolean voting model: each answer is either `yes` or `no`.
- Voter authorization based on a predefined list of eligible voters.
- Protection against duplicate voting by the same authorized voter.
- Encrypted aggregation of votes without revealing individual choices.
- Final result decryption only at the aggregated level.
- Planned automated test suite for validating voting scenarios and edge cases.

## Technologies

- Python
- Paillier cryptosystem
- Homomorphic encryption
- JSON or CSV for local data storage
- Terminal / command-line interface
- `uv` for Python version, virtual environment, and dependency management
- Automated tests, for example with `pytest` planned or recommended

## Installation

The project can be configured with `uv`. This tool is used to manage the Python version, virtual environment, and project dependencies.

### 1. Clone the repository

```bash
git clone https://github.com/user/project-name.git
cd project-name
```

### 2. Install `uv`

#### Linux / macOS

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### Windows PowerShell

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Verify the installation:

```bash
uv --version
```

### 3. Create a virtual environment

```bash
uv venv
```

By default, a `.venv` directory will be created in the project directory.

### 4. Activate the virtual environment

#### Linux / macOS

```bash
source .venv/bin/activate
```

#### Windows

```cmd
.venv\Scripts\activate.bat
```

### 5. Install all dependencies

If the project contains a `pyproject.toml` file, install the dependencies with:

```bash
uv sync
```

### 6. Run the project

After activating the virtual environment, run the application according to its entry point, for example:

```bash
python src/main.py
```

You can also run commands without manually activating the environment by using `uv run`, for example:

```bash
uv run python src/main.py
```

## Usage

The application is operated from the terminal. A typical voting workflow includes the following steps:

1. Load or create the list of authorized voters.
2. Define voting questions or candidates.
3. Generate or load the Paillier public and private keys.
4. Allow each authorized voter to cast one encrypted ballot.
5. Store encrypted votes in a JSON or CSV file.
6. Aggregate encrypted votes for each question or candidate.
7. Decrypt only the final aggregated results.
8. Display the total number of `yes` and `no` votes for each question.

Example use cases:

- Conducting a private yes/no vote for several proposals.
- Running a small election with multiple candidates or questions.
- Demonstrating privacy-preserving vote aggregation using homomorphic encryption.

## Testing

The project should include automated tests that generate voters, simulate voting behavior, and verify correctness of the system. Recommended test scenarios include:

- An authorized voter successfully casts a valid vote.
- An unauthorized person attempts to vote and is rejected.
- An authorized voter attempts to vote more than once and is rejected.
- Multiple voters cast votes for multiple questions.
- The encrypted vote aggregation produces the same result as a plain-text reference calculation.
- The final decrypted results match the expected totals generated during the test setup.
- Invalid or malformed voting data is handled safely.

A recommended test command is:

```bash
uv run pytest
```

## Contribution

Contributions are welcome. Suggested improvements include expanding the automated test suite, improving the command-line interface, adding better input validation, and extending the storage layer.

Before contributing, please make sure that:

- The code is readable and documented where necessary.
- New functionality is covered by tests.
- Existing tests pass successfully.
- Cryptographic logic is not changed without proper verification.

## License

This project is intended for educational and research purposes. Add the final license information according to the repository requirements, for example MIT, Apache 2.0, or another appropriate license.
