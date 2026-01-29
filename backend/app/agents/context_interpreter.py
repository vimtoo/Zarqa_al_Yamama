"""
Context Interpreter Agent
Scrapes news and sentiment data from NewsData.io and GDELT
Maps to knowledge graph and outputs sentiment impact scores
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import httpx

from app.config import settings
from app.graph.state import ForecastState, ContextSentimentOutput
from app.llm.client import llm_manager
from app.data_sources.news_client import NewsClient
from app.core.http_client import GlobalHTTPClient

logger = logging.getLogger(__name__)


class NewsDataClient:
    """Client for NewsData.io API"""
    
    def __init__(self):
        self.api_key = settings.NEWSDATA_API_KEY
        self.base_url = settings.NEWSDATA_BASE_URL
        
        if not self.api_key:
            logger.warning("NewsData.io API key not configured")
    
    async def get_news(
        self,
        query: str = None,
        category: str = None,
        language: str = "en",
        country: str = None,
        domain: str = None,
        page: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsData.io API
        
        Args:
            query: Keywords to search for
            category: News category (business, politics, world, etc.)
            language: Language code
            country: Country code (us, gb, ae, sa, etc.)
            domain: Specific news domain
            page: Pagination token
            
        Returns:
            List of news articles
        """
        if not self.api_key:
            logger.error("NewsData.io API key not set")
            return []
        
        url = f"{self.base_url}/latest"
        
        params = {
            "apikey": self.api_key,
            "language": language
        }
        
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if country:
            params["country"] = country
        if domain:
            params["domain"] = domain
        if page:
            params["page"] = page
        
        try:
            client = GlobalHTTPClient.get_client()
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("results", [])
                logger.info(f"Fetched {len(articles)} articles from NewsData.io")
                return articles
            else:
                logger.error(f"NewsData.io API error: {response.status_code} - {response.text}")
                return []
                    
        except Exception as e:
            logger.error(f"NewsData.io request error: {str(e)}")
            return []
    
    async def get_crypto_news(self, coin: str = None) -> List[Dict[str, Any]]:
        """Fetch cryptocurrency news"""
        return await self.get_news(
            query=coin or "cryptocurrency bitcoin",
            category="business"
        )
    
    async def get_business_news(self, keywords: str = None) -> List[Dict[str, Any]]:
        """Fetch business news"""
        return await self.get_news(
            query=keywords,
            category="business"
        )
    
    async def get_world_news(self, keywords: str = None) -> List[Dict[str, Any]]:
        """Fetch world/geopolitical news"""
        return await self.get_news(
            query=keywords,
            category="world"
        )


