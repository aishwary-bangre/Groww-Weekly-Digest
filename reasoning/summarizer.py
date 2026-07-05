import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ingestion.models import ProcessedReview

logger = logging.getLogger("groww_pulse.reasoning.summarizer")

class ThemeInsight(BaseModel):
    theme_name: str = Field(description="A short, 3-5 word name for the theme (e.g., 'Login Timeouts')")
    verbatim_quotes: List[str] = Field(description="Exact quotes extracted from the reviews matching this theme")
    action_ideas: List[str] = Field(description="Actionable ideas for the product/engineering team based on the feedback")

class Summarizer:
    """Integrates with an LLM (Llama 3.3 via Groq) to extract themes and strictly validate quotes."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        from langchain_groq import ChatGroq
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
        
        self.parser = JsonOutputParser(pydantic_object=ThemeInsight)
        self.prompt = PromptTemplate(
            template="""
            Analyze the following cluster of user reviews for the Groww app.
            Identify the primary overarching theme of these reviews.
            Extract 2-3 VERBATIM quotes that represent this theme perfectly.
            Provide 2 actionable ideas for the product team.
            
            {format_instructions}
            
            Reviews:
            {reviews_text}
            """,
            input_variables=["reviews_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.chain = self.prompt | self.llm | self.parser

    def _validate_quote(self, quote: str, original_texts: List[str]) -> bool:
        """
        Anti-Hallucination Gate.
        Returns True ONLY if the exact quote string exists inside any of the original reviews.
        """
        quote_clean = quote.strip().lower()
        for text in original_texts:
            if quote_clean in text.lower():
                return True
        return False

    def summarize_clusters(self, clusters: Dict[int, List[ProcessedReview]]) -> Dict[int, Optional[ThemeInsight]]:
        """
        Sends the text of the top clusters to the LLM for theme extraction,
        and enforces the anti-hallucination quote validation gate.
        """
        insights = {}
        
        for cluster_id, reviews in clusters.items():
            if cluster_id == -1:
                continue # Skip noise
                
            logger.info(f"Summarizing cluster {cluster_id} containing {len(reviews)} reviews...")
            
            # Combine texts for the prompt
            original_texts = [r.scrubbed_text for r in reviews]
            combined_text = "\n---\n".join(original_texts)
            
            try:
                # Call the real Gemini API
                raw_response = self.chain.invoke({"reviews_text": combined_text})
                response = ThemeInsight(**raw_response)
                
                # --- Anti-Hallucination Gate ---
                validated_quotes = []
                for quote in response.verbatim_quotes:
                    if self._validate_quote(quote, original_texts):
                        validated_quotes.append(quote)
                    else:
                        logger.warning(f"HALLUCINATION BLOCKED: The quote '{quote}' was not found in the source text.")
                        
                # Update the insight with only validated quotes
                response.verbatim_quotes = validated_quotes
                
                # If all quotes were hallucinations, we might want to flag the whole insight
                if not validated_quotes:
                    logger.error(f"Cluster {cluster_id} generated 0 valid quotes. Discarding theme.")
                    insights[cluster_id] = None
                else:
                    insights[cluster_id] = response
                    
            except Exception as e:
                logger.error(f"Failed to summarize cluster {cluster_id}: {e}")
                insights[cluster_id] = None
                
        logger.info(f"Successfully generated insights for {len([i for i in insights.values() if i])} clusters.")
        return insights
