import json
import io
import requests
from chemist import (
    Model, db
)
from datetime import datetime
from .base import metadata


def load_json(what, default=None) -> str:
    try:
        return json.loads(what)
    except (json.JSONDecodeError):
        return default


class HttpInteraction(Model):
    table = db.Table('http_interaction',metadata,
        db.Column('id', db.Integer, primary_key=True),

        db.Column('request_url', db.String(255), nullable=False, unique=True),
        db.Column('request_method', db.String(10), nullable=False),
        db.Column('request_headers', db.UnicodeText()),
        db.Column('request_params', db.UnicodeText()),
        db.Column('request_body', db.UnicodeText()),

        db.Column('response_status', db.Integer),
        db.Column('response_headers', db.UnicodeText()),
        db.Column('response_body', db.UnicodeText()),

        db.Column('created_at', db.DateTime, default=datetime.utcnow),
        db.Column('updated_at', db.DateTime, default=datetime.utcnow)
    )

    def response(self) -> requests.Response:
        response = requests.Response()
        response.status_code = self.response_status
        response.raw = io.BytesIO(bytes(self.response_body, 'utf-8'))
        response.headers = load_json(self.response_headers, {})
        return response

    def request(self) -> requests.Request:
        request = requests.Request(
            method=self.request_method,
            url=self.request_url,
            headers=load_json(self.request_headers, {}),
            data=load_json(self.request_body, {}),
            params=load_json(self.request_params, {}),
        )
        request.url = self.request_url
        request.method = self.request_url
        request.body = self.request_body
        request.headers = load_json(self.request_headers)
        return request

    @classmethod
    def get_by_requests_request(model, request: requests.Request):
        return model.get_by_url_and_method(
            method=request.method,
            url=request.url,
        )

    @classmethod
    def get_by_url_and_method(cls, url: str, method: str):
        return cls.find_one_by(
            request_url=url,
            request_method=method,
        )


    @classmethod
    def upsert(cls, request: requests.Request, response: requests.Response):
        interaction = cls.get_or_create(
            request_url=request.url,
            request_method=request.method,
        )

        return interaction.update_and_save(
            request_headers=json.dumps(dict(request.headers)),
            request_body=request.body,
            response_headers=json.dumps(dict(response.headers)),
            response_status=response.status_code,
            response_body=response.text
        )
