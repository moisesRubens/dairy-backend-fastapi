from exceptions.common_exceptions import AdminPermissionRequired
from database.model import SalePoints


def require_admin(session, user, message):
    actor = session.get(SalePoints, int(user['sub']))
    if actor is None or actor.level != 1:
        raise AdminPermissionRequired(message)
    return actor
