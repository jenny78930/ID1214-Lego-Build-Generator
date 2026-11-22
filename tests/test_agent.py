"""Agent tests: a fake LLM gives canned replies, OpenSCAD is the real program."""

from types import SimpleNamespace

import pytest

from legogen.agent import extract_code, generate_openscad
from legogen.openscad import find_openscad

GOOD = "```openscad\ncube([6, 4, 3]);\n```"
SYNTAX_ERROR = "```openscad\ncube([1,2,;\n```"
TOO_BIG = "```openscad\ncube([50, 5, 5]);\n```"


class FakeClient:
    """Stands in for anthropic.Anthropic(): returns the replies one by one."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.messages = self  # so that client.messages.create(...) works

    def create(self, **kwargs):
        self.requests.append(list(kwargs["messages"]))  # copy: the list keeps growing
        text = self.replies.pop(0)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)], stop_reason="end_turn")


def have_openscad():
    try:
        find_openscad()
        return True
    except FileNotFoundError:
        return False


needs_openscad = pytest.mark.skipif(not have_openscad(), reason="OpenSCAD not installed")


def test_extract_code():
    assert extract_code("hi\n```openscad\ncube(1);\n```\nbye") == "cube(1);"
    assert extract_code("no code here") is None


@needs_openscad
def test_works_first_try(tmp_path):
    code, stl_path = generate_openscad("a block", tmp_path, client=FakeClient([GOOD]))
    assert code == "cube([6, 4, 3]);"
    assert stl_path.exists()


@needs_openscad
def test_retries_after_errors(tmp_path):
    client = FakeClient([SYNTAX_ERROR, TOO_BIG, GOOD])
    generate_openscad("a block", tmp_path, client=client)
    assert len(client.requests) == 3
    # The 2nd request carries OpenSCAD's error, the 3rd the "too big" complaint.
    assert "Parser error" in client.requests[1][-1]["content"]
    assert "too big" in client.requests[2][-1]["content"]


@needs_openscad
def test_gives_up_after_three_attempts(tmp_path):
    with pytest.raises(RuntimeError):
        generate_openscad("a block", tmp_path, client=FakeClient([SYNTAX_ERROR] * 3))
