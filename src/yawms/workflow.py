from functools import update_wrapper
from typing import Callable

from yawms.rule import Job, Rule, RuleBody
from yawms.types import PathLike, PathLikeOrCallable, PyTree


class Workflow:
    rules: list[Rule]
    default_rule: Rule | None

    def __init__(self) -> None:
        self.rules = []
        self.default_rule = None

    def rule(
        self,
        *,
        name: str | None = None,
        output: PyTree[PathLike] | None = None,
        input: PathLikeOrCallable | None = None,
        require: PathLikeOrCallable | None = None,
        default: bool = False,
    ) -> Callable[[RuleBody], Rule]:
        def decorated(func: RuleBody) -> Rule:
            rule = Rule(
                workflow=self,
                name=name or func.__name__,
                body=func,
                output=output,
                input=input,
                require=require,
            )
            update_wrapper(rule, func)
            self.rules.append(rule)
            if default:
                self.default_rule = rule
            return rule

        return decorated

    def run(self, *targets: PathLike | Rule | Job) -> None:
        if not len(self.rules):
            raise ValueError("No rules defined")
        if not len(targets):
            targets = ((self.default_rule or self.rules[0]),)

        queue = [self._resolve(target) for target in targets]
        print(queue)
        # while len(queue):
        #     pass

    def _resolve(self, target: PathLike | Rule | Job) -> Job:
        if isinstance(target, Job):
            return target
        elif isinstance(target, Rule):
            return target.resolve()
        else:
            return self._find_rule(target)

    def _find_rule(self, target: PathLike) -> Job:
        for rule in reversed(self.rules):
            try:
                resolved = rule.resolve(target)
            except ValueError:
                continue
            else:
                return resolved
        raise ValueError(f"No rule found for target {target}")
