
# HTTP input documentation; validation is performed by request DTOs.
ENDPOINT_DOCS = {'login': {'requestBody': {'required': True,
                           'content': {'application/x-www-form-urlencoded': {'schema': {'type': 'object',
                                                                                        'required': ['username',
                                                                                                     'password'],
                                                                                        'properties': {'username': {'type': 'string'},
                                                                                                       'password': {'type': 'string'}}}}}}},
 'logout': {}}

from schemas.input_dto import InputDTO

class LoginRequestDTO(InputDTO):
    username: str
    password: str

    @classmethod
    def from_payload(cls, payload):
        result = super().from_payload(payload)
        if not result.username.strip() or not result.password.strip():
            raise ValueError('Username and password are required')
        return result
