import re
import unittest
from typing import List
from drone_ci_butler.drone_api.models import (
    Build,
    Step,
    Stage,
    BuildContext,
    Output,
    OutputLine,
)
from drone_ci_butler.drone_api.models import BuildContext
from drone_ci_butler.rule_engine.models import (
    Rule,
    RuleAction,
    Condition,
    RuleSet,
    ConditionSet,
    MatchedCondition,
    MatchedRule,
)


def fake_context_with_output_lines(
    build_link: str,
    step_name: str,
    stage_name="build",
    build_number=42,
    step_status="failure",
    lines: List[str] = None,
    **kw
):
    fake_build = Build(
        link=build_link,
    )
    fake_stage = Stage(name=stage_name)
    fake_step = Step(
        name=step_name,
        status=step_status,
        exit_code=1,
        output=Output(
            lines=[
                OutputLine(
                    time=i,
                    pos=i,
                    out=out,
                )
                for i, out in enumerate(map(str, lines or []))
            ]
        ),
    )

    return BuildContext(build=fake_build, stage=fake_stage, step=fake_step)
