import enum
import uuid
from datetime import datetime
from typing import Dict, Generic, List, Optional, TypeVar, Union

import pydantic
import pydantic.dataclasses
import pydantic.generics
from packaging import version

# from ..structures.core import StructureFamily

DataT = TypeVar("DataT")
LinksT = TypeVar("LinksT")
MetaT = TypeVar("MetaT")

if version.parse(pydantic.__version__) < version.parse("2.0.0"):
    generic_model = pydantic.generics.GenericModel
    orm = dict(orm_mode=True)
else:
    generic_model = pydantic.BaseModel
    orm = dict(from_attributes=True)


class Error(pydantic.BaseModel):
    code: int
    message: str


class Response(generic_model, Generic[DataT, LinksT, MetaT]):
    data: Optional[DataT] = None
    error: Optional[Error] = None
    links: Optional[LinksT] = None
    meta: Optional[MetaT] = None

    @pydantic.validator("error", always=True)
    def check_consistency(cls, v, values):
        if v is not None and values["data"] is not None:
            raise ValueError("must not provide both data and error")
        if v is None and values.get("data") is None:
            raise ValueError("must provide data or error")
        return v


class PaginationLinks(pydantic.BaseModel):
    self: str
    next: str
    prev: str
    first: str
    last: str


class EntryFields(str, enum.Enum):
    metadata = "metadata"
    structure_family = "structure_family"
    microstructure = "structure.micro"
    macrostructure = "structure.macro"
    count = "count"
    sorting = "sorting"
    specs = "specs"
    none = ""


class Structure(pydantic.BaseModel):
    micro: Optional[dict] = None
    macro: Optional[dict] = None


class SortingDirection(int, enum.Enum):
    ASCENDING = 1
    DECENDING = -1


class SortingItem(pydantic.BaseModel):
    key: str
    direction: SortingDirection


# class NodeAttributes(pydantic.BaseModel):
#     ancestors: List[str]
#     structure_family: Optional[StructureFamily]
#     specs: Optional[List[str]]
#     metadata: Optional[dict]  # free-form, user-specified dict
#     structure: Optional[Structure]
#     count: Optional[int]
#     sorting: Optional[List[SortingItem]]


AttributesT = TypeVar("AttributesT")
ResourceMetaT = TypeVar("ResourceMetaT")
ResourceLinksT = TypeVar("ResourceLinksT")


class SelfLinkOnly(pydantic.BaseModel):
    self: str


class NodeLinks(pydantic.BaseModel):
    self: str
    search: str
    full: str


class ArrayLinks(pydantic.BaseModel):
    self: str
    full: str
    block: str


class DataFrameLinks(pydantic.BaseModel):
    self: str
    full: str
    partition: str


class XarrayDataArrayLinks(pydantic.BaseModel):
    self: str
    full_variable: str


class XarrayDatasetLinks(pydantic.BaseModel):
    self: str
    full_variable: str
    full_coord: str
    full_dataset: str


resource_links_type_by_structure_family = {
    "node": NodeLinks,
    "array": ArrayLinks,
    "dataframe": DataFrameLinks,
    "xarray_data_array": XarrayDataArrayLinks,
    "xarray_dataset": XarrayDatasetLinks,
}


class EmptyDict(pydantic.BaseModel):
    pass


class NodeMeta(pydantic.BaseModel):
    count: int


class Resource(generic_model, Generic[AttributesT, ResourceLinksT, ResourceMetaT]):
    "A JSON API Resource"

    id: Union[str, uuid.UUID]
    attributes: AttributesT
    links: Optional[ResourceLinksT] = None
    meta: Optional[ResourceMetaT] = None