class GDELTClient:
    """Client for GDELT 2.0 Doc API (free, no key required)"""
    
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    async def search_docs(
        self,
        query: str,
        mode: str = "ArtList",
        max_records: int = 25,
        timespan: str = "7d"
    ) -> List[Dict[str, Any]]:
        """
        Search GDELT document database
        
        Args:
            query: Search query
            mode: Response mode (ArtList, TimelineVol, etc.)
            max_records: Maximum number of records
            timespan: Time window (7d, 30d, etc.)
            
        Returns:
            List of articles/events
        """
        params = {
            "query": query,
            "mode": mode,
            "maxrecords": max_records,
            "timespan": timespan,
            "format": "json"
        }
        
        try:
            client = GlobalHTTPClient.get_client()
            response = await client.get(self.BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                logger.info(f"Fetched {len(articles)} articles from GDELT")
                return articles
            else:
                logger.warning(f"GDELT API error: {response.status_code}")
                return []
                    
        except Exception as e:
            logger.warning(f"GDELT request error: {str(e)}")
            return []
    
    async def get_tone_timeline(
        self,
        query: str,
        timespan: str = "30d"
    ) -> Dict[str, Any]:
        """Get sentiment/tone timeline for a topic"""
        params = {
            "query": query,
            "mode": "TimelineTone",
            "timespan": timespan,
            "format": "json"
        }
        
        try:
            client = GlobalHTTPClient.get_client()
            response = await client.get(self.BASE_URL, params=params)
            
            if response.status_code == 200:
                return response.json()
            return {}
                    
        except Exception as e:
            logger.warning(f"GDELT tone timeline error: {str(e)}")
            return {}


class ContextInterpreter:
    """
    Agent responsible for narrative intelligence and sentiment analysis.
    Integrates with NewsData.io, GDELT, and LLM analysis.
    """

    def __init__(self):
        self.enabled = settings.CONTEXT_INTERPRETER_ENABLED
        self.enabled = settings.CONTEXT_INTERPRETER_ENABLED
        self.news_client = NewsClient()
        self.gdelt = GDELTClient()
        # self.newsdata = NewsDataClient() # Deprecated/Merged

    async def analyze(self, state: ForecastState) -> Dict[str, Any]:
        """
        Main analysis method for context interpretation.
        
        Args:
            state: Current ForecastState
            
        Returns:
            Updated state with context sentiment outputs
        """
        if not self.enabled:
            logger.warning("Context Interpreter is disabled")
            return state

        try:
            logger.info(f"Context Interpreter starting analysis for scenario: {state['scenario']}")
            
            # Map scenario to search query
            search_query = self._map_scenario_to_query(state['scenario'])
            
            # Fetch news and events data from multiple sources
            news_data = await self._fetch_news_data(search_query, state['scenario'])
            
            if news_data is None or len(news_data) == 0:
                state['context_error'] = "Failed to fetch news data"
                state['errors'].append("Context Interpreter: No news data available")
                # Use fallback data
                news_data = self._get_fallback_news(state['scenario'])
            
            # Analyze sentiment using LLM
            sentiment_analysis = await self._analyze_sentiment_with_llm(news_data, state['scenario'])
            
            # Extract themes and actors
            themes, actors = self._extract_themes_and_actors(news_data)
            
            # Generate context output
            context_output = self._generate_context_output(
                sentiment_analysis, themes, actors, news_data, state['scenario']
            )
            
            # Update state
            state['context_sentiment'] = context_output
            state['context_confidence'] = context_output.get('confidence', 0.0)
            state['context_themes'] = context_output.get('related_themes', [])
            state['context_key_actors'] = context_output.get('key_actors', [])
            state['context_mentions_24h'] = context_output.get('mentions_24h', 0)
            data_sources = []
            if settings.NEWSAPI_KEY or settings.GNEWS_API_KEY:
                data_sources.append('Global News (NewsAPI/GNews)')
            if settings.GDELT_ENABLED:
                data_sources.append('GDELT 2.0 Event Database')
            data_sources.append('LLM Sentiment Analysis')
            state['context_data_sources'] = data_sources
            state['agents_executed'].append('context_interpreter')
            
            logger.info(f"Context Interpreter completed. Sentiment: {sentiment_analysis.get('score', 0):.2f}")
            
        except Exception as e:
            logger.error(f"Context Interpreter error: {str(e)}")
            state['context_error'] = str(e)
            state['errors'].append(f"Context Interpreter: {str(e)}")
            state['warnings'].append("Context analysis unavailable due to error")
        
        return state

    def _map_scenario_to_query(self, scenario: str) -> str:
        """Map scenario to search query keywords"""
        scenario_lower = scenario.lower()
        
        # Oil-related scenarios
        if any(word in scenario_lower for word in ['oil', 'crude', 'petroleum', 'opec']):
            return "oil prices OPEC crude petroleum"
        
        # Gold-related scenarios
        if any(word in scenario_lower for word in ['gold', 'precious metal']):
            return "gold prices precious metals"
        
        # Currency scenarios
        if any(word in scenario_lower for word in ['dollar', 'euro', 'currency', 'forex']):
            return "currency exchange forex dollar"
        
        # Crypto scenarios
        if any(word in scenario_lower for word in ['bitcoin', 'crypto', 'blockchain']):
            return "bitcoin cryptocurrency blockchain"
        
        # Middle East scenarios
        if any(word in scenario_lower for word in ['middle east', 'gulf', 'saudi', 'uae']):
            return "Middle East Gulf region geopolitics"
        
        # Energy scenarios
        if any(word in scenario_lower for word in ['energy', 'gas', 'renewable']):
            return "energy natural gas renewable"
        
        # Default to economic news
        return scenario if len(scenario) > 5 else "global economy markets"

    async def _fetch_news_data(self, query: str, scenario: str) -> List[Dict[str, Any]]:
        """
        Fetch news and events data from NewsData.io and GDELT.
        """
        all_news = []
        
        try:
            # Fetch from NewsClient (NewsAPI + GNews)
            try:
                logger.info(f"Fetching news from NewsAPI/GNews for: {query}")
                news_results = await self.news_client.get_news(query, limit=10, days_back=7)
                
                for article in news_results:
                    all_news.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', 'NewsAPI/GNews'),
                        'url': article.get('url', ''),
                        'date': article.get('published_at', ''),
                        'sentiment': 0.0,  # Will be analyzed by LLM
                        'themes': [],
                        'country': [],
                        'api_source': 'news_client'
                    })
            except Exception as e:
                logger.error(f"NewsClient fetch failed: {e}")

            # Keep existing logic only for GDELT if needed, block old NewsData logic
            # if settings.NEWSDATA_ENABLED: ... (Removed/Replaced)
            
            # Fetch from GDELT (if enabled)
            if settings.GDELT_ENABLED:
                logger.info(f"Fetching news from GDELT for: {query}")
                gdelt_results = await self.gdelt.search_docs(
                    query=query,
                    max_records=10,
                    timespan="7d"
                )
                
                if gdelt_results:
                    for article in gdelt_results[:10]:
                        all_news.append({
                            'title': article.get('title', ''),
                            'description': '',
                            'source': article.get('domain', 'GDELT'),
                            'url': article.get('url', ''),
                            'date': article.get('seendate', ''),
                            'sentiment': article.get('tone', 0.0) / 10 if article.get('tone') else 0.0,
                            'themes': [],
                            'country': article.get('sourcecountry', ''),
                            'api_source': 'gdelt'
                        })
            else:
                logger.info("GDELT disabled; skipping.")
            
            logger.info(f"Total news items collected: {len(all_news)}")
            return all_news
            
        except Exception as e:
            logger.error(f"Error fetching news data: {str(e)}")
            return []

    def _get_fallback_news(self, scenario: str) -> List[Dict[str, Any]]:
        """Get fallback news data when APIs fail"""
        logger.info("Using fallback news data")
        return [
            {
                'title': f'Market Analysis: {scenario} Shows Mixed Signals',
                'description': 'Markets continue to show volatility amid global uncertainty.',
                'source': 'Fallback Data',
                'url': '',
                'date': datetime.now().isoformat(),
                'sentiment': 0.0,
                'themes': ['Market Analysis'],
                'country': [],
                'api_source': 'fallback'
            }
        ]

    async def _analyze_sentiment_with_llm(
        self,
        news_data: List[Dict[str, Any]],
        scenario: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment from news data using LLM.
        """
        try:
            # Prepare news summary for LLM
            news_summary = []
            for article in news_data[:10]:  # Limit to 10 articles for LLM
                news_summary.append({
                    'title': article.get('title', ''),
                    'source': article.get('source', ''),
                    'date': str(article.get('date', '')),
                    'initial_sentiment': article.get('sentiment', 0)
                })
            
            # Use LLM for sentiment analysis
            analysis = await llm_manager.analyze(
                data={
                    'scenario': scenario,
                    'news_articles': news_summary
                },
                analysis_type="sentiment",
                context=f"News sentiment analysis for: {scenario}"
            )
            
            if analysis and not analysis.get('parse_error'):
                return {
                    'score': analysis.get('sentiment_score', 0.0),
                    'themes': analysis.get('themes', []),
                    'market_impact': analysis.get('market_impact', 'neutral'),
                    'confidence': analysis.get('confidence', 0.7),
                    'llm_analysis': True
                }
            
            # Fallback to simple averaging if LLM fails
            sentiments = [a.get('sentiment', 0) for a in news_data if a.get('sentiment')]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            return {
                'score': avg_sentiment,
                'positive_count': sum(1 for s in sentiments if s > 0.3),
                'negative_count': sum(1 for s in sentiments if s < -0.3),
                'neutral_count': sum(1 for s in sentiments if -0.3 <= s <= 0.3),
                'momentum': 'neutral',
                'llm_analysis': False
            }
            
        except Exception as e:
            logger.warning(f"LLM sentiment analysis failed: {str(e)}")
            
            # Basic sentiment calculation
            sentiments = [a.get('sentiment', 0) for a in news_data if a.get('sentiment')]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            return {
                'score': avg_sentiment,
                'positive_count': sum(1 for s in sentiments if s > 0.3),
                'negative_count': sum(1 for s in sentiments if s < -0.3),
                'neutral_count': sum(1 for s in sentiments if -0.3 <= s <= 0.3),
                'momentum': 'neutral',
                'llm_analysis': False
            }

    def _extract_themes_and_actors(
        self, news_data: List[Dict[str, Any]]
    ) -> tuple:
        """Extract themes and key actors from news data"""
        themes = {}
        actors = set()
        
        # Actor keywords to look for
        actor_keywords = {
            'OPEC': ['OPEC', 'opec'],
            'United States': ['US', 'U.S.', 'United States', 'Biden', 'Washington', 'Federal Reserve', 'Fed'],
            'China': ['China', 'Chinese', 'Beijing', 'Xi Jinping'],
            'Russia': ['Russia', 'Russian', 'Moscow', 'Putin'],
            'Saudi Arabia': ['Saudi', 'Riyadh', 'MBS', 'Aramco'],
            'Iran': ['Iran', 'Iranian', 'Tehran'],
            'European Union': ['EU', 'European Union', 'ECB', 'Brussels'],
            'UAE': ['UAE', 'Emirates', 'Abu Dhabi', 'Dubai'],
            'Israel': ['Israel', 'Israeli', 'Tel Aviv'],
        }
        
        for item in news_data:
            # Extract themes
            for theme in item.get('themes', []):
                if isinstance(theme, str):
                    themes[theme] = themes.get(theme, 0) + 1
            
            # Extract actors from title and description
            text = f"{item.get('title', '')} {item.get('description', '')}"
            
            for actor, keywords in actor_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        actors.add(actor)
                        break
        
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        
        return [t[0] for t in sorted_themes[:5]], list(actors)[:5]

    def _generate_context_output(
        self,
        sentiment_analysis: Dict[str, Any],
        themes: List[str],
        actors: List[str],
        news_data: List[Dict[str, Any]],
        scenario: str
    ) -> ContextSentimentOutput:
        """Generate context output with sentiment and themes"""
        
        # Calculate total mentions
        total_mentions = len(news_data) * 100  # Estimated reach
        
        # Determine narrative momentum
        recent_sentiments = [n.get('sentiment', 0) for n in news_data[:5]]
        older_sentiments = [n.get('sentiment', 0) for n in news_data[5:10]]
        
        avg_recent = sum(recent_sentiments) / len(recent_sentiments) if recent_sentiments else 0
        avg_older = sum(older_sentiments) / len(older_sentiments) if older_sentiments else 0
        
        if avg_recent > avg_older + 0.1:
            momentum = 'improving'
        elif avg_recent < avg_older - 0.1:
            momentum = 'deteriorating'
        else:
            momentum = 'stable'
        
        return {
            'theme': scenario,
            'sentiment_score': float(sentiment_analysis.get('score', 0.0)),
            'narrative_momentum': momentum,
            'mentions_24h': total_mentions,
            'key_actors': actors if actors else ['Global Markets'],
            'related_themes': themes if themes else [
                'Market Analysis',
                'Economic Outlook',
                'Risk Assessment'
            ],
            'confidence': float(sentiment_analysis.get('confidence', 0.75)),
            'llm_enhanced': sentiment_analysis.get('llm_analysis', False),
            'market_impact': sentiment_analysis.get('market_impact', 'moderate'),
            'data_sources': [
                'NewsData.io (Global News)',
                'GDELT 2.0 Event Database',
                'LLM Analysis (OpenRouter/DeepSeek)'
            ],
            'articles_analyzed': len(news_data),
            'timestamp': datetime.now()
        }
