# HyDE (Hypothetical Document Embeddings) Implementation Guide

## Overview

This guide provides a step-by-step implementation of HyDE (Hypothetical Document Embeddings) for the Korean Learning Chatbot system. HyDE is a retrieval augmentation technique that generates hypothetical documents to improve semantic search quality.

## Current System Analysis

### Existing Architecture
- **LLM Agents**: Multi-agent system using PydanticAI with GPT-4.1
- **Vector Database**: Qdrant for storing embeddings
- **Embedding Model**: OpenAI `text-embedding-3-small`
- **Search Strategy**: Hybrid search (dense + sparse) with RRF fusion
- **Collections**: 
  - `korean_grammar_v2`: Grammar entries
  - `howtostudykorean`: Educational documents

### Current Retrieval Flow
1. User query → Direct embedding
2. Hybrid search (dense + sparse vectors)
3. RRF fusion for result combination
4. Optional cross-encoder reranking

## HyDE Implementation Strategy

### Step 1: Create HyDE Module Structure

Create a new module for HyDE functionality:

```bash
mkdir src/hyde
touch src/hyde/__init__.py
touch src/hyde/hyde_generator.py
touch src/hyde/hyde_retriever.py
```

### Step 2: Implement HyDE Generator

**File**: `src/hyde/hyde_generator.py`

```python
"""
HyDE (Hypothetical Document Embeddings) generator for Korean learning chatbot.
"""

from typing import List, Optional
import logfire
from pydantic_ai import Agent
from openai import AsyncOpenAI

from src.config.settings import Config
from src.config.prompts import prompts

config = Config()

class HyDEGenerator:
    """Generates hypothetical documents for improved retrieval."""
    
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
        self.grammar_hyde_agent = self._create_grammar_hyde_agent()
        self.doc_hyde_agent = self._create_doc_hyde_agent()
    
    def _create_grammar_hyde_agent(self) -> Agent:
        """Create agent for generating hypothetical grammar entries."""
        return Agent(
            model="openai:gpt-4.1",
            instrument=True,
            output_type=str,
            instructions="""
            You are a Korean language expert. Generate a hypothetical Korean grammar entry 
            that would directly answer the user's question.
            
            Requirements:
            - Write in Russian (the system's interface language)
            - Include Korean grammar pattern in original form
            - Provide 1-2 usage examples in Korean with Russian translation
            - Keep it concise (exactly 512 characters)
            - Focus on the specific grammar point requested
            
            Format:
            Grammar: [Korean pattern] ([Russian name])
            Usage: [Korean example] - [Russian translation]
            """
        )
    
    def _create_doc_hyde_agent(self) -> Agent:
        """Create agent for generating hypothetical educational documents."""
        return Agent(
            model="openai:gpt-4.1",
            instrument=True,
            output_type=str,
            instructions="""
            You are a Korean language teacher. Generate a hypothetical educational document 
            that would contain the answer to the user's question.
            
            Requirements:
            - Write in Russian (the system's interface language)
            - Include relevant Korean examples and explanations
            - Structure as educational content
            - Keep it exactly 512 characters
            - Focus on teaching the concept clearly
            """
        )
    
    async def generate_grammar_hypothesis(self, query: str) -> str:
        """
        Generate hypothetical grammar entry for the query.
        
        Args:
            query: User's grammar-related question
            
        Returns:
            Hypothetical grammar entry text
        """
        with logfire.span(f"Generating grammar hypothesis for: {query}"):
            try:
                result = await self.grammar_hyde_agent.run(
                    user_prompt=f"Generate a hypothetical grammar entry for: {query}"
                )
                hypothesis = result.output
                
                # Ensure exactly 512 characters
                if len(hypothesis) > 512:
                    hypothesis = hypothesis[:509] + "..."
                elif len(hypothesis) < 512:
                    hypothesis = hypothesis.ljust(512)
                
                logfire.info(f"Generated grammar hypothesis: {hypothesis[:100]}...")
                return hypothesis
                
            except Exception as e:
                logfire.error(f"Error generating grammar hypothesis: {e}")
                # Fallback to original query
                return query.ljust(512)
    
    async def generate_doc_hypothesis(self, query: str) -> str:
        """
        Generate hypothetical educational document for the query.
        
        Args:
            query: User's learning-related question
            
        Returns:
            Hypothetical document text
        """
        with logfire.span(f"Generating doc hypothesis for: {query}"):
            try:
                result = await self.doc_hyde_agent.run(
                    user_prompt=f"Generate a hypothetical educational document for: {query}"
                )
                hypothesis = result.output
                
                # Ensure exactly 512 characters
                if len(hypothesis) > 512:
                    hypothesis = hypothesis[:509] + "..."
                elif len(hypothesis) < 512:
                    hypothesis = hypothesis.ljust(512)
                
                logfire.info(f"Generated doc hypothesis: {hypothesis[:100]}...")
                return hypothesis
                
            except Exception as e:
                logfire.error(f"Error generating doc hypothesis: {e}")
                # Fallback to original query
                return query.ljust(512)

    async def generate_multiple_hypotheses(
        self, 
        query: str, 
        num_hypotheses: int = 3,
        doc_type: str = "grammar"
    ) -> List[str]:
        """
        Generate multiple hypothetical documents for ensemble retrieval.
        
        Args:
            query: User's question
            num_hypotheses: Number of hypotheses to generate
            doc_type: Type of document ("grammar" or "educational")
            
        Returns:
            List of hypothetical document texts
        """
        hypotheses = []
        
        for i in range(num_hypotheses):
            if doc_type == "grammar":
                hypothesis = await self.generate_grammar_hypothesis(query)
            else:
                hypothesis = await self.generate_doc_hypothesis(query)
            
            hypotheses.append(hypothesis)
        
        return hypotheses
```

