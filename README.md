# Yet Another Workflow Management System

```python
workflow = Workflow()

@workflow.rule(
    output="hello.txt",
)
def hello(rule: Rule) -> None:
    with open(rule.output, "w") as f:
        f.write("Hello World!")

workflow.run(
    targets=["hello.txt"],
)
```
