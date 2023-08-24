from pathlib import Path

from yawms.rule import Job
from yawms.workflow import Workflow


def test_basic_workflow() -> None:
    workflow = Workflow()

    @workflow.rule(output="hello.txt")
    def hello(rule: Job) -> None:
        assert isinstance(rule.output, Path)
        with open(rule.output, "w") as f:
            f.write("Hello world!")

    @workflow.rule(name="hello2", input="hello.txt")
    def hello_different_name(rule: Job) -> None:
        print("Hello world (2)!")

    # @workflow.rule(
    #     inputs=lambda rule: open(rule.outputs).read().splitlines(), requires=hello
    # )
    # def final_rule() -> None:
    #     print("Hello world!")

    workflow.run(hello_different_name)
    assert 0
