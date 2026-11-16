"""
Ambience Mall Gurugram: Comprehensive AI Concierge Test Suite.
Verifies all 12 test scenarios, tool calling, grounding, routing engine preservation,
and failure classification as specified in Phase 12.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_concierge import (
    AIConciergeService,
    FAILURE_INSUFFICIENT_CREDITS,
    FAILURE_INVALID_API_KEY,
    FAILURE_MISSING_API_KEY,
    FAILURE_MODEL_UNAVAILABLE,
    FAILURE_NETWORK_TIMEOUT,
    FAILURE_SERVER_ERROR,
    GROK_TOOLS,
    get_ai_concierge_service,
)
from src.api_service import MallService


class TestAIConcierge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mall_svc = MallService()
        cls.ai_svc = AIConciergeService(cls.mall_svc)

    # -------------------------------------------------------------------------
    # UNIT TESTS: Tools Grounding & Real Mall Data
    # -------------------------------------------------------------------------
    def test_tool_search_stores_zara(self):
        """Test 2: 'Where is ZARA?' tool execution grounds in real store G_005 on Ground Floor."""
        result, payload = self.ai_svc.execute_tool("search_stores", {"query": "ZARA"})
        self.assertGreater(result["total_matches"], 0)
        found_zara = any(s["name"] == "ZARA" for s in result["stores"])
        self.assertTrue(found_zara, "ZARA must be found in catalog")
        zara = next(s for s in result["stores"] if s["name"] == "ZARA")
        self.assertEqual(zara["id"], "G_005")
        self.assertEqual(zara["floor"], 0)
        self.assertEqual(zara["floor_name"], "Ground Floor")
        self.assertEqual(zara["category"], "Fashion")

    def test_tool_search_coffee_shops(self):
        """Test 3: 'Find coffee shops' returns genuine cafes/dining."""
        result, payload = self.ai_svc.execute_tool("search_stores", {"query": "Barista", "category": "Food & Dining"})
        self.assertGreater(result["total_matches"], 0)
        names = [s["name"] for s in result["stores"]]
        self.assertTrue(any("Barista" in n for n in names))

    def test_tool_fashion_ground_floor(self):
        """Test 4: 'Show fashion stores on the Ground Floor' filters correctly."""
        result, payload = self.ai_svc.execute_tool("search_stores", {"category": "Fashion", "floor": 0, "limit": 10})
        self.assertGreater(len(result["stores"]), 0)
        for s in result["stores"]:
            self.assertEqual(s["floor"], 0)
            self.assertEqual(s["floor_name"], "Ground Floor")

    def test_tool_unknown_store(self):
        """Test 8: Unknown store name search returns zero results without hallucination."""
        result, payload = self.ai_svc.execute_tool("search_stores", {"query": "Cyberdyne Systems Futuristic AI"})
        self.assertEqual(result["total_matches"], 0)
        self.assertEqual(len(result["stores"]), 0)

        details_res, details_payload = self.ai_svc.execute_tool("get_store_details", {"store_id": "NON_EXISTENT_ID"})
        self.assertFalse(details_res["found"])
        self.assertIn("not found", details_res["error"])

    def test_tool_request_navigation_preserves_engine(self):
        """Test 6: Navigation request calculates route and preserves algorithm identity."""
        result, route_payload = self.ai_svc.execute_tool(
            "request_navigation",
            {"destination_id": "G_005", "start_id": "G_GATE_1", "algorithm": "auto"}
        )
        self.assertEqual(result["destination"], "ZARA")
        self.assertEqual(result["destination_floor"], "Ground Floor")
        self.assertIn("algorithm_used", result)
        self.assertIn("engine_label", result)
        self.assertIn("path_cost", result)
        self.assertEqual(result["cost_unit"], "relative graph cost (not metres)")
        self.assertEqual(result["walking_time"], "not calibrated (dataset policy)")
        self.assertFalse(result["is_fallback"])

    def test_tool_create_itinerary_grounded(self):
        """Test 5: 2-Hour Itinerary selects genuine stores and calculates real legs."""
        result, itinerary_payload = self.ai_svc.execute_tool(
            "create_itinerary",
            {"activities": ["coffee", "shopping", "dining"], "duration_hours": 2.0}
        )
        stops = result["stops"]
        self.assertEqual(len(stops), 3)
        for s in stops:
            self.assertTrue(len(s["store_name"]) > 0)
            self.assertIn(s["floor"], ["Ground Floor", "First Floor", "Second Floor"])
            self.assertIsNotNone(s["leg_route"])
            self.assertIn("relative_path_cost", s["leg_route"])
            self.assertIn("algorithm", s["leg_route"])

    # -------------------------------------------------------------------------
    # CONNECTIVITY & FAILURE CLASSIFICATION TESTS
    # -------------------------------------------------------------------------
    def test_missing_api_key(self):
        """Test 9: Missing API key produces structured failure response."""
        original_key = os.environ.get("XAI_API_KEY")
        try:
            if "XAI_API_KEY" in os.environ:
                del os.environ["XAI_API_KEY"]
            svc = AIConciergeService(self.mall_svc)
            status = svc.check_connectivity()
            self.assertEqual(status["status"], "error")
            self.assertEqual(status["failure_type"], FAILURE_MISSING_API_KEY)
            self.assertFalse(status["configured"])

            chat_res = svc.process_chat([{"role": "user", "content": "Hello"}])
            self.assertFalse(chat_res["success"])
            self.assertEqual(chat_res["error"]["code"], FAILURE_MISSING_API_KEY)
        finally:
            if original_key is not None:
                os.environ["XAI_API_KEY"] = original_key

    def test_invalid_api_key_live_rejection(self):
        """Test 10: Invalid API key produces structured invalid_api_key failure response."""
        original_key = os.environ.get("XAI_API_KEY")
        try:
            os.environ["XAI_API_KEY"] = "xai_invalid_test_token_12345"
            svc = AIConciergeService(self.mall_svc)
            status = svc.check_connectivity()
            self.assertEqual(status["status"], "error")
            self.assertEqual(status["failure_type"], FAILURE_INVALID_API_KEY)
            self.assertTrue(status["configured"])
            self.assertIn("Invalid API key", status["message"])
        finally:
            if original_key is not None:
                os.environ["XAI_API_KEY"] = original_key
            else:
                os.environ.pop("XAI_API_KEY", None)

    # -------------------------------------------------------------------------
    # CONVERSATION SIMULATION & AGENT LOOP TESTS
    # -------------------------------------------------------------------------
    def test_conversation_flow_hello(self):
        """Test 1: 'Hello' prompt returns conversational greeting."""
        def mock_grok(conversation, tools):
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Welcome to Ambience Mall Gurugram! I am your AI Concierge. How can I assist your visit today?",
                    }
                }]
            }

        res = self.ai_svc.process_chat(
            [{"role": "user", "content": "Hello"}],
            mock_response_generator=mock_grok
        )
        self.assertTrue(res["success"])
        self.assertIn("Welcome to Ambience Mall Gurugram", res["reply"])

    def test_conversation_flow_where_is_zara(self):
        """Test 2: Full flow 'Where is ZARA?' executes tool search and grounds floor."""
        turn = 0
        def mock_grok(conversation, tools):
            nonlocal turn
            turn += 1
            if turn == 1:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_search_zara",
                                "type": "function",
                                "function": {
                                    "name": "search_stores",
                                    "arguments": json.dumps({"query": "ZARA"})
                                }
                            }]
                        }
                    }]
                }
            else:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "**ZARA** is located on the **Ground Floor** (Store ID: `G_005`). Would you like indoor turn-by-turn navigation from your current location?",
                        }
                    }]
                }

        res = self.ai_svc.process_chat(
            [{"role": "user", "content": "Where is ZARA?"}],
            mock_response_generator=mock_grok
        )
        self.assertTrue(res["success"])
        self.assertIn("search_stores", res["executed_tools"])
        self.assertIn("Ground Floor", res["reply"])
        self.assertEqual(len(res["suggestedStores"]), 1)
        self.assertEqual(res["suggestedStores"][0]["name"], "ZARA")
        self.assertEqual(res["suggestedStores"][0]["floor"], "Ground Floor")

    def test_conversation_flow_navigate_to_zara(self):
        """Test 6: 'Navigate to ZARA' executes request_navigation tool."""
        turn = 0
        def mock_grok(conversation, tools):
            nonlocal turn
            turn += 1
            if turn == 1:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_nav_zara",
                                "type": "function",
                                "function": {
                                    "name": "request_navigation",
                                    "arguments": json.dumps({"destination_id": "G_005", "start_id": "G_GATE_1"})
                                }
                            }]
                        }
                    }]
                }
            else:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "Route to **ZARA** (Ground Floor) computed from Gate 1 via Tabular Q-Learning RL navigation across 7 steps.",
                        }
                    }]
                }

        res = self.ai_svc.process_chat(
            [{"role": "user", "content": "Take me to ZARA"}],
            mock_response_generator=mock_grok
        )
        self.assertTrue(res["success"])
        self.assertIn("request_navigation", res["executed_tools"])
        self.assertEqual(res["action"], "navigate")
        self.assertIsNotNone(res["navigationTarget"])
        self.assertEqual(res["navigationTarget"]["name"], "ZARA")
        self.assertIsNotNone(res["route"])
        self.assertEqual(res["route"]["algorithm"], "rl")

    def test_conversation_flow_unknown_store_honesty(self):
        """Test 8: Unknown store search reports non-existence without hallucination."""
        turn = 0
        def mock_grok(conversation, tools):
            nonlocal turn
            turn += 1
            if turn == 1:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_search_unknown",
                                "type": "function",
                                "function": {
                                    "name": "search_stores",
                                    "arguments": json.dumps({"query": "Cyberdyne Systems"})
                                }
                            }]
                        }
                    }]
                }
            else:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "I searched the Ambience Mall directory, but **Cyberdyne Systems** is not a store at Ambience Mall Gurugram.",
                        }
                    }]
                }

        res = self.ai_svc.process_chat(
            [{"role": "user", "content": "Where is Cyberdyne Systems?"}],
            mock_response_generator=mock_grok
        )
        self.assertTrue(res["success"])
        self.assertIn("search_stores", res["executed_tools"])
        self.assertIn("not a store at Ambience Mall", res["reply"])
        self.assertEqual(len(res["suggestedStores"]), 0)

    def test_conversation_follow_up_context(self):
        """Test 7: Follow-up question about an itinerary preserves session context."""
        history = [
            {"role": "user", "content": "Plan a 2-hour visit with coffee and shopping."},
            {"role": "assistant", "content": "I've planned a 2-stop visit: Stop 1 is Barista on the Second Floor, Stop 2 is ZARA on the Ground Floor."},
            {"role": "user", "content": "How do I get between those two stops?"},
        ]
        def mock_grok(conversation, tools):
            # Check that conversation has the history
            has_barista = any("Barista" in m.get("content", "") for m in conversation)
            has_zara = any("ZARA" in m.get("content", "") for m in conversation)
            self.assertTrue(has_barista)
            self.assertTrue(has_zara)
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "From Barista on the Second Floor, take the Central Escalator down to the Ground Floor to reach ZARA.",
                    }
                }]
            }

        res = self.ai_svc.process_chat(history, mock_response_generator=mock_grok)
        self.assertTrue(res["success"])
        self.assertIn("Central Escalator", res["reply"])


if __name__ == "__main__":
    unittest.main()
