"""
Lead service.

Business logic for:

- Creating leads
- Updating leads
- Duplicate detection
- Organization isolation
- Lead status management
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lead import Lead

from app.repositories.lead_repository import (
    LeadRepository,
)

from app.schemas.lead import LeadCreate


ALLOWED_STATUSES = {
    "new",
    "contacted",
    "qualified",
    "converted",
    "lost",
}


class LeadService:
    """
    Business logic for lead management.

    Lead uniqueness is organization-scoped.

    A company can never access or update another company's
    leads through this service.
    """

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

        self.repository = (
            LeadRepository(db)
        )

    # =========================================================
    # CREATE OR UPDATE
    # =========================================================

    def create_or_update_lead(
        self,
        lead_data: LeadCreate,
        organization_id: int,
        conversation_id: int | None = None,
    ) -> Lead:
        """
        Create a new lead or update an existing lead.

        Matching priority:

        1. Same conversation
        2. Same phone within organization
        3. Same email within organization

        This prevents duplicate leads in common situations.
        """

        # -----------------------------------------------------
        # Normalize incoming data.
        # -----------------------------------------------------

        self._normalize_lead_data(
            lead_data
        )

        existing_lead = None

        # =====================================================
        # 1. SAME CONVERSATION
        # =====================================================

        if conversation_id is not None:

            existing_lead = (
                self.repository
                .get_by_conversation_in_organization(
                    conversation_id,
                    organization_id,
                )
            )

        # =====================================================
        # 2. SAME PHONE
        # =====================================================

        if (
            existing_lead is None
            and lead_data.phone
        ):

            normalized_phone = (
                self._normalize_phone(
                    lead_data.phone
                )
            )

            if normalized_phone:

                existing_lead = (
                    self.repository
                    .get_by_phone_in_organization(
                        normalized_phone,
                        organization_id,
                    )
                )

        # =====================================================
        # 3. SAME EMAIL
        # =====================================================

        if (
            existing_lead is None
            and lead_data.email
        ):

            normalized_email = (
                self._normalize_email(
                    lead_data.email
                )
            )

            if normalized_email:

                existing_lead = (
                    self.repository
                    .get_by_email_in_organization(
                        normalized_email,
                        organization_id,
                    )
                )

        # =====================================================
        # UPDATE EXISTING
        # =====================================================

        if existing_lead is not None:

            self._update_fields(
                existing_lead,
                lead_data,
            )

            # -------------------------------------------------
            # Associate current conversation when possible.
            # -------------------------------------------------

            if conversation_id is not None:

                existing_lead.conversation_id = (
                    conversation_id
                )

            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                existing_lead = self._find_existing_lead(
                    lead_data, organization_id, conversation_id
                )
                if existing_lead is None:
                    raise
                self._update_fields(existing_lead, lead_data)
                if conversation_id is not None:
                    existing_lead.conversation_id = conversation_id
                self.db.commit()
                self.db.refresh(existing_lead)
                return existing_lead

            self.db.refresh(
                existing_lead
            )

            return existing_lead

        # =====================================================
        # CREATE NEW
        # =====================================================

        lead = Lead(
            organization_id=organization_id,
            conversation_id=conversation_id,
            name=lead_data.name,
            phone=lead_data.phone,
            email=lead_data.email,
            interest=lead_data.interest,
            preferred_mode=(
                lead_data.preferred_mode
            ),
            preferred_time=(
                lead_data.preferred_time
            ),
            notes=lead_data.notes,
            status="new",
        )

        self.repository.add(
            lead
        )

        try:
            self.db.commit()
        except IntegrityError:
            # A concurrent request can win the lookup/insert race.  Re-read
            # the organization-scoped key and merge into that lead.
            self.db.rollback()
            existing_lead = self._find_existing_lead(
                lead_data, organization_id, conversation_id
            )
            if existing_lead is None:
                raise
            self._update_fields(existing_lead, lead_data)
            if conversation_id is not None:
                existing_lead.conversation_id = conversation_id
            self.db.commit()
            self.db.refresh(existing_lead)
            return existing_lead

        self.db.refresh(
            lead
        )

        return lead

    def save_context(
        self,
        context,
        organization_id: int,
        conversation_id: int,
    ) -> Lead | None:
        """
        Persist the stable lead context for one conversation.

        This is the single bridge between conversational state and
        the lead database. It is intentionally duck-typed so the
        service remains independent of LeadContextService's module.

        The operation is idempotent for a conversation: repeated
        messages update the same lead row instead of creating a new
        row for every field collected.
        """

        if context is None:

            return None

        if not getattr(context, "is_lead", False):

            return None

        values = {
            field: getattr(context, field, None)
            for field in (
                "name",
                "phone",
                "email",
                "interest",
                "preferred_mode",
                "preferred_time",
                "notes",
            )
        }

        if not any(values.values()):

            return None

        return self.create_or_update_lead(
            lead_data=LeadCreate(**values),
            organization_id=organization_id,
            conversation_id=conversation_id,
        )

    # =========================================================
    # UPDATE FIELDS
    # =========================================================

    def _find_existing_lead(
        self,
        lead_data: LeadCreate,
        organization_id: int,
        conversation_id: int | None,
    ) -> Lead | None:
        """Find a matching lead using the same deterministic key order."""
        if conversation_id is not None:
            lead = self.repository.get_by_conversation_in_organization(
                conversation_id, organization_id
            )
            if lead is not None:
                return lead
        if lead_data.phone:
            phone = self._normalize_phone(lead_data.phone)
            if phone:
                lead = self.repository.get_by_phone_in_organization(
                    phone, organization_id
                )
                if lead is not None:
                    return lead
        if lead_data.email:
            email = self._normalize_email(lead_data.email)
            if email:
                return self.repository.get_by_email_in_organization(
                    email, organization_id
                )
        return None

    @staticmethod
    def _update_fields(
        lead: Lead,
        lead_data: LeadCreate,
    ) -> None:
        """
        Update only fields that contain useful new information.

        Existing information is never replaced by None.
        """

        if lead_data.name:

            lead.name = (
                lead_data.name
            )

        if lead_data.phone:

            lead.phone = (
                lead_data.phone
            )

        if lead_data.email:

            lead.email = (
                lead_data.email
            )

        if lead_data.interest:

            lead.interest = (
                lead_data.interest
            )

        if lead_data.preferred_mode:

            lead.preferred_mode = (
                lead_data.preferred_mode
            )

        if lead_data.preferred_time:

            lead.preferred_time = (
                lead_data.preferred_time
            )

        if lead_data.notes:

            if lead.notes:

                lead.notes = (
                    f"{lead.notes}\n"
                    f"{lead_data.notes}"
                )

            else:

                lead.notes = (
                    lead_data.notes
                )

    # =========================================================
    # NORMALIZE LEAD DATA
    # =========================================================

    @classmethod
    def _normalize_lead_data(
        cls,
        lead_data: LeadCreate,
    ) -> None:
        """
        Normalize values before database operations.
        """

        if lead_data.phone:

            lead_data.phone = (
                cls._normalize_phone(
                    lead_data.phone
                )
            )

        if lead_data.email:

            lead_data.email = (
                cls._normalize_email(
                    lead_data.email
                )
            )

        if lead_data.name:

            lead_data.name = (
                lead_data.name
                .strip()
            )

        if lead_data.interest:

            lead_data.interest = (
                lead_data.interest
                .strip()
            )

        if lead_data.preferred_mode:

            lead_data.preferred_mode = (
                lead_data.preferred_mode
                .strip()
            )

        if lead_data.preferred_time:

            lead_data.preferred_time = (
                lead_data.preferred_time
                .strip()
            )

        if lead_data.notes:

            lead_data.notes = (
                lead_data.notes
                .strip()
            )

    # =========================================================
    # PHONE NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_phone(
        phone: str | None,
    ) -> str | None:
        """
        Normalize phone numbers for duplicate detection.

        Example:

            +91 98765 43210
            +919876543210
            9876543210

        The stored value remains a normalized string.

        This does not attempt country-specific validation.
        """

        if not phone:

            return None

        phone = str(
            phone
        ).strip()

        if not phone:

            return None

        digits = "".join(
            character
            for character in phone
            if character.isdigit()
        )

        if not digits or not 7 <= len(digits) <= 15:
            return None

        # Treat common national representations of an Indian number as the
        # same identity (9876543210, +91 9876543210, 919876543210).
        if len(digits) == 12 and digits.startswith("91"):
            return digits[2:]
        if len(digits) == 11 and digits.startswith("0"):
            return digits[1:]

        return digits

    # =========================================================
    # EMAIL NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_email(
        email: str | None,
    ) -> str | None:
        """
        Normalize email for duplicate detection.
        """

        if not email:

            return None

        email = (
            str(
                email
            )
            .strip()
            .lower()
        )

        if not email:

            return None

        return email

    # =========================================================
    # GET LEAD
    # =========================================================

    def get_lead(
        self,
        lead_id: int,
        organization_id: int,
    ) -> Lead | None:

        return (
            self.repository
            .get_by_id_in_organization(
                lead_id,
                organization_id,
            )
        )

    def get_lead_for_conversation(
        self,
        conversation_id: int,
        organization_id: int,
    ) -> Lead | None:
        """
        Return the lead associated with one conversation.

        This preserves lead state after older messages have fallen
        outside the in-memory conversation-history window.
        """

        return (
            self.repository
            .get_by_conversation_in_organization(
                conversation_id,
                organization_id,
            )
        )

    # =========================================================
    # GET ALL LEADS
    # =========================================================

    def get_all_leads(
        self,
        organization_id: int,
    ) -> list[Lead]:

        return (
            self.repository
            .get_all_in_organization(
                organization_id
            )
        )

    # =========================================================
    # GET BY STATUS
    # =========================================================

    def get_leads_by_status(
        self,
        organization_id: int,
        status: str,
    ) -> list[Lead]:

        self._validate_status(
            status
        )

        return (
            self.repository
            .get_by_status(
                organization_id,
                status,
            )
        )

    # =========================================================
    # UPDATE LEAD
    # =========================================================

    def update_lead(
        self,
        lead_id: int,
        organization_id: int,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        interest: str | None = None,
        preferred_mode: str | None = None,
        preferred_time: str | None = None,
        notes: str | None = None,
        status: str | None = None,
    ) -> Lead | None:

        lead = (
            self.repository
            .get_by_id_in_organization(
                lead_id,
                organization_id,
            )
        )

        if lead is None:

            return None

        if name is not None:

            lead.name = (
                name.strip()
            )

        if phone is not None:

            lead.phone = (
                self._normalize_phone(
                    phone
                )
            )

        if email is not None:

            lead.email = (
                self._normalize_email(
                    email
                )
            )

        if interest is not None:

            lead.interest = (
                interest.strip()
            )

        if preferred_mode is not None:

            lead.preferred_mode = (
                preferred_mode.strip()
            )

        if preferred_time is not None:

            lead.preferred_time = (
                preferred_time.strip()
            )

        if notes is not None:

            lead.notes = (
                notes.strip()
            )

        if status is not None:

            self._validate_status(
                status
            )

            lead.status = status

        self.db.commit()

        self.db.refresh(
            lead
        )

        return lead

    def delete_lead(
        self,
        lead_id: int,
        organization_id: int,
    ) -> bool:
        """Delete a lead only when it belongs to the organization."""

        lead = self.repository.get_by_id_in_organization(
            lead_id,
            organization_id,
        )

        if lead is None:
            return False

        self.db.delete(lead)
        self.db.commit()
        return True

    # =========================================================
    # UPDATE STATUS
    # =========================================================

    def update_status(
        self,
        lead_id: int,
        organization_id: int,
        status: str,
    ) -> Lead | None:

        self._validate_status(
            status
        )

        lead = (
            self.repository
            .get_by_id_in_organization(
                lead_id,
                organization_id,
            )
        )

        if lead is None:

            return None

        lead.status = status

        self.db.commit()

        self.db.refresh(
            lead
        )

        return lead

    # =========================================================
    # STATUS VALIDATION
    # =========================================================

    @staticmethod
    def _validate_status(
        status: str,
    ) -> None:

        if status not in ALLOWED_STATUSES:

            raise ValueError(
                f"Invalid lead status: {status}. "
                f"Allowed statuses: "
                f"{', '.join(sorted(ALLOWED_STATUSES))}"
            )
