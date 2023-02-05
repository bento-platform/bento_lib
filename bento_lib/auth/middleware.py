import json
import requests
import os
import jwt

from flask import request
from jwt.algorithms import RSAAlgorithm

class AuthxFlaskMiddleware():
    def __init__(self, oidc_iss="https://localhost/auth/realms/realm", client_id="abc123", oidc_alg="RS256"):
        print('authx middleware initialized')
        # authx poc
        self.oidc_issuer = oidc_iss
        self.client_id = client_id

        self.oidc_wellknown_path = self.oidc_issuer + "/protocol/openid-connect/certs"

        self.oidc_alg = oidc_alg

        r =requests.get(self.oidc_wellknown_path, verify=False)
        jwks = r.json()

        public_keys = jwks["keys"]
        rsa_key = [x for x in public_keys if x["alg"] == self.oidc_alg][0]
        rsa_key_json_str = json.dumps(rsa_key)
        
        self.public_key = RSAAlgorithm.from_jwk(rsa_key_json_str)

    def verify_token(self):
        print("authx checkup")
        if request.headers.get("Authorization"):
            print("authz header discovered")
            # Assume is Bearer token
            authz_str_split=request.headers.get("Authorization").split(' ')
            if len(authz_str_split) > 1:
                token_str = authz_str_split[1]
                # print(token_str)

                # use idp public_key to validate and parse inbound token
                try:
                    payload = jwt.decode(token_str, self.public_key, algorithms=[self.oidc_alg], audience="account")
                    header = jwt.get_unverified_header(token_str)
                except jwt.exceptions.ExpiredSignatureError:
                    raise AuthXException('Expired access_token!')
                except Exception:
                    raise AuthXException('access_token error!')

                # print(json.dumps(header, indent=4, separators=(',', ': ')))
                # print(json.dumps(payload, indent=4, separators=(',', ': ')))
            
                # TODO: parse out relevant claims/data
                roles = payload["resource_access"][self.client_id]["roles"]
                print(roles)

            else:
                raise AuthXException('Malformed access_token !')
        else:
            raise AuthXException('Missing access_token !')


class AuthXException(Exception):
    def __init__(self, message="Unauthorized", status_code=401):
        super().__init__()
        self.message = message
        self.status_code = status_code