from schemas.auth_schema import LoginRequestDTO, ENDPOINT_DOCS
from exceptions.common_exceptions import ExpiredTokenException, InvalidCredentialsException
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas.input_dto import RequestParameters
from pydantic import BaseModel
from dependencies.sale_point_dependencies import make_session, oauth2_scheme, validate_token
from exceptions.sale_point_exceptions import SalePointNotFound
from services.sale_point_service import login_service, logout_service
from typing import Annotated

class TokenResponseDTO(BaseModel):
    access_token: str
    token_type: str = 'bearer'
auth_router = APIRouter(prefix='/auth', tags=['Auth'])

@auth_router.post('/sessions', status_code=status.HTTP_201_CREATED, response_model=TokenResponseDTO, openapi_extra=ENDPOINT_DOCS['login'])
async def login_auth_controller(http_request: Request, *, session=Depends(make_session, use_cache=False)):
    try:
        form_data = LoginRequestDTO.from_payload(dict(await http_request.form()))
        token = login_service(form_data, session)
        return {'access_token': token, 'token_type': 'bearer'}
    except HTTPException:
        raise
    except InvalidCredentialsException as error:
        raise HTTPException(401, detail=str(error), headers={'WWW-Authenticate': 'Bearer'}) from error
    except SalePointNotFound as error:
        raise HTTPException(404, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error

@auth_router.delete('/sessions/current', status_code=status.HTTP_204_NO_CONTENT, openapi_extra=ENDPOINT_DOCS['logout'])
async def logout_auth_controller(http_request: Request, *, token: Annotated[str, Depends(oauth2_scheme)], user_data=Depends(validate_token), session=Depends(make_session, use_cache=False)):
    try:
        await logout_service(token, session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except ExpiredTokenException as error:
        raise HTTPException(401, detail=str(error), headers={'WWW-Authenticate': 'Bearer'}) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(422, detail=str(error)) from error
