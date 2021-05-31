from typing import Union, Optional
from itertools import chain
from uiclasses import Model
from uiclasses.typing import Property
from datetime import datetime
from drone_ci_butler import events


class OutputLine(Model):
    time: int
    pos: int
    out: str


class OutputMessage(Model):
    message: str


class Output(Model):
    lines: OutputLine.List
    message: str
    headers: Property[dict]

    def with_headers(self, headers: dict) -> Model:
        self.headers = headers
        return self

    def to_dict(self, *args, **kwargs) -> dict:
        data = self.serialize(*args, **kwargs)
        data.pop("headers", None)
        return data

    def to_string(self, prefix: str = "") -> str:
        lines = []
        if self.message:
            lines.append(f"{prefix}{self.message}\r\n")

        for line in self.lines or []:
            lines.append(f"\r{prefix}{line.pos}:{line.out}")

        return "".join(lines)


class Step(Model):
    __visible_attributes__ = ["name", "status", "number"]
    __id_attributes__ = ["id", "step_id", "number"]

    id: int
    step_id: int
    number: int
    name: str
    status: str
    exit_code: int
    started: int
    stopped: int
    version: int

    output: Output

    @property
    def started_at(self):
        if not self.started:
            return
        return datetime.fromtimestamp(self.started)

    @property
    def stopped_at(self):
        if not self.stopped:
            return
        return datetime.fromtimestamp(self.stopped)

    def __ui_attributes__(self):
        return {
            "number": self.id,
            "name": self.name,
            "started": self.started,
            "stopped": self.stopped,
            "exit_code": self.exit_code,
        }

    def to_string(self, *args, **kw) -> str:
        if self.output:
            return self.output.to_string(*args, **kw)

        return ""

    def with_output(self, output: Output) -> Model:
        self.output = output
        return self

    def with_stage(self, stage) -> Model:
        self.stage = stage
        return self


class Stage(Model):
    __id_attributes__ = ["id", "repo_id", "number"]
    __visible_attributes__ = ["name", "status", "number"]
    id: int
    repo_id: int
    build_id: int
    number: int
    name: str
    kind: str
    type: str
    status: str
    errignore: bool
    exit_code: int
    machine: str
    os: str
    arch: str
    started: int
    stopped: int
    created: int
    updated: int
    version: int
    on_success: bool
    on_failure: bool

    steps: Step.List

    @property
    def started_at(self):
        if not self.started:
            return
        return datetime.fromtimestamp(self.started)

    @property
    def finished_at(self):
        if not self.finished:
            return
        return datetime.fromtimestamp(self.finished)

    @property
    def created_at(self):
        if not self.created:
            return
        return datetime.fromtimestamp(self.created)

    @property
    def updated_at(self):
        if not self.updated:
            return
        return datetime.fromtimestamp(self.updated)

    def with_build(self, build) -> Model:
        self.build = build
        return self

    def failed_steps(self) -> Step.List:
        steps = Step.List(self.steps or [])
        failed_steps = steps.filter(lambda step: step.exit_code != 0)
        return failed_steps

    def succeeded_steps(self) -> Step.List:
        steps = Step.List(self.steps or [])
        return steps.filter(lambda step: step.exit_code == 0)

    def __ui_attributes__(self):
        return {
            "number": self.id,
            "name": self.name,
            "started": self.started,
            "stopped": self.stopped,
        }


class Build(Model):
    __id_attributes__ = ["number", "link"]

    id: int
    repo_id: int
    number: int
    status: str
    event: str
    action: str
    link: str
    message: str
    before: str
    after: str
    ref: str
    source_repo: str
    source: str
    target: str
    author_login: str
    author_name: str
    author_email: str
    author_avatar: str
    sender: str
    started: int
    finished: int
    created: int
    updated: int
    version: int

    stages: Stage.List

    headers: Property[dict]

    __visible_attributes__ = ["name", "status", "number"]

    @property
    def started_at(self):
        if not self.started:
            return
        return datetime.fromtimestamp(self.started)

    @property
    def finished_at(self):
        if not self.finished:
            return
        return datetime.fromtimestamp(self.finished)

    @property
    def created_at(self):
        if not self.created:
            return
        return datetime.fromtimestamp(self.created)

    @property
    def updated_at(self):
        if not self.updated:
            return
        return datetime.fromtimestamp(self.updated)

    def __ui_attributes__(self):
        return {
            "number": self.id,
            "link": self.link,
            "message": self.message,
            "started": self.started,
            "finished": self.finished,
        }

    def with_headers(self, headers: dict) -> Model:
        self.headers = headers
        return self

    def failed_stages(self) -> Stage.List:
        stages = self.stages or Stage.List([])
        return stages.filter(lambda stage: stage.on_success)

    def failed_steps(self) -> Step.List:
        stages = self.failed_stages()
        steps = []
        for stage in stages:
            steps.extend(stage.failed_steps())

        return Step.List(steps)

    def get_step_by_number(self, step_number: int) -> Optional[Step]:
        for stage in self.stages:
            for step in stage.steps:
                if step.number == step_number:
                    return step
