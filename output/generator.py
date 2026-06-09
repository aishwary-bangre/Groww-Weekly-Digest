import logging
from typing import Dict
from datetime import datetime
from reasoning.summarizer import ThemeInsight

logger = logging.getLogger("groww_pulse.output.generator")

class OutputGenerator:
    """Transforms verified insights into final payload structures for MCP."""
    
    def _render_markdown_report(self, insights: Dict[int, ThemeInsight]) -> str:
        """Generates the Markdown representation of the Weekly Pulse."""
        today = datetime.now().strftime("%Y-%m-%d")
        iso_week = datetime.now().isocalendar()[1]
        
        lines = [
            f"## Weekly Review Pulse: Week {iso_week} ({today})",
            "",
            "Here are the top themes extracted from recent Google Play Store reviews:",
            ""
        ]
        
        for cluster_id, insight in insights.items():
            if not insight:
                continue
                
            lines.append(f"### Theme: {insight.theme_name}")
            lines.append("**Verbatim Quotes:**")
            for quote in insight.verbatim_quotes:
                lines.append(f"- \"{quote}\"")
                
            lines.append("")
            lines.append("**Actionable Ideas for Product/Engineering:**")
            for action in insight.action_ideas:
                lines.append(f"- {action}")
            lines.append("")
            lines.append("---")
            lines.append("")
            
        return "\n".join(lines)

    def generate_doc_payload(self, insights: Dict[int, ThemeInsight], doc_id: str) -> dict:
        """
        Creates the JSON payload required to append a section via Docs MCP.
        Assumes the MCP tool expects a target doc_id and the markdown content.
        """
        markdown_content = self._render_markdown_report(insights)
        
        logger.info("Generated Google Docs MCP payload.")
        return {
            "documentId": doc_id,
            "content": markdown_content,
            "action": "append"
        }
        
    def generate_email_payload(self, insights: Dict[int, ThemeInsight], doc_link: str, recipients: list[str]) -> dict:
        """
        Creates the JSON payload for the Gmail MCP tool.
        Instead of sending the full report, it sends a deep link teaser.
        """
        iso_week = datetime.now().isocalendar()[1]
        
        # Get just the top 2 theme names for the email teaser
        valid_insights = [i for i in insights.values() if i]
        top_themes = [i.theme_name for i in valid_insights[:2]]
        teaser_text = ", ".join(top_themes) if top_themes else "General Feedback"
        
        html_body = f"""
        <html>
            <body>
                <h2>Groww Weekly Pulse (Week {iso_week}) is ready!</h2>
                <p>This week's top themes include: <strong>{teaser_text}</strong>.</p>
                <p>Click below to read the full report, verbatim quotes, and action items in Google Docs:</p>
                <br>
                <a href="{doc_link}" style="display: inline-block; padding: 10px 20px; background-color: #00E676; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">View Full Pulse Report</a>
            </body>
        </html>
        """
        
        logger.info("Generated Gmail MCP payload.")
        return {
            "to": recipients,
            "subject": f"Groww Weekly Pulse - Week {iso_week}",
            "body": html_body,
            "isHtml": True
        }
