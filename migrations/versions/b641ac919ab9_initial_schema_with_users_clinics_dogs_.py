"""Initial schema with users, clinics, dogs, requests, and responses

Revision ID: b641ac919ab9
Revises:
Create Date: 2025-11-12 09:01:23.641977

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b641ac919ab9"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("clinic_staff", "dog_owner", "admin", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # Create clinics table
    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clinics_city"), "clinics", ["city"], unique=False)
    op.create_index(op.f("ix_clinics_owner_id"), "clinics", ["owner_id"], unique=False)

    # Create dog_profiles table
    op.create_table(
        "dog_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("breed", sa.String(length=100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("sex", sa.Enum("MALE", "FEMALE", name="dogsex"), nullable=False),
        sa.Column(
            "blood_type",
            sa.Enum(
                "DEA_1_1_POSITIVE",
                "DEA_1_1_NEGATIVE",
                "DEA_1_2_POSITIVE",
                "DEA_1_2_NEGATIVE",
                "DEA_3_POSITIVE",
                "DEA_3_NEGATIVE",
                "DEA_4_POSITIVE",
                "DEA_4_NEGATIVE",
                "DEA_5_POSITIVE",
                "DEA_5_NEGATIVE",
                "DEA_7_POSITIVE",
                "DEA_7_NEGATIVE",
                "UNKNOWN",
                name="bloodtype",
            ),
            nullable=True,
        ),
        sa.Column("last_donation_date", sa.Date(), nullable=True),
        sa.Column("medical_notes", sa.Text(), nullable=True),
        sa.Column("vaccination_status", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_dog_profiles_blood_type"), "dog_profiles", ["blood_type"], unique=False
    )
    op.create_index(op.f("ix_dog_profiles_owner_id"), "dog_profiles", ["owner_id"], unique=False)

    # Create blood_donation_requests table
    op.create_table(
        "blood_donation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "blood_type_needed",
            sa.Enum(
                "DEA_1_1_POSITIVE",
                "DEA_1_1_NEGATIVE",
                "DEA_1_2_POSITIVE",
                "DEA_1_2_NEGATIVE",
                "DEA_3_POSITIVE",
                "DEA_3_NEGATIVE",
                "DEA_4_POSITIVE",
                "DEA_4_NEGATIVE",
                "DEA_5_POSITIVE",
                "DEA_5_NEGATIVE",
                "DEA_7_POSITIVE",
                "DEA_7_NEGATIVE",
                "UNKNOWN",
                name="bloodtype",
            ),
            nullable=True,
        ),
        sa.Column("volume_ml", sa.Integer(), nullable=False),
        sa.Column(
            "urgency",
            sa.Enum("CRITICAL", "URGENT", "ROUTINE", name="requesturgency"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("OPEN", "FULFILLED", "CANCELLED", "EXPIRED", name="requeststatus"),
            nullable=False,
        ),
        sa.Column("patient_details", sa.Text(), nullable=True),
        sa.Column("needed_by_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_info", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_blood_donation_requests_blood_type_needed"),
        "blood_donation_requests",
        ["blood_type_needed"],
        unique=False,
    )
    op.create_index(
        op.f("ix_blood_donation_requests_clinic_id"),
        "blood_donation_requests",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_blood_donation_requests_status"),
        "blood_donation_requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_blood_donation_requests_urgency"),
        "blood_donation_requests",
        ["urgency"],
        unique=False,
    )

    # Create donation_responses table
    op.create_table(
        "donation_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dog_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACCEPTED", "DECLINED", "COMPLETED", name="responsestatus"),
            nullable=False,
        ),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["dog_id"], ["dog_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["request_id"], ["blood_donation_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", "dog_id", name="uq_request_dog"),
    )
    op.create_index(
        op.f("ix_donation_responses_dog_id"),
        "donation_responses",
        ["dog_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_donation_responses_owner_id"),
        "donation_responses",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_donation_responses_request_id"),
        "donation_responses",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_donation_responses_status"),
        "donation_responses",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table("donation_responses")
    op.drop_table("blood_donation_requests")
    op.drop_table("dog_profiles")
    op.drop_table("clinics")
    op.drop_table("users")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS responsestatus")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS requesturgency")
    op.execute("DROP TYPE IF EXISTS bloodtype")
    op.execute("DROP TYPE IF EXISTS dogsex")
    op.execute("DROP TYPE IF EXISTS userrole")
