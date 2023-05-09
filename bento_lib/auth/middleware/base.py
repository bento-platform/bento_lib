import jwt
import logging
import requests
import time

from abc import ABC
from jwt import PyJWK, PyJWKSet
from threading import Thread
from typing import FrozenSet, Optional, Tuple

from ..exceptions import BentoAuthException


class BaseAuthMiddleware(ABC):
    def __init__(
        self,
        bento_authz_service_url: str,
        openid_config_url: str,
        openid_aud: str,
        disallowed_algorithms: FrozenSet[str] = frozenset({}),
        drs_compat: bool = False,
        sr_compat: bool = False,
        debug_mode: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self._debug: bool = debug_mode
        self._logger = logger or logging.getLogger(__name__)

        self._drs_compat: bool = drs_compat
        self._sr_compat: bool = sr_compat

        self._bento_authz_service_url: str = bento_authz_service_url

        # Populated by key-rotation thread vvv
        self._jwks: Tuple[PyJWK, ...] = ()
        self._openid_config: Optional[dict] = None
        # ^^^

        self._openid_config_url: str = openid_config_url
        self._openid_aud: str = openid_aud

        self._disallowed_algorithms = disallowed_algorithms

        # initialize key-rotation-fetching background process:
        self._fetch_jwks_background_thread = Thread(target=self._fetch_jwks)
        self._fetch_jwks_background_thread.daemon = True
        self._fetch_jwks_background_thread.start()

    def _fetch_jwks(self):
        while True:
            if not self._openid_config:
                r = requests.get(self._openid_config_url, verify=not self._debug)
                self._openid_config = r.json()

            # Manually do JWK signing key fetching. This way, we can turn off SSL verification in debug mode.

            r = requests.get(self._openid_config["jwks_uri"], verify=not self._debug)
            jwks = r.json()
            jwk_set = PyJWKSet.from_dict(jwks)

            self._jwks = tuple(k for k in jwk_set.keys if k.public_key_use in ("sig", None) and k.key_id)

            time.sleep(60)  # sleep 1 minute

    def verify_token(self, token: str):
        try:
            header = jwt.get_unverified_header(token)
            signing_key = next((k for k in self._jwks if k.key_id == header["kid"]), None)
            if signing_key is None:
                raise BentoAuthException("Could not find signing key")
            if (alg := header["alg"]) is None or alg in self._disallowed_algorithms:
                raise BentoAuthException("Disallowed signing algorithm")
            return jwt.decode(
                token, signing_key.key, algorithms=[signing_key.Algorithm], audience=self._openid_aud)
        # specific jwt errors
        except jwt.exceptions.ExpiredSignatureError:
            raise BentoAuthException("Expired access token")
        # less-specific jwt errors
        except jwt.exceptions.InvalidTokenError:
            raise BentoAuthException("Invalid access token")
        # general jwt errors
        except jwt.exceptions.PyJWTError:
            raise BentoAuthException("Access token error")
        # other
        except Exception:
            raise BentoAuthException("Access token error")
