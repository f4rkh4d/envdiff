"""Core diff logic for env dictionaries."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiffResult:
    only_in_a: list[str] = field(default_factory=list)
    only_in_b: list[str] = field(default_factory=list)
    different: list[str] = field(default_factory=list)  # keys present in both, differing values
    same: list[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_a or self.only_in_b or self.different)


def diff_envs(a: dict[str, str], b: dict[str, str]) -> DiffResult:
    result = DiffResult()
    keys = sorted(set(a) | set(b))
    for k in keys:
        in_a = k in a
        in_b = k in b
        if in_a and not in_b:
            result.only_in_a.append(k)
        elif in_b and not in_a:
            result.only_in_b.append(k)
        elif a[k] != b[k]:
            result.different.append(k)
        else:
            result.same.append(k)
    return result


@dataclass
class CheckResult:
    missing: list[str] = field(default_factory=list)  # keys in example but not in target
    extra: list[str] = field(default_factory=list)  # keys in target but not in example
    empty: list[str] = field(default_factory=list)  # keys present but with empty string

    @property
    def ok(self) -> bool:
        return not self.missing


def check_against_example(target: dict[str, str], example: dict[str, str]) -> CheckResult:
    r = CheckResult()
    for k in example:
        if k not in target:
            r.missing.append(k)
        elif target[k] == "":
            r.empty.append(k)
    for k in target:
        if k not in example:
            r.extra.append(k)
    r.missing.sort()
    r.extra.sort()
    r.empty.sort()
    return r
