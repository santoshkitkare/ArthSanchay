"""Import every model here so SQLAlchemy's mapper configuration can resolve the string-based
relationship() type hints across files (User <-> Scenario <-> ScenarioInputs/Dependent/Goal/
IncomeStream <-> RefreshToken/PasswordResetToken). Import this module (not the submodules
directly) before calling Base.metadata.create_all() or running Alembic autogenerate.
"""
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.scenario import Scenario, ScenarioInputs
from app.models.dependent import Dependent
from app.models.goal import Goal
from app.models.income_stream import IncomeStream

__all__ = [
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "Scenario",
    "ScenarioInputs",
    "Dependent",
    "Goal",
    "IncomeStream",
]
