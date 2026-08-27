"""Single-user mode: the local admin account and the switch back to sign-in."""

import pytest
from fastapi_users.password import PasswordHelper
from sqlalchemy.orm import Session

from onyx.auth.users import single_user_mode_enabled
from onyx.configs.app_configs import SINGLE_USER_EMAIL
from onyx.db.enums import Permission
from onyx.db.users import (
    get_or_create_single_user_account,
    get_user_by_email,
    set_single_user_credentials,
)
from onyx.error_handling.exceptions import OnyxError
from onyx.server.settings.store import load_settings, store_settings
from tests.external_dependency_unit.conftest import create_test_user, delete_test_user

pytestmark = pytest.mark.usefixtures("tenant_context")


@pytest.fixture
def single_user_account(db_session: Session):  # type: ignore[no-untyped-def]
    """The local account, removed again after the test."""
    account = get_or_create_single_user_account(db_session)
    yield account
    delete_test_user(db_session, account)
    db_session.commit()


@pytest.fixture
def restore_single_user_setting():  # type: ignore[no-untyped-def]
    """Put the stored flag back the way the test found it."""
    original = load_settings().single_user_mode_enabled
    yield
    settings = load_settings()
    settings.single_user_mode_enabled = original
    store_settings(settings)


def test_local_account_is_created_as_admin(single_user_account) -> None:  # type: ignore[no-untyped-def]
    """The account has to be an admin — it is the only account there is."""
    assert single_user_account.email == SINGLE_USER_EMAIL
    assert (
        Permission.FULL_ADMIN_PANEL_ACCESS.value
        in single_user_account.effective_permissions
    )
    assert single_user_account.is_verified is True


def test_creation_is_idempotent(db_session: Session, single_user_account) -> None:  # type: ignore[no-untyped-def]
    """A restart must reuse the account rather than make a second one."""
    again = get_or_create_single_user_account(db_session)
    assert again.id == single_user_account.id


def test_credentials_land_on_the_existing_account(
    db_session: Session, single_user_account
) -> None:  # type: ignore[no-untyped-def]
    """Turning sign-in on must not strand the chat history on an orphan row."""
    original_id = single_user_account.id
    original_hash = single_user_account.hashed_password

    updated = set_single_user_credentials(
        db_session=db_session,
        email="owner@example.com",
        hashed_password=PasswordHelper().hash("SomePassword123!"),
    )

    assert updated.id == original_id
    assert updated.email == "owner@example.com"
    assert updated.hashed_password != original_hash
    assert get_user_by_email(SINGLE_USER_EMAIL, db_session) is None


@pytest.mark.usefixtures("single_user_account")
def test_email_already_taken_is_rejected(db_session: Session) -> None:
    """Claiming another account's email would merge two identities."""
    other = create_test_user(db_session, "single_user_conflict")
    try:
        with pytest.raises(OnyxError):
            set_single_user_credentials(
                db_session=db_session,
                email=other.email,
                hashed_password=PasswordHelper().hash("SomePassword123!"),
            )
    finally:
        delete_test_user(db_session, other)
        db_session.commit()


@pytest.mark.usefixtures("restore_single_user_setting")
def test_stored_setting_beats_the_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """An operator who turned sign-in on must not have it reverted by a restart."""
    monkeypatch.setattr("onyx.server.settings.store.SINGLE_USER_MODE", True)

    settings = load_settings()
    settings.single_user_mode_enabled = False
    store_settings(settings)

    assert load_settings().single_user_mode_enabled is False
    assert single_user_mode_enabled() is False


@pytest.mark.usefixtures("restore_single_user_setting")
def test_env_var_seeds_an_undecided_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh install takes its default from the compose overlay."""
    monkeypatch.setattr("onyx.server.settings.store.SINGLE_USER_MODE", True)

    settings = load_settings()
    settings.single_user_mode_enabled = None
    store_settings(settings)

    assert load_settings().single_user_mode_enabled is True
