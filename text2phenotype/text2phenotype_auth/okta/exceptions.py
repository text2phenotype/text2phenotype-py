from typing import Optional


class OktaClientError(Exception):
    """
    https://developer.okta.com/docs/reference/api-overview/#errors

    All error requests will return with a custom JSON error object:
    {
        "errorCode": "E0000001",
        "errorSummary": "Api validation failed",
        "errorLink": "E0000001",
        "errorId": "oaeHfmOAx1iRLa0H10DeMz5fQ",
        "errorCauses": [
            {
                "errorSummary": "login: An object with this field already exists in the current organization"
            }
        ]
    }
    """

    ERROR_MAP = {
        'E0000001': 'A user with this email already exists'
    }

    def __init__(self, error_json: Optional[dict] = None, msg: Optional[str] = None):
        self.error_json = error_json or {}
        self.msg = msg or ''

    @property
    def error_code(self) -> str:
        return self.error_json.get('errorCode', '')

    @property
    def cause(self) -> str:
        if self.error_json:
            causes = self.error_json.get('errorCauses', [])
            summary = causes[0]['errorSummary'] if causes else ''
            return self.ERROR_MAP.get(self.error_code, summary)
        return ''

    @property
    def summary(self) -> str:
        return self.error_json.get('errorSummary', '')

    def __str__(self):
        parts = []

        if self.msg:
            parts.append(self.msg)

        if self.error_json:
            preffix = 'Details = ' if parts else ''
            parts.append(f'{preffix}{self.error_json}')

        return ', '.join(parts)