### Step 3: Implement HyDE Retriever

**File**: `src/hyde/hyde_retriever.py`

```python
"""
HyDE-enhanced retrieval functionality.
"""

from typing import List, Optional, Dict, Any
import asyncio
import logfire
from pydantic_ai import RunContext
from qdrant_client.http.models import Prefetch, SparseVector, FusionQuery, Fusion

from src.config.settings import Config
from src.schemas.schemas import GrammarEntryV2, RetrievedGrammar, RouterAgentDeps, RetrievedDoc
from src.hyde.hyde_generator import HyDEGenerator

config = Config()

class HyDERetriever:
    """Enhanced retriever using HyDE for improved semantic search."""
    
    def __init__(self, hyde_generator: HyDEGenerator):
        self.hyde_generator = hyde_generator
    
    async def retrieve_with_hyde_grammar(
        self,
        context: RunContext[RouterAgentDeps],
        search_query: str,
        retrieve_top_k: int = 15,
        use_multiple_hypotheses: bool = True,
        num_hypotheses: int = 3
    ) -> List[GrammarEntryV2] | None:
        """
        Retrieve grammar entries using HyDE enhancement.
        
        Args:
            context: Runtime context with dependencies
            search_query: Original user query
            retrieve_top_k: Number of results to retrieve
            use_multiple_hypotheses: Whether to use multiple hypotheses
            num_hypotheses: Number of hypotheses for ensemble retrieval
            
        Returns:
            List of retrieved grammar entries
        """
        with logfire.span(f"HyDE grammar retrieval for: {search_query}"):
            # Generate hypothetical document(s)
            if use_multiple_hypotheses:
                hypotheses = await self.hyde_generator.generate_multiple_hypotheses(
                    search_query, num_hypotheses, "grammar"
                )
            else:
                hypothesis = await self.hyde_generator.generate_grammar_hypothesis(search_query)
                hypotheses = [hypothesis]
            
            # Perform retrieval for each hypothesis
            all_results = []
            for i, hypothesis in enumerate(hypotheses):
                logfire.info(f"Retrieving with hypothesis {i+1}: {hypothesis[:100]}...")
                
                results = await self._perform_hybrid_search(
                    context, hypothesis, retrieve_top_k, config.qdrant_collection_name_v2
                )
                if results:
                    # Add hypothesis source info
                    for result in results:
                        result.hypothesis_source = i
                    all_results.extend(results)
            
            if not all_results:
                logfire.info("No results found with HyDE. Falling back to original query.")
                return await self._perform_hybrid_search(
                    context, search_query, retrieve_top_k, config.qdrant_collection_name_v2
                )
            
            # Deduplicate and merge results
            unique_results = self._deduplicate_results(all_results)
            
            # Convert to expected format
            grammar_results = []
            for result in unique_results[:retrieve_top_k]:
                grammar_results.append(
                    GrammarEntryV2(**result.payload) if hasattr(result, 'payload') 
                    else result.content
                )
            
            logfire.info(f"HyDE retrieval returned {len(grammar_results)} results")
            return grammar_results
    
    async def retrieve_with_hyde_docs(
        self,
        context: RunContext[RouterAgentDeps],
        search_query: str,
        retrieve_top_k: int = 15,
        rerank_top_k: int = 10,
        use_multiple_hypotheses: bool = True,
        num_hypotheses: int = 3
    ) -> List[Dict[str, Any]] | None:
        """
        Retrieve educational documents using HyDE enhancement.
        
        Args:
            context: Runtime context with dependencies
            search_query: Original user query
            retrieve_top_k: Number of results to retrieve
            rerank_top_k: Number of results after reranking
            use_multiple_hypotheses: Whether to use multiple hypotheses
            num_hypotheses: Number of hypotheses for ensemble retrieval
            
        Returns:
            List of retrieved document contents
        """
        with logfire.span(f"HyDE doc retrieval for: {search_query}"):
            # Generate hypothetical document(s)
            if use_multiple_hypotheses:
                hypotheses = await self.hyde_generator.generate_multiple_hypotheses(
                    search_query, num_hypotheses, "educational"
                )
            else:
                hypothesis = await self.hyde_generator.generate_doc_hypothesis(search_query)
                hypotheses = [hypothesis]
            
            # Perform retrieval for each hypothesis
            all_results = []
            for i, hypothesis in enumerate(hypotheses):
                logfire.info(f"Retrieving docs with hypothesis {i+1}: {hypothesis[:100]}...")
                
                results = await self._perform_hybrid_search(
                    context, hypothesis, retrieve_top_k, config.qdrant_collection_name_rag
                )
                if results:
                    # Add hypothesis source info
                    for result in results:
                        result.hypothesis_source = i
                    all_results.extend(results)
            
            if not all_results:
                logfire.info("No results found with HyDE. Falling back to original query.")
                return await self._perform_hybrid_search(
                    context, search_query, retrieve_top_k, config.qdrant_collection_name_rag
                )
            
            # Deduplicate and merge results
            unique_results = self._deduplicate_results(all_results)
            
            # Convert to RetrievedDoc format for reranking
            docs = [
                RetrievedDoc(
                    id=str(result.id),
                    content=result.payload,
                    score=result.score,
                )
                for result in unique_results
            ]
            
            # Perform reranking with original query (not hypothesis)
            if len(docs) > 1:
                docs = await self._rerank_documents(context, search_query, docs)
            
            # Return top results
            result_contents = [doc.content for doc in docs[:rerank_top_k]]
            logfire.info(f"HyDE doc retrieval returned {len(result_contents)} results")
            return result_contents
    
    async def _perform_hybrid_search(
        self,
        context: RunContext[RouterAgentDeps],
        query: str,
        retrieve_top_k: int,
        collection_name: str
    ) -> List[Any]:
        """Perform hybrid search with dense and sparse vectors."""
        # Create embeddings
        vector_query = await context.deps.openai_client.embeddings.create(
            model=config.embedding_model, input=query
        )
        sparse_vector_query = next(context.deps.sparse_embedding.query_embed(query))
        sparse_vector_query = SparseVector(**sparse_vector_query.as_object())
        
        vector_query = vector_query.data[0].embedding
        
        # Set up prefetches
        bm_25_prefetch = Prefetch(
            query=sparse_vector_query,
            using=config.sparse_embedding_model,
            limit=retrieve_top_k,
            score_threshold=0,
        )
        
        dense_prefetch = Prefetch(
            query=vector_query,
            using=config.embedding_model,
            limit=retrieve_top_k,
            score_threshold=0,
        )
        
        # Perform hybrid search
        hits = context.deps.qdrant_client.query_points(
            collection_name=collection_name,
            prefetch=[bm_25_prefetch, dense_prefetch],
            query=FusionQuery(fusion=Fusion.RRF),
            with_payload=True,
        ).points
        
        return hits
    
    def _deduplicate_results(self, results: List[Any]) -> List[Any]:
        """Remove duplicate results based on ID."""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            result_id = str(result.id)
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # Sort by score (higher is better)
        return sorted(unique_results, key=lambda x: x.score, reverse=True)
    
    async def _rerank_documents(
        self,
        context: RunContext[RouterAgentDeps],
        original_query: str,
        docs: List[RetrievedDoc]
    ) -> List[RetrievedDoc]:
        """Rerank documents using cross-encoder."""
        cross_input = []
        for doc in docs:
            doc_data = ". ".join([
                doc.content.get("topic", ""),
                doc.content.get("subtopic", ""),
                doc.content.get("content", "")
            ])
            cross_input.append([original_query, doc_data])
        
        scores = context.deps.reranking_model.predict(cross_input)
        
        # Add cross-encoder scores
        for idx, score in enumerate(scores):
            docs[idx].cross_score = float(score)
            logfire.info(f"Document {idx} reranking: {docs[idx].score:.4f} -> {score:.4f}")
        
        # Sort by cross-encoder score
        return sorted(docs, key=lambda x: x.cross_score or 0, reverse=True)
```

