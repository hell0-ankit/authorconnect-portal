from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from services.ai_service import generate_ticket_response_draft


class RoyaltyDraftSafetyTests(SimpleTestCase):
    @patch("services.ai_service._generate_text")
    def test_escalation_request_keeps_verified_context_and_disclaims_action(
        self, generate_text
    ):
        draft = generate_ticket_response_draft(
            "Royalty status",
            "Any update on this?",
            "Title: Echoes of the Silent Valley",
            book_title="Echoes of the Silent Valley",
            pending_royalty=Decimal("5952.00"),
            conversation_context=(
                "Author: Please escalate this to the royalty team and "
                "let me know the expected resolution time."
            ),
        )

        self.assertEqual(
            draft,
            "Dear Author,\n\n"
            "Thank you for contacting us regarding your pending royalty "
            "of Rs 5,952 for 'Echoes of the Silent Valley.'\n\n"
            "Your request requires review by our royalty team to verify "
            "the pending balance, identify the relevant sales period, and "
            "confirm the payment status. We cannot confirm an exact "
            "resolution date until the details have been reviewed.\n\n"
            "Please note that your request has not yet been confirmed as "
            "escalated. We will provide an update once the review process "
            "and expected timeline are verified.\n\n"
            "Best regards,\n"
            "AuthorConnect Support",
        )
        self.assertNotIn("November", draft)
        self.assertNotIn("15th", draft)
        generate_text.assert_not_called()

    @patch("services.ai_service._generate_text")
    def test_missing_sales_period_gets_no_invented_payment_schedule(
        self, generate_text
    ):
        draft = generate_ticket_response_draft(
            "Royalty payout status",
            "My pending royalty is Rs 5952. When will it be paid?",
            "",
            pending_royalty=Decimal("5952.00"),
        )

        self.assertIn("verify the relevant sales period and payment status", draft)
        self.assertIn("before confirming a payment or resolution timeline", draft)
        self.assertNotIn("October", draft)
        self.assertNotIn("15th", draft)
        self.assertNotIn("45 days", draft)
        generate_text.assert_not_called()

    @patch("services.ai_service._generate_text")
    def test_royalty_escalation_context_is_retained_without_a_book_record(
        self, generate_text
    ):
        draft = generate_ticket_response_draft(
            "Payment inquiry",
            "Please escalate this to the royalty team.",
            "",
            conversation_context=(
                "Author: My pending amount is Rs 5,952 for "
                "Echoes of the Silent Valley."
            ),
        )

        self.assertIn("has not yet been confirmed as escalated", draft)
        self.assertIn("relevant sales period", draft)
        self.assertNotIn("Echoes of the Silent Valley", draft)
        self.assertNotIn("Rs 5,952", draft)
        generate_text.assert_not_called()

    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
    @patch(
        "services.ai_service.FAQ_CONTENT",
        "Royalty payments are processed within 45 days after the end of "
        "the sales month.",
    )
    @patch("services.ai_service.genai.Client")
    def test_configured_45_day_policy_is_passed_without_substitution(
        self, client_class
    ):
        client = client_class.return_value
        client.models.generate_content.return_value = SimpleNamespace(
            text="We will review your request."
        )

        generate_ticket_response_draft(
            "Book status",
            "Please share an update on my book.",
            "",
        )

        system_instruction = (
            client.models.generate_content.call_args.kwargs[
                "config"
            ].system_instruction
        )
        self.assertIn("within 45 days after the end of the sales month", system_instruction)
        self.assertIn("do not substitute other", system_instruction)
        self.assertIn("Never provide a payment or resolution date unless", system_instruction)
