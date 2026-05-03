class VotingError(Exception):
    """Base exception for voting-related errors."""


class UnauthorizedVoterError(VotingError):
    """Raised when a voter is not authorized to vote."""


class VoterAlreadyVotedError(VotingError):
    """Raised when a voter tries to vote more than once for the same question."""


class InvalidQuestionError(VotingError):
    """Raised when a question does not exist."""


class InvalidVoteValueError(VotingError):
    """Raised when the vote value is not valid."""


class KeyNotFoundError(VotingError):
    """Raised when Paillier keys are missing or invalid."""