### Step 4: Update Agent Tools

**File**: `src/llm_agent/agent_tools.py` (Modify existing functions)

Add HyDE imports and modify existing retrieval functions:

```python
# Add to imports
from src.hyde.hyde_generator import HyDEGenerator
from src.hyde.hyde_retriever import HyDERetriever

# Add HyDE initialization (add after config setup)
_hyde_generator = None
_hyde_retriever = None

async def get_hyde_retriever(context: RunContext[RouterAgentDeps]) -> HyDERetriever:
    """Get or create HyDE retriever instance."""
    global _hyde_generator, _hyde_retriever
    
    if _hyde_retriever is None:
        _hyde_generator = HyDEGenerator(context.deps.openai_client)
        _hyde_retriever = HyDERetriever(_hyde_generator)
    
    return _hyde_retriever

# Modify existing retrieve_grammars_tool function
async def retrieve_grammars_tool(
    context: RunContext[RouterAgentDeps], 
    search_query: str, 
    retrieve_top_k: int = 15,
    use_hyde: bool = True
) -> list[GrammarEntryV2] | None:
    """
    Enhanced tool for extracting grammatical constructions with optional HyDE.
    
    Args:
        context: the call context
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        use_hyde: whether to use HyDE enhancement
    """
    if use_hyde:
        hyde_retriever = await get_hyde_retriever(context)
        return await hyde_retriever.retrieve_with_hyde_grammar(
            context, search_query, retrieve_top_k
        )
    else:
        # Original implementation (existing code)
        # ... keep existing implementation as fallback
        pass

# Modify existing retrieve_docs_tool function
async def retrieve_docs_tool(
    context: RunContext[RouterAgentDeps],
    search_query: str,
    retrieve_top_k: int = 15,
    rerank_top_k: int = 10,
    use_hyde: bool = True
) -> list[dict] | None:
    """
    Enhanced tool for extracting documents with optional HyDE.
    
    Args:
        context: the call context
        search_query: запрос для поиска
        retrieve_top_k: количество RETRIEVED результатов
        rerank_top_k: количество результатов ПОСЛЕ reranking-а
        use_hyde: whether to use HyDE enhancement
    """
    if use_hyde:
        hyde_retriever = await get_hyde_retriever(context)
        return await hyde_retriever.retrieve_with_hyde_docs(
            context, search_query, retrieve_top_k, rerank_top_k
        )
    else:
        # Original implementation (existing code)
        # ... keep existing implementation as fallback
        pass
```

