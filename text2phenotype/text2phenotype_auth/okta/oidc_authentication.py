import base64
import hashlib
import json
import os
import requests
import uuid
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Dict,
    List,
    Tuple,
)
from urllib.parse import quote_plus
from django.shortcuts import reverse
from django.db import transaction
from django.contrib import messages
from jose import jwt
from jose.exceptions import (
    ExpiredSignatureError,
    JWTClaimsError,
    JWTError,
)
from text2phenotype.common.log import operations_logger
from text2phenotype.text2phenotype_auth.models.text2phenotype_user import Text2phenotypeUser
from text2phenotype.text2phenotype_auth.models.email import EmailAddress
from text2phenotype.text2phenotype_auth.models.text2phenotype_group import Text2phenotypeGroup
from text2phenotype.text2phenotype_auth.models.oauth2_flow import OAuth2Flow
from text2phenotype.text2phenotype_auth.okta.auth_constant import (
    Applications,
    AppNameDB2Okta,
    AppNameOkta2DB
)
from text2phenotype.text2phenotype_auth.okta.constants import OktaConstants


class BaseOpenIDConnectClient:
    CALLBACK_VIEW_NAME = ''
    FRONTEND_CALLBACK_PATH = ''
    CONFIG_URI = ''
    RESPONSE_TYPE = 'code'
    SCOPES = ['openid']
    USER_MODEL = Text2phenotypeUser
    EMAIL_MODEL = EmailAddress
    LOGIN_FUNC = None
    LOGIN_URL = ''

    EXTRA_AUTH_PARAMS = dict()

    def __init__(self, request: requests.request, client_id: str,
                 client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.request = request
        self.auth_endpoint = None
        self.token_endpoint = None
        self.issuer = None
        self.jwks_uri = None
        self._success_redirect = None
        self._configure_from_discovery_doc()

    @transaction.atomic
    def oidc_user_login_workflow(self, claims: Dict, tokens: Dict) -> Tuple[Text2phenotypeUser, str]:
        emails = []
        if 'email' in claims:
            emails = [claims['email']]
        elif 'emails' in claims:
            emails = claims['emails']

        user = self._find_user(claims['sub'], emails)
        if user and user.is_deleted:
            messages.add_message(self.request, messages.ERROR,
                                 'This user has been deleted. Please contact your account administrator.')
            return user, self.LOGIN_URL

        if not user:
            user = self._setup_new_user(claims)
        else:
            self._update_existing_user(user, claims)

        self._update_user_emails(user, emails)

        if user and not user.is_active:
            messages.add_message(self.request, messages.ERROR,
                                 'This user has been disabled. Please contact your account administrator.')
            return user, self.LOGIN_URL

        # After migration on Cyan Okta tenant, user's groups now comes in the "text2phenotype-groups" claim
        role_groups = claims.get(OktaConstants.TEXT2PHENOTYPE_GROUPS_CLAIM, [])

        # This for backwards compatibility. Check the previous "role-groups" claim
        # TODO: When we don't need to support both schemes the old one could be removed
        if not role_groups:
            role_groups = claims.get(OktaConstants.ROLE_GROUPS_CLAIM, [])

        groups_without_prefix = set((':').join(r.split(':')[1:]) for r in role_groups)
        db_groups = set(f'{AppNameDB2Okta.get(g.application)}:{g.name}' for g in Text2phenotypeGroup.objects.filter(users=user))
        if db_groups.symmetric_difference(groups_without_prefix):
            self._update_user_groups(user, role_groups)

        # Ensure that current session exists in the DB
        if not self.request.session.session_key:
            self.request.session_key.save()

        self.LOGIN_FUNC(self.request, user)

        return user, self._success_redirect

    @staticmethod
    def robust_b64_url_decode(val: str) -> str:

        padding = len(val) % 4
        val += '=' * padding
        res_val = base64.urlsafe_b64decode(val)

        return res_val.decode('utf-8')

    def prep_authorization_url(self):

        if self.request.session.is_empty():
            self.request.session.create()

        # Define State and Nonce and save for later
        # https://developers.google.com/identity/protocols/OpenIDConnect#createxsrftoken
        flow, _ = OAuth2Flow.objects.get_or_create(session_id=self.request.session.session_key)
        flow.state = hashlib.sha256(os.urandom(1024)).hexdigest()
        flow.nonce = uuid.uuid1().hex
        flow.redirect_url = self.request.POST.get('nextPath', '/patient/')
        flow.save()

        # Prep URL parameters
        redirect_uri = self._get_redirect_uri()
        redirect_uri = quote_plus(redirect_uri, encoding="utf-8")

        scopes = quote_plus(" ".join(self.SCOPES), encoding="utf-8")

        extras = ''
        for k, v in self.EXTRA_AUTH_PARAMS.items():
            extras += f'&{k}={v}'

        first_char = '&' if '?' in self.auth_endpoint else '?'

        full_url = (f'{self.auth_endpoint}'
                    f'{first_char}client_id={self.client_id}'
                    f'&redirect_uri={redirect_uri}'
                    f'&state={flow.state}'
                    f'&nonce={flow.nonce}'
                    f'&scope={scopes}'
                    f'&response_type={self.RESPONSE_TYPE}'
                    f'{extras}')

        operations_logger.debug(f'OIDC URL: {full_url}')

        return full_url

    def process_oauth_callback(self) -> Tuple[Dict, Dict]:
        flow = self._get_flow()
        tokens = self._fetch_tokens()
        claims = self._verify_id_token(tokens.get('id_token'),
                                       tokens.get('access_token'),
                                       flow)

        self._success_redirect = flow.redirect_url
        flow.delete()

        return claims, tokens

    def _check_at_hash_claim(self, id_token):
        payload = id_token.split('.')[1]
        claims = json.loads(self.robust_b64_url_decode(payload))
        return 'at_hash' in claims

    def _configure_from_discovery_doc(self):
        resp = requests.get(self.CONFIG_URI)
        config = json.loads(resp.text)
        self.auth_endpoint = config['authorization_endpoint']
        self.token_endpoint = config['token_endpoint']
        self.issuer = config['issuer']
        self.jwks_uri = config['jwks_uri']

    def _fetch_tokens(self) -> Dict:

        headers = {'content-type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': self.request.GET.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': self._get_redirect_uri(),
            'scope': 'openid',
        }

        resp = requests.post(self.token_endpoint, data=data, headers=headers)
        if not resp.ok:
            raise ValueError(f'Bad response from {self.token_endpoint}')

        resp_data = json.loads(resp.text)

        # calc expiry
        if 'access_token' in resp_data and 'expires_in' in resp_data:
            now = datetime.utcnow()
            diff = timedelta(seconds=int(resp_data['expires_in']))
            resp_data['access_expiry'] = now + diff

        return resp_data

    def _find_user(self, sub: str, emails: List[str]):
        try:
            user = self.USER_MODEL.objects.get(sub=sub)
        except self.USER_MODEL.DoesNotExist:
            pass
        else:
            return user

        email_obj = None
        for email in emails:
            try:
                email_obj = self.EMAIL_MODEL.objects.get(email=email)
            except self.EMAIL_MODEL.DoesNotExist:
                pass
            else:
                break

        if email_obj:
            return self.USER_MODEL.objects.get(id=email_obj.user_id)

    def _get_flow(self) -> 'OAuth2Flow':
        try:
            flow = OAuth2Flow.objects.get(session_id=
                                          self.request.session.session_key)
        except OAuth2Flow.DoesNotExist:
            raise ValueError('No matching session data.  Cannot check state, '
                             'so rejecting request.')

        return flow

    def _get_header_data(self, id_token) -> Dict:
        header, _ = id_token.split('.', 1)
        header_data = json.loads(self.robust_b64_url_decode(header))

        return header_data

    def _get_jwt_metadata(self) -> Dict:
        resp = requests.get(self.jwks_uri)

        return json.loads(resp.text)

    def _get_redirect_uri(self) -> str:
        return (f"{self.request.scheme}://{self.request.get_host()}"
                f"{reverse(self.CALLBACK_VIEW_NAME).rstrip('/')}")

    def _setup_new_user(self, claims: Dict) -> 'Text2phenotypeUser':

        user = self.USER_MODEL()
        user.first_name = claims.get('given_name')
        user.last_name = claims.get('family_name')
        user.sub = claims['sub']  # This must exist, don't use `get`
        user.save()

        return user

    def _update_user_groups(self, user: Text2phenotypeUser, role_groups: List):
        current_groups = set()
        for rg in role_groups:
            _, app, role = rg.split(':')

            if app in [OktaConstants.Apps.INTEGRATION_PORTAL, OktaConstants.Apps.SANDS]:
                current_groups.add((AppNameOkta2DB[app], role))

        legacy_groups = set()
        for mg in user.text2phenotype_groups.filter(
                application__in=[Applications.INTEGRATION_PORTAL.value, Applications.SANDS.value]):
            legacy_groups.add((mg.application, mg.name))

        missing_groups = current_groups - legacy_groups
        extra_groups = legacy_groups - current_groups

        for mg in missing_groups:
            try:
                group = Text2phenotypeGroup.objects.get(application=mg[0], name=mg[1])
            except Text2phenotypeGroup.DoesNotExist:
                operations_logger.warning(f'Requested group ({mg}) does not exist!')
                continue

            group.users.add(user)
            group.save()

        for eg in extra_groups:
            try:
                group = Text2phenotypeGroup.objects.get(application=eg[0], name=eg[1])
            except Text2phenotypeGroup.DoesNotExist:
                operations_logger.warning(f'Requested group ({eg}) does not exist!')
                continue

            group.users.remove(user)
            group.save()

    def _update_existing_user(self, user: 'Text2phenotypeUser', claims: Dict):

        if not user.first_name or user.first_name != claims.get('given_name'):
            user.first_name = claims.get('given_name')

        if not user.last_name or user.last_name != claims.get('family_name'):
            user.last_name = claims.get('family_name')

        if user.sub != claims['sub']:
            user.sub = claims['sub']

        user.save()

    def _update_user_emails(self, user: 'Text2phenotypeUser', emails: List):
        qset = user.emails.all()

        check_primary = True
        for email in emails:
            if not qset.filter(email__iexact=email):
                new_email = EmailAddress(user=user,
                                         email=email)
                new_email.save()

                if check_primary and not qset.filter(primary=True):
                    new_email.make_primary()
                    check_primary = False

    def _verify_id_token(self, id_token: str, access_token: str,
                         flow: 'OAuth2Flow') -> Dict:

        # check state
        if flow.state != self.request.GET.get('state'):
            raise ValueError('Mismatched state! Rejecting suspicious request.')

        meta_data = self._get_jwt_metadata()
        header_data = self._get_header_data(id_token)
        has_at_hash_claim = self._check_at_hash_claim(id_token)

        # need to check this to prevent jose from throwing an error
        # Active Directory B2C tenant doesn't include at_hash claim
        if not has_at_hash_claim:
            access_token = None

        key = None
        for potential in meta_data['keys']:
            if potential['kid'] == header_data['kid']:
                key = potential
                break

        try:
            claims = jwt.decode(id_token, key,
                                algorithms=header_data['alg'],
                                audience=self.client_id,
                                issuer=self.issuer,
                                access_token=access_token)
        except (JWTError, JWTClaimsError, ExpiredSignatureError) as err:
            operations_logger.exception('Error verifying id_token!',
                                        exc_info=True)
            raise ValueError('Error verifying id_token! Rejecting suspicious '
                             'request.')

        # check nonce
        if flow.nonce != claims['nonce']:
            raise ValueError('Mismatched nonce! Rejecting suspicious request.')

        return claims

