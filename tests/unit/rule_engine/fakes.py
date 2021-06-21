import re
import unittest
from typing import List
from drone_ci_butler.drone_api.models import (
    Build,
    Step,
    Stage,
    AnalysisContext,
    Output,
    OutputLine,
)
from drone_ci_butler.drone_api.models import AnalysisContext
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
    build_link: str = "https://dummy.drone.com/owner/repo/1337",
    step_name: str = "dummy",
    stage_name="build",
    build_number=1337,
    step_status="failure",
    lines: List[str] = None,
    **kw
):
    fake_build = Build(
        link=build_link,
        number=build_number,
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

    return AnalysisContext(build=fake_build, stage=fake_stage, step=fake_step)