### Step 5: Update Agent Instructions

**File**: `src/llm_agent/agent.py` (Modify thinking_grammar_agent)

Update the thinking agent to work better with HyDE:

```python
# Modify thinking_grammar_agent instructions
thinking_grammar_agent = Agent(
    model="openai:gpt-4.1",
    instrument=True,
    output_type=str,
    instructions="""
        You are a Korean language expert assistant with access to enhanced retrieval capabilities.
        
        1. Processing the user's query:
        - Analyze the user's Korean language question thoroughly
        - The system will automatically generate hypothetical documents that would answer this question
        - These hypothetical documents improve the quality of information retrieval
        
        2. Use the enhanced `docs_search` tool:
        - The tool now uses HyDE (Hypothetical Document Embeddings) for better retrieval
        - It automatically generates relevant hypothetical content and retrieves similar real documents
        - If no suitable documents are found, try rephrasing the search query and use `docs_search` again
        
        3. Formulate a comprehensive answer:
        - Integrate the retrieved information into your explanation
        - Don't just output the search results - synthesize them into a coherent response
        - Provide practical examples and clear explanations in Russian
        
        If suitable documents cannot be found even after improving the search query, answer the user's question using your own knowledge.
    """
)
```

### Step 6: Configuration Updates

**File**: `src/config/settings.py` (Add HyDE-specific settings)

