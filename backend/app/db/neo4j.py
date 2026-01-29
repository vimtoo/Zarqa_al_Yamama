"""
Neo4j Knowledge Graph Client
Manages relationships between geopolitical actors, themes, and events
Supports Neo4j Aura cloud deployment
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """Client for Neo4j knowledge graph with Aura cloud support (Async)"""
    
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        
        self.driver = self._create_driver()
        
        # Initialization logic moved to a separate async method since __init__ cannot be async
        # Call await start() in main startup

    def _create_driver(self):
        """Create Neo4j driver with proper authentication"""
        try:
            logger.info(f"Connecting to Neo4j at: {self.uri}")
            
            driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=200,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create Neo4j driver: {str(e)}")
            return None

    async def verify_connection(self):
        """Verify connectivity and initialize graph"""
        if not self.driver:
            return
            
        try:
            await self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
            await self._initialize_graph()
        except Exception as e:
            logger.error(f"Neo4j connection verification failed: {str(e)}")
    
    async def _initialize_graph(self):
        """Initialize graph constraints and indexes"""
        try:
            async with self.driver.session(database=self.database) as session:
                # Create constraints for Actor nodes
                await session.run("CREATE CONSTRAINT actor_name IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE")
                
                # Create constraints for Theme nodes
                await session.run("CREATE CONSTRAINT theme_name IF NOT EXISTS FOR (t:Theme) REQUIRE t.name IS UNIQUE")
                
                # Create constraints for Event nodes
                await session.run("CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE")
                
                # Create indexes
                await session.run("CREATE INDEX actor_country IF NOT EXISTS FOR (a:Actor) ON (a.country)")
                await session.run("CREATE INDEX theme_category IF NOT EXISTS FOR (t:Theme) ON (t.category)")
                await session.run("CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp)")
                
                logger.info("Neo4j graph initialized with constraints and indexes")
                
        except Exception as e:
            logger.warning(f"Error initializing Neo4j graph (non-fatal): {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Neo4j connection is healthy"""
        if not self.driver:
            return False
        
        try:
            async with self.driver.session(database=self.database) as session:
                await session.run("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False
    
    async def add_actor(
        self,
        name: str,
        country: str = None,
        actor_type: str = "Country",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add geopolitical actor to graph"""
        if not self.driver:
            return False
            
        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    """
                    MERGE (a:Actor {name: $name})
                    SET a.country = $country,
                        a.type = $actor_type,
                        a.updated_at = timestamp()
                    """,
                    name=name,
                    country=country,
                    actor_type=actor_type
                )
            
            logger.info(f"Added actor: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding actor: {str(e)}")
            return False
    
    async def add_theme(
        self,
        name: str,
        category: str = None,
        description: str = None
    ) -> bool:
        """Add theme to graph"""
        if not self.driver:
            return False
            
        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    """
                    MERGE (t:Theme {name: $name})
                    SET t.category = $category,
                        t.description = $description,
                        t.updated_at = timestamp()
                    """,
                    name=name,
                    category=category,
                    description=description
                )
            
            logger.info(f"Added theme: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding theme: {str(e)}")
            return False
    
    async def add_event(
        self,
        event_id: str,
        title: str,
        timestamp: str,
        source: str = None,
        sentiment: float = None,
        url: str = None
    ) -> bool:
        """Add event to graph"""
        if not self.driver:
            return False
            
        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(
                    """
                    MERGE (e:Event {id: $event_id})
                    SET e.title = $title,
                        e.timestamp = $timestamp,
                        e.source = $source,
                        e.sentiment = $sentiment,
                        e.url = $url,
                        e.created_at = timestamp()
                    """,
                    event_id=event_id,
                    title=title,
                    timestamp=timestamp,
                    source=source,
                    sentiment=sentiment,
                    url=url
                )
            
            logger.info(f"Added event: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding event: {str(e)}")
            return False
    
    async def create_relationship(
        self,
        source_type: str,
        source_name: str,
        relationship_type: str,
        target_type: str,
        target_name: str,
        weight: float = 1.0,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Create relationship between nodes"""
        if not self.driver:
            return False
            
        try:
            # Determine the key field based on node type
            source_key = "id" if source_type == "Event" else "name"
            target_key = "id" if target_type == "Event" else "name"
            
            async with self.driver.session(database=self.database) as session:
                query = f"""
                MATCH (source:{source_type} {{{source_key}: $source_name}})
                MATCH (target:{target_type} {{{target_key}: $target_name}})
                MERGE (source)-[r:{relationship_type}]->(target)
                SET r.weight = $weight,
                    r.updated_at = timestamp()
                """
                
                await session.run(
                    query,
                    source_name=source_name,
                    target_name=target_name,
                    weight=weight
                )
            
            logger.info(f"Created relationship: {source_name} -{relationship_type}-> {target_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return False
    
    async def link_event_to_actors(
        self,
        event_id: str,
        actors: List[str],
        relationship_type: str = "INVOLVES"
    ) -> int:
        """Link an event to multiple actors"""
        if not self.driver:
            return 0
            
        count = 0
        for actor in actors:
            if await self.create_relationship(
                source_type="Event",
                source_name=event_id,
                relationship_type=relationship_type,
                target_type="Actor",
                target_name=actor
            ):
                count += 1
        
        return count
    
    async def link_event_to_themes(
        self,
        event_id: str,
        themes: List[str],
        relationship_type: str = "RELATES_TO"
    ) -> int:
        """Link an event to multiple themes"""
        if not self.driver:
            return 0
            
        count = 0
        for theme in themes:
            if await self.create_relationship(
                source_type="Event",
                source_name=event_id,
                relationship_type=relationship_type,
                target_type="Theme",
                target_name=theme
            ):
                count += 1
        
        return count
    
    async def get_related_themes(self, actor_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get themes related to an actor"""
        if not self.driver:
            return []
            
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (a:Actor {name: $actor_name})-[r]->(t:Theme)
                    RETURN t.name as theme, r.weight as weight
                    ORDER BY r.weight DESC
                    LIMIT $limit
                    """,
                    actor_name=actor_name,
                    limit=limit
                )
                
                themes = []
                async for record in result:
                    themes.append({
                        'theme': record['theme'],
                        'weight': record['weight']
                    })
                
                return themes
                
        except Exception as e:
            logger.error(f"Error getting related themes: {str(e)}")
            return []
    
    async def get_actor_relationships(self, actor_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for an actor"""
        if not self.driver:
            return []
            
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (a:Actor {name: $actor_name})-[r]->(target)
                    RETURN type(r) as relationship_type, 
                           labels(target)[0] as target_type,
                           target.name as target_name, 
                           r.weight as weight
                    ORDER BY r.weight DESC
                    """,
                    actor_name=actor_name
                )
                
                relationships = []
                async for record in result:
                    relationships.append({
                        'type': record['relationship_type'],
                        'target_type': record['target_type'],
                        'target': record['target_name'],
                        'weight': record['weight']
                    })
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error getting actor relationships: {str(e)}")
            return []
    
    async def get_recent_events(
        self,
        limit: int = 10,
        actor: str = None,
        theme: str = None
    ) -> List[Dict[str, Any]]:
        """Get recent events, optionally filtered by actor or theme"""
        if not self.driver:
            return []
            
        try:
            async with self.driver.session(database=self.database) as session:
                if actor:
                    query = """
                    MATCH (e:Event)-[:INVOLVES]->(a:Actor {name: $filter_value})
                    RETURN e.id as id, e.title as title, e.timestamp as timestamp, 
                           e.source as source, e.sentiment as sentiment
                    ORDER BY e.created_at DESC
                    LIMIT $limit
                    """
                    filter_value = actor
                elif theme:
                    query = """
                    MATCH (e:Event)-[:RELATES_TO]->(t:Theme {name: $filter_value})
                    RETURN e.id as id, e.title as title, e.timestamp as timestamp,
                           e.source as source, e.sentiment as sentiment
                    ORDER BY e.created_at DESC
                    LIMIT $limit
                    """
                    filter_value = theme
                else:
                    query = """
                    MATCH (e:Event)
                    RETURN e.id as id, e.title as title, e.timestamp as timestamp,
                           e.source as source, e.sentiment as sentiment
                    ORDER BY e.created_at DESC
                    LIMIT $limit
                    """
                    filter_value = None
                
                if filter_value:
                    result = await session.run(query, filter_value=filter_value, limit=limit)
                else:
                    result = await session.run(query, limit=limit)
                
                events = []
                async for record in result:
                    events.append({
                        'id': record['id'],
                        'title': record['title'],
                        'timestamp': record['timestamp'],
                        'source': record['source'],
                        'sentiment': record['sentiment']
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"Error getting recent events: {str(e)}")
            return []
    
    async def find_shortest_path(
        self,
        source_name: str,
        target_name: str
    ) -> List[Dict[str, Any]]:
        """Find shortest path between two actors"""
        if not self.driver:
            return []
            
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH path = shortestPath(
                        (source:Actor {name: $source_name})-[*]-(target:Actor {name: $target_name})
                    )
                    RETURN [node in nodes(path) | node.name] as path,
                           length(path) as length
                    """,
                    source_name=source_name,
                    target_name=target_name
                )
                
                paths = []
                async for record in result:
                    paths.append({
                        'path': record['path'],
                        'length': record['length']
                    })
                
                return paths
                
        except Exception as e:
            logger.error(f"Error finding shortest path: {str(e)}")
            return []
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        if not self.driver:
            return {'error': 'No database connection'}
            
        try:
            async with self.driver.session(database=self.database) as session:
                actor_res = await session.run("MATCH (a:Actor) RETURN count(a) as count")
                actor_count = (await actor_res.single())['count']
                
                theme_res = await session.run("MATCH (t:Theme) RETURN count(t) as count")
                theme_count = (await theme_res.single())['count']
                
                event_res = await session.run("MATCH (e:Event) RETURN count(e) as count")
                event_count = (await event_res.single())['count']
                
                rel_res = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = (await rel_res.single())['count']
                
                return {
                    'actors': actor_count,
                    'themes': theme_count,
                    'events': event_count,
                    'relationships': rel_count,
                    'database': self.database,
                    'connected': True
                }
                
        except Exception as e:
            logger.error(f"Error getting graph stats: {str(e)}")
            return {'error': str(e), 'connected': False}
    
    async def create_hypothesis_edge(
        self,
        event_id: str,
        outcome_name: str,
        scenario_id: str,
        confidence: str,
        evidence_cluster_ids: List[str],
        provenance: str,
        weight: float = None
    ) -> bool:
        """
        Create a hypothesis edge between an Event and a potential Outcome.
        Mandatory fields: scenario_id, confidence, evidence_cluster_ids, provenance.
        Used for competing hypotheses (Phase H).
        """
        if not self.driver:
            return False
            
        try:
            async with self.driver.session(database=self.database) as session:
                # We MERGE the Outcome node to ensure it exists (it's abstract)
                # We MATCH the Event (must exist)
                # We MERGE the relationship with the unique scenario_id key to allow multiple edges
                
                query = """
                MATCH (e:Event {id: $event_id})
                MERGE (o:Outcome {name: $outcome_name})
                MERGE (e)-[r:HYPOTHESIZED_CAUSES {scenario_id: $scenario_id}]->(o)
                SET r.confidence = $confidence,
                    r.evidence_cluster_ids = $evidence_cluster_ids,
                    r.provenance = $provenance,
                    r.weight = $weight,
                    r.created_at = timestamp()
                """
                
                await session.run(
                    query,
                    event_id=event_id,
                    outcome_name=outcome_name,
                    scenario_id=scenario_id,
                    confidence=confidence,
                    evidence_cluster_ids=evidence_cluster_ids,
                    provenance=provenance,
                    weight=weight
                )
            
            logger.info(f"Created hypothesis edge: {event_id} -> {outcome_name} (Scenario: {scenario_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating hypothesis edge: {str(e)}")
            return False

    async def close(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")


# Singleton instance
neo4j_graph = None

def get_neo4j_graph() -> Neo4jKnowledgeGraph:
    """Get or create Neo4j graph instance"""
    global neo4j_graph
    if neo4j_graph is None:
        neo4j_graph = Neo4jKnowledgeGraph()
    return neo4j_graph

