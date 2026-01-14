"""
A2UI Demo Test - Verify A2UI rendering in hndl-it floater
Run this to see A2UI components rendered in the quick dialog.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from floater.quick_dialog import QuickDialog


def demo_a2ui():
    """Run A2UI rendering demo."""
    app = QApplication(sys.argv)
    
    # Create dialog
    dialog = QuickDialog()
    dialog.show()
    dialog.apply_mode("full")
    dialog.expand_to_log()
    
    # Demo A2UI payload - simulates Airweave search results
    demo_payload = {
        "type": "List",
        "id": "demo_results",
        "props": {"title": "🔍 Airweave Search Results"},
        "children": [
            {
                "type": "Card",
                "id": "result_1",
                "props": {
                    "title": "Y-IT Research on AI Automation",
                    "subtitle": "Score: 0.92 | Source: research_swarm"
                },
                "children": [
                    {
                        "type": "Text",
                        "id": "result_1_text",
                        "props": {
                            "text": "The AAA (AI Automation Agency) model has a 73% failure rate according to our verified data. Key claims from gurus include..."
                        }
                    },
                    {
                        "type": "Button",
                        "id": "result_1_btn",
                        "props": {
                            "label": "📖 View Full",
                            "action": "expand_result",
                            "payload": {"entity_id": "aaa_research_001"}
                        }
                    }
                ]
            },
            {
                "type": "Card",
                "id": "result_2",
                "props": {
                    "title": "GPU Price History Analysis",
                    "subtitle": "Score: 0.85 | Source: browser_agent"
                },
                "children": [
                    {
                        "type": "Text",
                        "id": "result_2_text",
                        "props": {
                            "text": "RTX 2060 12GB prices tracked from $289 to $349 over Q4 2025..."
                        }
                    },
                    {
                        "type": "Button",
                        "id": "result_2_btn",
                        "props": {
                            "label": "📊 View Chart",
                            "action": "show_chart",
                            "payload": {"entity_id": "gpu_prices_001"}
                        }
                    }
                ]
            },
            {
                "type": "Divider",
                "id": "divider_1",
                "props": {}
            },
            {
                "type": "ProgressBar",
                "id": "sync_progress",
                "props": {"value": 75, "max": 100}
            },
            {
                "type": "Text",
                "id": "sync_status",
                "props": {"text": "Syncing with Airweave: 75% complete"}
            }
        ]
    }
    
    # Render the A2UI payload
    dialog.render_a2ui(demo_payload)
    dialog.add_log("✅ A2UI Demo loaded - check the render zone!")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    demo_a2ui()