```python
# Add to Config class
class Config(BaseSettings):
    # ... existing settings ...
    
    # HyDE-specific settings
    use_hyde: bool = True
    hyde_num_hypotheses: int = 3
    hyde_hypothesis_length: int = 512
    hyde_use_multiple_hypotheses: bool = True
    
    # Model settings for HyDE generation
    hyde_model: str = "openai:gpt-4.1"
```

### Step 7: Add Schema Updates

**File**: `src/schemas/schemas.py` (Add HyDE-related schemas)

```python
# Add new schemas for HyDE
class HyDEConfig(BaseModel):
    """Configuration for HyDE retrieval."""
    use_hyde: bool = True
    num_hypotheses: int = 3
    hypothesis_length: int = 512
    use_multiple_hypotheses: bool = True

class EnhancedRetrievedGrammar(RetrievedGrammar):
    """Extended retrieved grammar with HyDE information."""
    hypothesis_source: Optional[int] = None
    hyde_score: Optional[float] = None

class EnhancedRetrievedDoc(RetrievedDoc):
    """Extended retrieved document with HyDE information."""
    hypothesis_source: Optional[int] = None
    hyde_score: Optional[float] = None
```

### Step 8: Testing and Validation

Create test files to validate HyDE implementation:

**File**: `tests/test_hyde.py`

```python
"""
Tests for HyDE implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.hyde.hyde_generator import HyDEGenerator
from src.hyde.hyde_retriever import HyDERetriever

@pytest.fixture
def mock_openai_client():
    client = Mock()
    client.embeddings.create = AsyncMock()
    return client

@pytest.fixture
def hyde_generator(mock_openai_client):
    return HyDEGenerator(mock_openai_client)

@pytest.fixture  
def hyde_retriever(hyde_generator):
    return HyDERetriever(hyde_generator)

@pytest.mark.asyncio
async def test_grammar_hypothesis_generation(hyde_generator):
    """Test grammar hypothesis generation."""
    query = "как использовать грамматику 고 싶다?"
    
    hypothesis = await hyde_generator.generate_grammar_hypothesis(query)
    
    assert isinstance(hypothesis, str)
    assert len(hypothesis) == 512
    assert "고 싶다" in hypothesis or "хотеть" in hypothesis.lower()

@pytest.mark.asyncio
async def test_multiple_hypotheses_generation(hyde_generator):
    """Test multiple hypotheses generation."""
    query = "объясните будущее время в корейском"
    
    hypotheses = await hyde_generator.generate_multiple_hypotheses(
        query, num_hypotheses=3, doc_type="grammar"
    )
    
    assert len(hypotheses) == 3
    assert all(len(h) == 512 for h in hypotheses)
    assert all(isinstance(h, str) for h in hypotheses)

@pytest.mark.asyncio
async def test_doc_hypothesis_generation(hyde_generator):
    """Test document hypothesis generation."""
    query = "как изучать корейские частицы?"
    
    hypothesis = await hyde_generator.generate_doc_hypothesis(query)
    
    assert isinstance(hypothesis, str)
    assert len(hypothesis) == 512
```

### Step 9: Performance Monitoring

Add monitoring for HyDE performance:

**File**: `src/hyde/monitoring.py`

