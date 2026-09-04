"""
LLM-based lead extraction.

This service is responsible only for extracting structured
lead information from conversation history.

It does NOT generate customer-facing responses.
"""

import json

from app.llm.llm_factory import get_llm

from app.prompts.receptionist import (
    LEAD_EXTRACTION_PROMPT,
)

from app.schemas.lead import LeadCreate
from app.services.lead_context_service import LeadContextService


class LeadExtractor:
    """
    Extract structured lead information from conversation.

    The extraction model is completely separate from the
    normal customer-facing response generation.
    """

    def __init__(self):
        try:
            self.llm = get_llm()
        except Exception as exc:
            # Extraction is an enhancement; deterministic conversation
            # parsing must still work when no provider is configured.
            print("Lead extraction LLM initialization error:", exc)
            self.llm = None

    # =========================================================
    # EXTRACT
    # =========================================================

    async def extract(
        self,
        conversation_text: str,
    ) -> tuple[bool, LeadCreate]:
        """
        Extract lead information.

        Returns:

            (
                is_lead,
                LeadCreate(...)
            )

        Important:

        The customer never sees the extraction JSON.
        """

        conversation_text = (
            conversation_text or ""
        ).strip()

        if not conversation_text:

            return (
                False,
                LeadCreate(),
            )

        if self.llm is None:
            return self._fallback_extract(conversation_text)

        # -----------------------------------------------------
        # Build extraction prompt.
        # -----------------------------------------------------

        prompt = f"""
{LEAD_EXTRACTION_PROMPT}

============================================================
TASK
============================================================

Analyze the conversation below.

Extract ONLY information that the customer actually provided.

Do not guess.

Do not invent missing information.

Do not infer a phone number, email, name, course, mode,
or preferred time unless supported by the conversation.

============================================================
LEAD RULE
============================================================

A conversation can be considered a lead when the customer
shows genuine business interest or provides useful contact
information.

Examples:

- "I want to join Python."
- "I'm interested in your course."
- "Please contact me."
- "My name is Rahul and my number is 9876543210."
- "I want admission for Python."
- "Can someone call me?"

A simple information question does NOT automatically mean
the customer is a lead.

Example:

Customer:
"What is the Python fee?"

This alone should generally NOT create a lead.

============================================================
FIELDS
============================================================

Return these fields:

is_lead
name
phone
email
interest
preferred_mode
preferred_time
notes

Rules:

- Use null when information is not available.
- Keep the customer's actual information.
- Do not invent values.
- interest should describe the actual product, course,
  service, or subject the customer is interested in.
- notes can contain useful customer-specific information.
- Do not put general company knowledge into notes.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON:

{{
    "is_lead": false,
    "name": null,
    "phone": null,
    "email": null,
    "interest": null,
    "preferred_mode": null,
    "preferred_time": null,
    "notes": null
}}

============================================================
CONVERSATION
============================================================

{conversation_text}

============================================================
JSON
============================================================
""".strip()

        # -----------------------------------------------------
        # Structured LLM generation.
        # -----------------------------------------------------

        try:

            response = (
                await self.llm
                .generate_structured(
                    prompt
                )
            )

        except Exception as exc:

            print(
                "Lead extraction LLM error:",
                exc,
            )

            return self._fallback_extract(conversation_text)

        # -----------------------------------------------------
        # Clean response.
        # -----------------------------------------------------

        cleaned = (
            self._extract_json(
                response
            )
        )

        if not cleaned:
            return self._fallback_extract(conversation_text)

        # -----------------------------------------------------
        # Parse JSON.
        # -----------------------------------------------------

        try:

            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError as exc:

            print(
                "Lead extraction JSON error:",
                exc,
            )

            return self._fallback_extract(conversation_text)

        if not isinstance(
            data,
            dict,
        ):
            return self._fallback_extract(conversation_text)

        # -----------------------------------------------------
        # Lead flag.
        # -----------------------------------------------------

        is_lead = (
            self._to_bool(
                data.get(
                    "is_lead"
                )
            )
        )

        # -----------------------------------------------------
        # Extract fields.
        # -----------------------------------------------------

        name = self._clean_value(
            data.get(
                "name"
            )
        )

        phone = self._clean_value(
            data.get(
                "phone"
            )
        )

        email = self._clean_value(
            data.get(
                "email"
            )
        )

        interest = self._clean_value(
            data.get(
                "interest"
            )
        )

        preferred_mode = (
            self._clean_value(
                data.get(
                    "preferred_mode"
                )
            )
        )

        preferred_time = (
            self._clean_value(
                data.get(
                    "preferred_time"
                )
            )
        )

        notes = self._clean_value(
            data.get(
                "notes"
            )
        )

        # Validate each field independently.  One hallucinated value (for
        # example an invalid phone) must not discard the valid fields from
        # the same model response.
        values = {
            "name": name,
            "phone": phone,
            "email": email,
            "interest": interest,
            "preferred_mode": preferred_mode,
            "preferred_time": preferred_time,
            "notes": notes,
        }
        for field, value in values.items():
            if value is None:
                continue
            try:
                LeadCreate(**{field: value})
            except Exception:
                values[field] = None

        name = values["name"]
        phone = values["phone"]
        email = values["email"]
        interest = values["interest"]
        preferred_mode = values["preferred_mode"]
        preferred_time = values["preferred_time"]
        notes = values["notes"]

        # If the model forgot is_lead but extracted useful customer
        # information, treat it as a lead.
        has_useful_information = any(values.values())

        # The model cannot manufacture a lead by toggling a boolean.  A lead
        # requires either customer-provided data or a genuine intent signal.
        if not has_useful_information:
            return (
                False,
                LeadCreate(),
            )

        if (
            not is_lead
            and has_useful_information
        ):

            # Useful customer information exists.
            is_lead = True

        # -----------------------------------------------------
        # Create validated Pydantic schema.
        # -----------------------------------------------------

        try:

            lead = LeadCreate(
                name=name,
                phone=phone,
                email=email,
                interest=interest,
                preferred_mode=preferred_mode,
                preferred_time=preferred_time,
                notes=notes,
            )

        except Exception as exc:

            print(
                "Lead schema validation error:",
                exc,
            )

            return (
                False,
                LeadCreate(),
            )

        return (
            is_lead,
            lead,
        )

    # =========================================================
    # JSON EXTRACTION
    # =========================================================

    @staticmethod
    def _fallback_extract(conversation_text: str) -> tuple[bool, LeadCreate]:
        """Use the deterministic parser when the optional LLM fails."""
        context = LeadContextService().build_context(
            [{"role": "user", "content": conversation_text}]
        )
        return context.is_lead, LeadCreate(
            name=context.name,
            phone=context.phone,
            email=context.email,
            interest=context.interest,
            preferred_mode=context.preferred_mode,
            preferred_time=context.preferred_time,
            notes=context.notes,
        )

    @staticmethod
    def _extract_json(
        response: str,
    ) -> str:
        """
        Extract a JSON object from the model output.
        """

        response = (
            response or ""
        ).strip()

        if not response:

            return ""

        # -----------------------------------------------------
        # Remove markdown fences.
        # -----------------------------------------------------

        response = (
            response
            .replace(
                "```json",
                "",
            )
            .replace(
                "```",
                "",
            )
            .strip()
        )

        # -----------------------------------------------------
        # Direct JSON.
        # -----------------------------------------------------

        if (
            response.startswith("{")
            and response.endswith("}")
        ):

            return response

        # -----------------------------------------------------
        # Search for JSON object.
        # -----------------------------------------------------

        start = response.find(
            "{"
        )

        end = response.rfind(
            "}"
        )

        if (
            start == -1
            or end == -1
            or end <= start
        ):

            return ""

        candidate = (
            response[
                start : end + 1
            ]
        )

        try:

            json.loads(
                candidate
            )

        except json.JSONDecodeError:

            return ""

        return candidate

    # =========================================================
    # CLEAN VALUE
    # =========================================================

    @staticmethod
    def _clean_value(
        value,
    ) -> str | None:
        """
        Convert extracted values into clean strings.
        """

        if value is None:

            return None

        if isinstance(
            value,
            list,
        ):

            value = ", ".join(
                str(
                    item
                )
                for item in value
            )

        elif not isinstance(
            value,
            str,
        ):

            value = str(
                value
            )

        value = (
            value
            .strip()
        )

        if not value:

            return None

        # -----------------------------------------------------
        # Don't store common null-like model outputs.
        # -----------------------------------------------------

        if value.lower() in {
            "null",
            "none",
            "n/a",
            "na",
            "unknown",
            "not provided",
            "not available",
        }:

            return None

        return value

    # =========================================================
    # BOOLEAN
    # =========================================================

    @staticmethod
    def _to_bool(
        value,
    ) -> bool:

        if isinstance(
            value,
            bool,
        ):

            return value

        if value is None:

            return False

        if isinstance(
            value,
            str,
        ):

            return (
                value
                .strip()
                .lower()
                in {
                    "true",
                    "1",
                    "yes",
                }
            )

        return bool(
            value
        )