class AccessAndRefreshTokens(pydantic.BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    token_type: str


class RefreshToken(pydantic.BaseModel):
    refresh_token: str


class AuthenticationMode(str, enum.Enum):
    password = "password"
    external = "external"


class AboutAuthenticationProvider(pydantic.BaseModel):
    provider: str
    mode: AuthenticationMode
    links: Dict[str, str]
    confirmation_message: Optional[str] = None


class AboutAuthenticationLinks(pydantic.BaseModel):
    whoami: str
    apikey: str
    refresh_session: str
    revoke_session: str
    logout: str


class AboutAuthentication(pydantic.BaseModel):
    required: bool
    providers: List[AboutAuthenticationProvider]
    links: Optional[AboutAuthenticationLinks] = None


class About(pydantic.BaseModel):
    api_version: int
    library_version: str
    formats: Dict[str, List[str]]
    aliases: Dict[str, Dict[str, List[str]]]
    queries: List[str]
    authentication: AboutAuthentication
    links: Dict[str, str]
    meta: dict


class PrincipalType(str, enum.Enum):
    user = "user"
    service = "service"  # TODO Add support for services.


class Identity(pydantic.BaseModel, **orm):
    id: pydantic.constr(max_length=255)
    provider: pydantic.constr(max_length=255)
    latest_login: Optional[datetime] = None


class Role(pydantic.BaseModel, **orm):
    name: str
    scopes: List[str]
    # principals


class APIKey(pydantic.BaseModel, **orm):
    first_eight: pydantic.constr(min_length=8, max_length=8)
    expiration_time: Optional[datetime] = None
    note: Optional[pydantic.constr(max_length=255)] = None
    scopes: List[str]
    latest_activity: Optional[datetime] = None


class APIKeyWithSecret(APIKey):
    secret: str  # hex-encoded bytes

    @classmethod
    def from_orm(cls, orm, secret):
        return cls(
            first_eight=orm.first_eight,
            expiration_time=orm.expiration_time,
            note=orm.note,
            scopes=orm.scopes,
            latest_activity=orm.latest_activity,
            secret=secret,
        )


class Session(pydantic.BaseModel, **orm):
    """
    This related to refresh tokens, which have a session uuid ("sid") claim.

    When the client attempts to use a refresh token, we first check
    here to ensure that the "session", which is associated with a chain
    of refresh tokens that came from a single authentication, are still valid.
    """

    # The id field (primary key) is intentionally not exposed to the application.
    # It is left as an internal database concern.
    uuid: uuid.UUID
    expiration_time: datetime
    revoked: bool


class Principal(pydantic.BaseModel, **orm):
    "Represents a User or Service"

    # The id field (primary key) is intentionally not exposed to the application.
    # It is left as an internal database concern.
    uuid: uuid.UUID
    type: PrincipalType
    identities: List[Identity] = []
    # roles: List[Role] = []
    api_keys: List[APIKey] = []
    sessions: List[Session] = []
    latest_activity: Optional[datetime] = None
    # Optional parameters reflecting current permissions for the authenticated user
    roles: Optional[List[str]] = []
    scopes: Optional[List[str]] = []
    api_key_scopes: Optional[Union[List[str], None]] = None

    @classmethod
    def from_orm(cls, orm, latest_activity=None):
        instance = super().from_orm(orm)
        instance.latest_activity = latest_activity
        return instance


class AllowedScopes(pydantic.BaseModel, **orm):
    "Returns roles and current allowed scopes for a user authenticated with API key or token"

    roles: List[str] = []
    scopes: List[str] = []


class APIKeyRequestParams(pydantic.BaseModel):
    # Provide an example for expires_in. Otherwise, OpenAPI suggests lifetime=0.
    # If the user is not reading carefully, they will be frustrated when they
    # try to use the instantly-expiring API key!
    expires_in: Optional[int] = pydantic.Field(..., example=600)  # seconds
    # scopes: Optional[List[str]] = pydantic.Field(..., example=["inherit"])
    scopes: Optional[List[str]] = pydantic.Field(default=["inherit"], example=["inherit"])
    note: Optional[str] = None