```python
"""
Monitoring and metrics for HyDE performance.
"""

import time
import logfire
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class HyDEMetrics:
    """Metrics for HyDE retrieval performance."""
    hypothesis_generation_time: float = 0.0
    retrieval_time: float = 0.0
    total_time: float = 0.0
    num_hypotheses: int = 0
    results_found: int = 0
    fallback_used: bool = False
    query_complexity: str = "simple"  # simple, medium, complex
    
class HyDEMonitor:
    """Monitor HyDE performance and quality."""
    
    def __init__(self):
        self.metrics_history: List[HyDEMetrics] = []
    
    def start_hypothesis_timer(self) -> float:
        """Start timing hypothesis generation."""
        return time.time()
    
    def end_hypothesis_timer(self, start_time: float) -> float:
        """End timing and return duration."""
        return time.time() - start_time
    
    def log_retrieval_metrics(self, metrics: HyDEMetrics):
        """Log retrieval metrics."""
        self.metrics_history.append(metrics)
        
        logfire.info(
            "HyDE Retrieval Metrics",
            hypothesis_time=metrics.hypothesis_generation_time,
            retrieval_time=metrics.retrieval_time,
            total_time=metrics.total_time,
            num_hypotheses=metrics.num_hypotheses,
            results_found=metrics.results_found,
            fallback_used=metrics.fallback_used,
            query_complexity=metrics.query_complexity
        )
    
    def get_average_metrics(self, last_n: int = 100) -> Dict[str, float]:
        """Get average metrics for last N retrievals."""
        recent_metrics = self.metrics_history[-last_n:]
        
        if not recent_metrics:
            return {}
        
        return {
            "avg_hypothesis_time": sum(m.hypothesis_generation_time for m in recent_metrics) / len(recent_metrics),
            "avg_retrieval_time": sum(m.retrieval_time for m in recent_metrics) / len(recent_metrics),
            "avg_total_time": sum(m.total_time for m in recent_metrics) / len(recent_metrics),
            "avg_results_found": sum(m.results_found for m in recent_metrics) / len(recent_metrics),
            "fallback_rate": sum(1 for m in recent_metrics if m.fallback_used) / len(recent_metrics)
        }
```

### Step 10: Gradual Rollout Strategy

**Phase 1: Development Testing**
1. Implement basic HyDE functionality
2. Test with sample queries  
3. Compare results with baseline system
4. Tune hypothesis generation prompts

**Phase 2: A/B Testing**
1. Add feature flag for HyDE (`use_hyde` parameter)
2. Route 50% of queries through HyDE
3. Monitor performance metrics
4. Collect user feedback on answer quality

**Phase 3: Full Deployment**
1. Set HyDE as default if metrics show improvement
2. Keep fallback to original retrieval as backup
3. Monitor system performance and costs
4. Fine-tune based on production data

## Usage Examples

### Basic Grammar Query with HyDE
```python
# In agent_tools.py
async def grammar_search(context: RunContext[RouterAgentDeps], search_query: str):
    # HyDE will automatically generate hypothetical grammar entries
    # and retrieve similar real entries from the database
    docs = await retrieve_grammars_tool(context, search_query, use_hyde=True)
    return docs
```

### Complex Learning Question with HyDE
```python
# In agent.py - thinking_grammar_agent tool
async def docs_search(context: RunContext[RouterAgentDeps], search_query: str):  
    # HyDE will generate hypothetical educational content
    # and find real documents that match the learning needs
    docs = await retrieve_docs_tool(context, search_query, use_hyde=True)
    return docs
```

## Benefits of HyDE Implementation

1. **Improved Semantic Matching**: Hypothetical documents bridge the gap between user queries and stored content
2. **Better Handling of Complex Queries**: Multi-hypothesis approach captures different aspects of complex questions  
3. **Maintained Performance**: Fallback to original system ensures reliability
4. **Configurable**: Easy to tune and disable if needed
5. **Monitoring**: Built-in metrics to track performance improvements

## Considerations

1. **Increased Latency**: HyDE adds hypothesis generation time (~200-500ms per hypothesis)
2. **Higher Costs**: Additional LLM calls for hypothesis generation
3. **Complexity**: More complex debugging and error handling
4. **Tuning Required**: Hypothesis prompts need optimization for Korean language learning domain

## Monitoring Success

Key metrics to track:
- **Relevance**: User satisfaction with retrieved results
- **Latency**: Total response time including hypothesis generation
- **Cost**: Additional token usage for hypothesis generation  
- **Fallback Rate**: How often the system falls back to original retrieval
- **Coverage**: Percentage of queries that benefit from HyDE

This implementation provides a comprehensive HyDE system that enhances the existing Korean learning chatbot's retrieval capabilities while maintaining backward compatibility and performance monitoring.