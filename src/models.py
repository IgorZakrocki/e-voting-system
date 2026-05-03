from dataclasses import dataclass


@dataclass
class Voter:
    voter_id: str
    name: str
    voted: bool = False


@dataclass
class Question:
    question_id: str
    text: str


@dataclass
class Vote:
    vote_id: str
    voter_id: str
    question_id: str
    encrypted_vote: str
    exponent: int


@dataclass
class ElectionResult:
    question_id: str
    question_text: str
    yes: int
    no: int
    total_valid_votes: int
