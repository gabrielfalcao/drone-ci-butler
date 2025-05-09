from typing import Union, Optional, Iterator
from itertools import chain
from uiclasses import Model
from uiclasses.typing import Property
from term2md.term2md import convert as ansi_to_markdown

from datetime import datetime


class OutputLine(Model):
    __id_attributes__ = ["time", "pos", "out"]
    time: int
    pos: int
    out: str

    def __str__(self):
        return self.to_string()

    def to_string(self):
        if self.out:
            return self.out
        return f"{time}:{pos}:{out}"


class OutputMessage(Model):
    __id_attributes__ = ["message"]
    message: str


class OutputLines(OutputLine.List):
    def __str__(self):
        return "\n".join([str(l.out or "") for l in self])


class Output(Model):
    __id_attributes__ = ["lines", "message"]
    lines: OutputLines
    message: str
    headers: Property[dict]

    def with_headers(self, headers: dict) -> Model:
        self.headers = dict(headers)
        return self

    def to_dict(self, *args, **kwargs) -> dict:
        data = self.serialize(*args, **kwargs)
        data.pop("headers", None)
        return data

    def get_sorted_output_lines(self):
        return [l.out for l in self.lines.sorted(key=lambda l: l.pos)]

    def to_html(self):
        ansi = "\n".join(self.get_sorted_output_lines())
        return ansi

    def to_markdown(self):
        return "\n".join(map(ansi_to_markdown, self.get_sorted_output_lines()))

    def __str__(self):
        if self.lines:
            return str(self.lines)
        return "`<no output>`"

    def to_string(self, prefix: str = "") -> str:
        lines = []
        if self.message:
            lines.append(f"{prefix}{self.message}\r\n")

        for line in self.lines or []:
            lines.append(f"\r{prefix}{line.pos}:{line.out}")

        return "".join(lines)


class Step(Model):
    __visible_attributes__ = [
        "name",
        "status",
        "number",
        "started",
        "stopped",
        "exit_code",
    ]
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
            "status": self.status,
            "started": self.started,
            "stopped": self.stopped,
            "exit_code": self.exit_code,
        }

    def to_string(self, *args, **kw) -> str:
        if self.output:
            return self.output.to_string(*args, **kw)

        return ""

    def to_markdown(self, *args, **kw) -> str:
        if self.output:
            return self.output.to_markdown(*args, **kw)

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
        self.headers = dict(headers)
        return self

    def iter_steps(self) -> Iterator[Step]:
        for stage in self.stages or []:
            for step in stage.steps or []:
                yield step

    @property
    def steps(self) -> Step.List:
        return Step.List(self.iter_steps())

    def get_step_by_number(self, stage_number: int, step_number: int) -> Optional[Step]:
        for stage in self.stages:
            if stage.number != stage_number:
                continue
            for step in stage.steps:
                if step.number == step_number:
                    return step


class AnalysisContext(Model):
    __id_attributes__ = ["build", "state", "step"]
    build: Build
    stage: Stage
    step: Step

    def __str__(self):
        parts = []
        if self.build and self.build.link:
            parts.append(f"build='{self.build.link}'")
        if self.stage and self.stage.number:
            parts.append(f"stage='{self.stage.number}'")
        if self.step and self.step.number:
            parts.append(f"step='{self.step.number}'")
        attrs = ", ".join(parts)
        return f"<AnalysisContext {attrs}>"
