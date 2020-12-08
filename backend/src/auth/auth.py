import json
from flask import request, _request_ctx_stack , abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'nadia-fsdn.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
    get_token_auth_header() method
    1. Attempt to get the header from the request
    2. Raise an AuthError if no header is present
    3. Split bearer and the token
    4. Raise an AuthError if the header is malformed
    5. Return the token part of the header
'''
def get_token_auth_header():

    if 'Authorization' not in request.headers:
       abort(401)

    auth_header = request.headers['Authorization']
    header_parts = auth_header.split()
    if header_parts[0].lower() != 'bearer':
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(header_parts) != 2:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)

    
    return header_parts[1]

    # ref: https://auth0.com/docs/quickstart/backend/python/01-authorization
'''   
    check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it raises an AuthError if permissions are not included in the payload
        
    it raises an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''

def check_permissions(permission, payload):
    if 'permissions' not in payload:
           abort(400)
    if permission not in payload['permissions']:
        abort(401)
    return True

    # ref: Using RBAC in Flask Lesson

'''
verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    1. An Auth0 token with key id (kid)
    2. Verify the token using Auth0 /.well-known/jwks.json
    3. Decode the payload from the token
    4. Validate the claims
    5. return the decoded payload
'''

def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)

    # CHOOSE OUR KEY
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    # Finally, verify!!!
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms = ALGORITHMS,
                audience = API_AUDIENCE,
                issuer = 'https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)
            
    #ref: Identity and Authentication Lesson
   

'''
@requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    1. it uses the get_token_auth_header method to get the token
    2. it uses the verify_decode_jwt method to decode the jwt
    3. it uses the check_permissions method validate claims and check the requested permission
    4. return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            jwt = get_token_auth_header()
            try:
            
                payload = verify_decode_jwt(jwt)
            except: 
                abort(401) 
                
                
            check_permissions(permission, payload)
            
            return f(jwt, *args, **kwargs)
            
        return wrapper
    return requires_auth_decorator



    #ref: Using RBAC in Flask