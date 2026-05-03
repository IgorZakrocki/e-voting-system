# Secure Homomorphic E-Voting System

A terminal-based electronic voting system that protects voter privacy using Paillier homomorphic encryption. The application allows eligible voters to cast encrypted yes/no votes for multiple questions or candidates, while final results are computed without revealing individual ballots.

## Features

- Homomorphic vote encryption using the Paillier cryptosystem.
- Terminal-based voting interface.
- Local JSON file storage for voters, questions, encrypted votes, results, and audit logs.
- Multiple voting questions or candidates.
- Boolean answer model: `yes` / `no`.
- Authorized voter list.
- Duplicate-vote protection per question.
- Encrypted aggregation of votes.
- Decryption only at the aggregated result level.
- Audit logging without storing plaintext vote choices.
- Automated unit and integration tests.

## Project Structure

```text
secure-e-voting/
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .python-version
├── data/
│   ├── voters.json
│   ├── questions.json
│   ├── votes.json
│   ├── results.json
│   └── audit_log.json
├── keys/
│   ├── public_key.json
│   └── private_key.json
├── src/
│   └── secure_e_voting/
│       ├── __init__.py
│       ├── main.py
│       ├── crypto.py
│       ├── models.py
│       ├── repositories.py
│       ├── services.py
│       ├── cli.py
│       └── exceptions.py
├── tests/
│   ├── conftest.py
│   ├── test_crypto.py
│   ├── test_voting.py
│   ├── test_tally.py
│   └── test_integration.py
└── scripts/
    ├── generate_keys.py
    ├── seed_data.py
    ├── run_demo.py
    └── reset_data.py
```

## Technologies

- Python 3.11+
- `phe` for Paillier homomorphic encryption
- `rich` for terminal output
- `pytest` for automated tests
- JSON files as a lightweight persistence layer
- `uv` for Python version, virtual environment, and dependency management

## Installation

The project can be configured with `uv`. This tool is used to manage the Python version, virtual environment, and project dependencies.

### 1. Clone the repository

```bash
git clone https://github.com/user/secure-e-voting.git
cd secure-e-voting
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

By default, this creates a `.venv` directory inside the project directory.

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

If the project contains a `pyproject.toml` file, install dependencies with:

```bash
uv sync
```

### 6. Run the project

After activating the virtual environment, run the application with:

```bash
python -m secure_e_voting.main
```

You can also run commands without manually activating the environment:

```bash
uv run python -m secure_e_voting.main
```

## Usage

Seed sample data and generate Paillier keys:

```bash
uv run python scripts/seed_data.py
```

Run the interactive terminal application:

```bash
uv run python -m secure_e_voting.main
```

Run an automated demonstration:

```bash
uv run python scripts/run_demo.py
```

Reset votes, results, audit logs, and voter state:

```bash
uv run python scripts/reset_data.py
```

Generate a fresh Paillier key pair only:

```bash
uv run python scripts/generate_keys.py
```

## Data Model

### Voters

Each voter is stored in `data/voters.json`:

```json
{
  "voter_id": "voter_001",
  "name": "Alice Smith",
  "voted_questions": []
}
```

The `voted_questions` list prevents duplicate voting on the same question while still allowing the voter to answer other questions.

### Questions

Questions are stored in `data/questions.json`:

```json
{
  "question_id": "q1",
  "text": "Should candidate Alice be accepted?"
}
```

### Votes

Votes are encrypted before being written to `data/votes.json`. The system stores only the encrypted ciphertext and exponent required to reconstruct the encrypted number.

### Results

Final results are stored in `data/results.json` after encrypted votes are aggregated and the final sum is decrypted.

### Audit Log

The audit log stores operational events such as accepted votes, rejected votes, unauthorized attempts, and completed tally operations. It does not store plaintext vote content.

## Testing

Run all tests:

```bash
uv run pytest
```

The test suite includes:

- encryption and decryption tests,
- homomorphic addition tests,
- authorized voter tests,
- unauthorized voter rejection tests,
- duplicate voting tests,
- multiple-question voting tests,
- full election flow integration tests.

## Security Notes

This is an educational project, not a production-ready voting system. It demonstrates the privacy property of homomorphic tallying, but it does not implement all requirements of a real-world election platform, such as strong identity verification, distributed key management, coercion resistance, verifiable ballots, or independent public auditability.

The private key must be protected. In a real system, `keys/private_key.json` must never be committed to a public repository.

## License

MIT License. Replace this section if your project uses a different license.

## New CLI modes

The application can now infer the voting screen from the questions file. If questions look like referendum questions, the UI shows `Tak/Nie`; if the file contains candidates/election items, it shows an election list.

Local TUI with a custom questions file:

```bash
uv run python -m secure_e_voting.main local data/questions.json
```

Backward-compatible shortcut:

```bash
uv run python -m secure_e_voting.main data/questions.json
```

Default local mode still works:

```bash
uv run python -m secure_e_voting.main
```

## Client-server mode

Start the server and pass the questions file path:

```bash
uv run python -m secure_e_voting.main server data/questions.json
```

The server listens on TCP port `8765` and broadcasts discovery packets on UDP port `8766` to `255.255.255.255`. This is the IP-layer equivalent of broadcast discovery, so the client does not need to know the server IP address.

Start a client in the same LAN:

```bash
uv run python -m secure_e_voting.main client
```

Flow:

1. client discovers the server automatically,
2. voter enters name, last 4 PESEL digits, and ID card number,
3. server verifies the voter against `data/voters.json`,
4. server sends the detected voting mode and questions,
5. client submits answers,
6. server records encrypted votes and returns the result summary.

Optional ports:

```bash
uv run python -m secure_e_voting.main server data/questions.json --port 9000 --discovery-port 9001
uv run python -m secure_e_voting.main client --discovery-port 9001
```
