"""initial schema

Revision ID: 19f8fe5f585c
Revises:
Create Date: 2026-07-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "19f8fe5f585c"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("industries", sa.JSON(), nullable=False),
        sa.Column("company_size_min", sa.Integer(), nullable=True),
        sa.Column("company_size_max", sa.Integer(), nullable=True),
        sa.Column("revenue_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("revenue_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("geography", sa.JSON(), nullable=False),
        sa.Column("target_roles", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("max_leads_per_cycle", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("email_tone_of_voice", sa.Text(), nullable=True),
        sa.Column("followup_offer_text", sa.Text(), nullable=True),
        sa.Column("followup_delay_business_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("close_after_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    lead_status = sa.Enum(
        "nuovo", "inviata", "risposto", "follow_up_inviato", "chiuso_senza_risposta", "opt_out",
        name="lead_status",
    )
    lead_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("contact_first_name", sa.String(255), nullable=True),
        sa.Column("contact_last_name", sa.String(255), nullable=True),
        sa.Column("role_title", sa.String(255), nullable=True),
        sa.Column("email", sa.String(320), nullable=True, unique=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("linkedin_company_url", sa.String(500), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("company_size", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("status", lead_status, nullable=False, server_default="nuovo"),
        sa.Column("legal_basis", sa.Text(), nullable=False),
        sa.Column("first_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_change_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leads_email", "leads", ["email"])
    op.create_index("ix_leads_status", "leads", ["status"])
    op.create_index(
        "ix_leads_company_contact", "leads", ["company_name", "contact_first_name", "contact_last_name"]
    )

    message_type = sa.Enum("first", "followup", name="message_type")
    message_status = sa.Enum("draft", "sent", "failed", name="message_status")
    message_type.create(op.get_bind(), checkfirst=True)
    message_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_type", message_type, nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", message_status, nullable=False, server_default="draft"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("graph_message_id", sa.String(500), nullable=True),
        sa.Column("graph_conversation_id", sa.String(500), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_email_messages_graph_message_id", "email_messages", ["graph_message_id"])
    op.create_index("ix_email_messages_graph_conversation_id", "email_messages", ["graph_conversation_id"])

    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "email_message_id",
            sa.Integer(),
            sa.ForeignKey("email_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("graph_message_id", sa.String(500), nullable=False),
        sa.Column("graph_conversation_id", sa.String(500), nullable=True),
        sa.Column("from_address", sa.String(320), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_replies_graph_message_id", "replies", ["graph_message_id"])
    op.create_index("ix_replies_graph_conversation_id", "replies", ["graph_conversation_id"])

    job_type = sa.Enum(
        "weekly_sourcing_and_send", "daily_reply_check", "daily_followup", "manual", name="job_type"
    )
    execution_status = sa.Enum("running", "success", "failed", "partial", name="execution_status")
    job_type.create(op.get_bind(), checkfirst=True)
    execution_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", execution_status, nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "suppressions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_suppressions_email", "suppressions", ["email"])

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("max_emails_per_day", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("weekly_job_day_of_week", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weekly_job_hour", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("daily_job_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Europe/Rome"),
        sa.Column("default_followup_delay_business_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("default_close_after_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.execute(
        "INSERT INTO system_settings (id, max_emails_per_day, weekly_job_day_of_week, weekly_job_hour, "
        "daily_job_hour, timezone, default_followup_delay_business_days, default_close_after_days) "
        "VALUES (1, 30, 0, 8, 9, 'Europe/Rome', 3, 7)"
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("suppressions")
    op.drop_table("users")
    op.drop_table("execution_logs")
    sa.Enum(name="execution_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="job_type").drop(op.get_bind(), checkfirst=True)
    op.drop_table("replies")
    op.drop_table("email_messages")
    sa.Enum(name="message_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="message_type").drop(op.get_bind(), checkfirst=True)
    op.drop_table("leads")
    sa.Enum(name="lead_status").drop(op.get_bind(), checkfirst=True)
    op.drop_table("campaigns")
