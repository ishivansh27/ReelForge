"""
Central place that defines the SQLAlchemy declarative Base, and imports
every model so Alembic can "see" them when generating migrations.

If you add a new model file under app/models/, import it here too --
otherwise Alembic will silently ignore it.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Base.metadata knows about every table.
# These are plain module imports (not `from x import Y`) on purpose: a
# `from` import would try to bind the class name immediately, which
# breaks if some other module imports e.g. `app.models.user` directly
# before `app.db.base` -- that re-enters this file mid-import and the
# class name doesn't exist on the partially-initialized module yet.
import app.models.user  # noqa: E402,F401
import app.models.project  # noqa: E402,F401
import app.models.blueprint  # noqa: E402,F401
import app.models.asset_slot  # noqa: E402,F401
import app.models.user_asset  # noqa: E402,F401
import app.models.render_job  # noqa: E402,F401
import app.models.refresh_token  # noqa: E402,F401
