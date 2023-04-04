import json
import requests
import jwt
import time

from threading import Thread
from flask import Flask, request, g
from jwt.algorithms import RSAAlgorithm

from .exceptions import BentoAuthException


class FlaskAuthMiddleware:
    def __init__(
        self,
        app: Flask,
        oidc_iss="https://localhost/auth/realms/realm",
        oidc_wellknown_path="https://localhost/auth/realms/realm/protocol/openid-connect/certs",
        client_id="abc123",
        oidc_alg="RS256"
    ):
        self._app: Flask = app

        self.public_key = None

        self.oidc_issuer = oidc_iss
        self.client_id = client_id
        self.oidc_alg = oidc_alg

        self.oidc_wellknown_path = oidc_wellknown_path

        # initialize key-rotation-fetching background process
        fetch_jwks_background_thread = Thread(target=self.fetch_jwks)
        fetch_jwks_background_thread.daemon = True
        fetch_jwks_background_thread.start()

    def fetch_jwks(self):
        while True:
            r = requests.get(self.oidc_wellknown_path, verify=False)
            jwks = r.json()

            public_keys = jwks["keys"]
            rsa_key = [x for x in public_keys if x["alg"] == self.oidc_alg][0]
            rsa_key_json_str = json.dumps(rsa_key)

            self.public_key = RSAAlgorithm.from_jwk(rsa_key_json_str)

            time.sleep(60)  # sleep 1 minute

    def verify_token_optional(self):
        g.authn = {}
        if request.headers.get("Authorization"):
            self.verify_token()

    def verify_token_required(self):
        g.authn = {}
        if request.headers.get("Authorization"):
            self.verify_token()
        else:
            raise BentoAuthException('Missing access_token !')

    def verify_token(self):
        # Assume is Bearer token
        authz_str_split = request.headers.get("Authorization").split(' ')
        if len(authz_str_split) > 1:
            token_str = authz_str_split[1]
            # print(token_str)

            # use idp public_key to validate and parse inbound token
            try:
                # header = jwt.get_unverified_header(token_str)
                payload = jwt.decode(token_str, self.public_key, algorithms=[self.oidc_alg], audience="account")
            # specific jwt errors
            except jwt.exceptions.ExpiredSignatureError:
                raise BentoAuthException('Expired access_token!')
            # less-specific jwt errors
            except jwt.exceptions.InvalidTokenError:
                raise BentoAuthException('Invalid access_token!')
            except jwt.exceptions.DecodeError:
                raise BentoAuthException('Error decoding access_token!')
            # general jwt errors
            except jwt.exceptions.PyJWTError:
                raise BentoAuthException('access_token error!')
            # other
            except Exception:
                raise BentoAuthException('access_token error!')

            # print(json.dumps(header, indent=4, separators=(',', ': ')))
            # print(json.dumps(payload, indent=4, separators=(',', ': ')))

            g.authn['has_valid_token'] = True

            # parse out relevant roles
            if 'resource_access' in payload.keys() and \
                    str(self.client_id) in payload["resource_access"].keys() and \
                    'roles' in payload["resource_access"][self.client_id].keys():
                roles = payload["resource_access"][self.client_id]["roles"]
                print(roles)

                g.authn['roles'] = roles

        else:
            raise BentoAuthException('Malformed access_token !')
