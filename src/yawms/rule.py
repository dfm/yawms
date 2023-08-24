from pathlib import Path
from typing import TYPE_CHECKING, Callable

import optree
from optree.typing import PyTree

from yawms.types import PathLike, PathLikeOrCallable
from yawms.wildcard import Wildcard, WildcardError, apply_wildcards

if TYPE_CHECKING:
    from yawms.workflow import Workflow

RuleBody = Callable[["Job"], None]


class Rule:
    workflow: "Workflow"
    name: str | None
    body: RuleBody | None
    output: PyTree[Wildcard] | None
    input: PathLikeOrCallable | None
    require: PathLikeOrCallable | None

    def __init__(
        self,
        *,
        workflow: "Workflow",
        body: RuleBody | None = None,
        name: str | None = None,
        output: PyTree[PathLike] | None = None,
        input: PathLikeOrCallable | None = None,
        require: PathLikeOrCallable | None = None,
    ) -> None:
        self.workflow = workflow
        self.name = name
        self.body = body
        self.output = (
            optree.tree_map(
                lambda p: (
                    Wildcard(p.as_posix()) if isinstance(p, Path) else Wildcard(p)
                ),
                output,
            )
            if output is not None
            else None
        )
        self.input = input
        self.require = require

    def __repr__(self) -> str:
        return f"<Rule {self.name}>"

    def set_input(self, input: PathLikeOrCallable) -> None:
        self.input = input

    def set_require(self, require: PathLikeOrCallable) -> None:
        self.require = require

    def resolve(self, target: PathLike | None = None) -> "Job":
        if target is None:
            if self.output is None:
                num_wildcards = 0
            else:
                num_wildcards = sum(
                    len(w.names) for w in optree.tree_flatten(self.output)[0]
                )
            if num_wildcards:
                raise ValueError(
                    "Cannot resolve rule with no target when output wildcards are "
                    "required"
                )
            return Job(self, {})

        if self.output is None:
            raise ValueError(
                "Cannot resolve rule with target when output is not specified"
            )

        if isinstance(target, Path):
            target = target.as_posix()
        for wildcard in optree.tree_flatten(self.output)[0]:
            matches = wildcard.match(target)
            if matches is not None:
                return Job(self, matches)

        raise ValueError(f"Path {target} does not match rule {self}")

    def __call__(self, target: PathLike | None = None) -> None:
        self.resolve(target=target)()


class Job:
    wildcards: dict[str, str]
    workflow: "Workflow"
    name: str | None
    body: RuleBody
    output: PyTree[Path | PyTree[Path]] | None

    def __init__(self, rule: Rule, wildcards: dict[str, str]) -> None:
        self.wildcards = wildcards
        self.workflow = rule.workflow
        self.name = (
            apply_wildcards(wildcards, rule.name) if rule.name is not None else None
        )
        self.body = rule.body or (lambda *_: None)
        self.output = (
            optree.tree_map(lambda o: self._apply_wildcards(o.pattern), rule.output)
            if rule.output is not None
            else None
        )
        self._input = rule.input
        self._require = rule.require

    def __repr__(self) -> str:
        return f"<Job {self.name}>"

    def __hash__(self) -> int:
        flat: list[Path] = optree.tree_flatten(self.output)[0]  # type: ignore
        return hash(tuple(p.as_posix() for p in flat))

    def __call__(self) -> None:
        self.body(self)

    def _apply_wildcards(self, pattern: PathLikeOrCallable) -> Path | PyTree[Path]:
        if callable(pattern):
            tree = pattern(self.wildcards)
            return optree.tree_map(Path, tree)
        elif isinstance(pattern, Path):
            return Path(apply_wildcards(self.wildcards, pattern.as_posix()))
        else:
            if TYPE_CHECKING:
                assert isinstance(pattern, str)
            return Path(apply_wildcards(self.wildcards, pattern))

    @property
    def input(self) -> PyTree[Path | PyTree[Path]] | None:
        if self._input is None:
            return None
        try:
            return optree.tree_map(self._apply_wildcards, self._input)
        except WildcardError as e:
            raise ValueError(
                "Could not resolve 'input' wildcards from output paths; "
                f"needed wildcard {e.name}, but only found:\n"
                + "\n".join(f"- {k} = {v}" for k, v in self.wildcards.items())
            ) from None

    @property
    def require(self) -> PyTree[Path | PyTree[Path]] | None:
        if self._require is None:
            return None
        try:
            return optree.tree_map(self._apply_wildcards, self._require)
        except WildcardError as e:
            raise ValueError(
                "Could not resolve 'require' wildcards from output paths; "
                f"needed wildcard {e.name}, but only found:\n"
                + "\n".join(f"- {k} = {v}" for k, v in self.wildcards.items())
            ) from None
