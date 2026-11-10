"""
Database models of the application, divided into separate modules.
Importing this package exposes all models and helper objects.
"""
from webapp import db, login_manager

from webapp.model.feedback import (
    ObservationFeedback,
    ObservationFeedbackPosition,
)

from webapp.model.db.user import (
    load_user,
    User,
    UserPreferences,
    Group,
    Role,
    user_group,
    role_group,
    Poweruser,
)
from webapp.model.db.post import Post
from webapp.model.db.site import Site
from webapp.model.db.observatory import Observatory
from webapp.model.db.telescope import Telescope
from webapp.model.db.filterset import Filterset
from webapp.model.db.observation_request import (
    ObservationRequest,
    ObservationRequestPosition,
    ObservationRequestLog,
)
from webapp.model.db.observation_history import ObservationHistory
from webapp.model.db.system_parameters import (
    SystemParameters,
    SystemParametersHistory,
    MotivationTypes,
    ObjectTypes,
)
from webapp.model.db.catalogue import (
    CatalogueMeta,
    Catalogue,
)
from webapp.model.db.poweruser_meldung import PoweruserMeldung
from webapp.model.db.observatory_reservation import (
    ObservatoryReservation,
    Status,
)

from webapp.model.db import (
    user,
    post,
    site,
    observatory,
    telescope,
    filterset,
    observation_request,
    observation_history,
    system_parameters,
    catalogue,
    poweruser_meldung,
    observatory_reservation,
)

__all__ = [
    'db',
    'login_manager',
    'load_user',
    'User',
    'UserPreferences',
    'Group',
    'Role',
    'user_group',
    'role_group',
    'Poweruser',
    'Post',
    'Site',
    'Observatory',
    'Telescope',
    'Filterset',
    'ObservationRequest',
    'ObservationRequestPosition',
    'ObservationRequestLog',
    'ObservationHistory',
    'SystemParameters',
    'SystemParametersHistory',
    'MotivationTypes',
    'ObjectTypes',
    'CatalogueMeta',
    'Catalogue',
    'PoweruserMeldung',
    'ObservatoryReservation',
    'Status',
    'ObservationFeedback',
    'ObservationFeedbackPosition',
    'user',
    'post',
    'site',
    'observatory',
    'telescope',
    'filterset',
    'observation_request',
    'observation_history',
    'system_parameters',
    'catalogue',
    'poweruser_meldung',
    'observatory_reservation',
]
