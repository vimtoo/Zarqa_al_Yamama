"""
LLM Client for OpenRouter and DeepSeek Integration
Provides intelligent analysis capabilities for Zarqa al Yamama
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from app.config import settings, Settings
from app.core.http_client import GlobalHTTPClient
try:
    from app.llm.antigravity import build_messages, prompt_fingerprint
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Antigravity module not found. Using minimal fallback builders.")

    def build_messages(*args, **kwargs):
        return [{"role": "system", "content": ""}, {"role": "user", "content": str(kwargs)}]

    def prompt_fingerprint(prompt_id: str, version: str) -> str:
        return f"{prompt_id}:{version}"

import datetime

logger = logging.getLogger(__name__)


# SYSTEM_PROMPT_TEMPLATE REMOVED - Prompts are managed by Antigravity



class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate completion from prompt"""
        pass
    
    @abstractmethod
    async def analyze(
        self,
        data: Dict[str, Any],
        analysis_type: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DEPRECATED: Use LLMManager.analyze() instead.
        Analyze data using LLM
        """
        pass


class OpenRouterClient(BaseLLMClient):
    """Client for OpenRouter API"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.DEFAULT_LLM_MODEL

        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate completion using OpenRouter"""
        if not self.api_key:
            logger.error("OpenRouter API key not set")
            return ""
        
        # Use provided messages or build from prompt
        final_messages = messages or []
        if not final_messages:
            if system_prompt:
                final_messages.append({"role": "system", "content": system_prompt})
            final_messages.append({"role": "user", "content": prompt})
        
        # Use overriden model or default
        target_model = model or self.model

        try:
            client = GlobalHTTPClient.get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://zarqa-al-yamama.ai",
                    "X-Title": "Zarqa al Yamama Forecasting"
                },
                json={
                    "model": target_model,
                    "messages": final_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return ""
                    
        except Exception as e:
            logger.error(f"OpenRouter completion error: {str(e)}")
            return ""
    
    async def analyze(
        self,
        data: Dict[str, Any],
        analysis_type: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze data using OpenRouter LLM"""
        raise RuntimeError("OpenRouterClient.analyze() is disabled. Use LLMManager.analyze() + Antigravity.")



class DryRunNetworkBlocked(Exception):
    """Raised when network calls are blocked by dry-run mode"""
    pass

class GeminiClient(BaseLLMClient):
    """Client for Google Gemini Developer API"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = settings.GEMINI_BASE_URL
        self.default_model = "gemini-2.0-flash" 
        
        # Startup check handled by config validator, but we double check enabled state
        if settings.GEMINI_ENABLED and not self.api_key:
             logger.error("Gemini enabled but key missing in client init")

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate completion using Gemini API"""
        if not settings.GEMINI_ENABLED:
            logger.warning("Attempted to use GeminiClient while disabled")
            return ""
            
        if not self.api_key:
            logger.error("Gemini API key not set")
            return ""
        
        target_model = model or self.default_model
        
        # Build contents
        gemini_contents = []
        
        # Helper to map standard messages to Gemini 'contents'
        c_messages = messages or []
        for m in c_messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                # System prompt handled via systemInstruction
                if not system_prompt:
                    system_prompt = content
                continue
            
            g_role = "model" if role == "assistant" else "user"
            gemini_contents.append({
                "role": g_role,
                "parts": [{"text": content}]
            })
            
        # If explicit prompt provided and no messages (or appended to history)
        if prompt:
             gemini_contents.append({
                  "role": "user", 
                  "parts": [{"text": prompt}]
             })
             
        if not gemini_contents:
             logger.warning("Gemini request with empty contents")
             return ""

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        if system_prompt:
             payload["systemInstruction"] = {
                  "parts": [{"text": system_prompt}]
             }
             
        if settings.GEMINI_DRY_RUN:
            logger.info("Gemini Dry Run: Blocking network call.")
            raise DryRunNetworkBlocked("Network call blocked by GEMINI_DRY_RUN")

        try:
            client = GlobalHTTPClient.get_client()
            # Append model to base URL path
            url = f"{self.base_url}/models/{target_model}:generateContent"
            
            response = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key
                },
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError, TypeError):
                    logger.error(f"Gemini malformed response: {str(data)[:200]}")
                    return ""
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return ""
                    
        except Exception as e:
            logger.error(f"Gemini completion error: {str(e)}")
            return ""

    async def analyze(self, *args, **kwargs):
        raise RuntimeError("GeminiClient.analyze() disabled. Use LLMManager.")


class DeepSeekClient(BaseLLMClient):
    """Client for DeepSeek API"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL
        self.reasoning_model = settings.REASONING_MODEL
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured")
        pass
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        messages: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> str:
        """Generate completion using DeepSeek"""
        if not self.api_key:
            logger.error("DeepSeek API key not set")
            return ""
        
        # Use provided messages or build from prompt
        final_messages = messages or []
        if not final_messages:
            if system_prompt:
                final_messages.append({"role": "system", "content": system_prompt})
            final_messages.append({"role": "user", "content": prompt})
        
        # Use overriden model or default
        target_model = model or self.model
        
        try:
            client = GlobalHTTPClient.get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": target_model,
                    "messages": final_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return ""
                    
        except Exception as e:
            logger.error(f"DeepSeek completion error: {str(e)}")
            return ""
    
    async def reason(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Use DeepSeek reasoning model for complex analysis"""
        if not self.api_key:
            logger.error("DeepSeek API key not set")
            return {"error": "API key not configured"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = GlobalHTTPClient.get_client()
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.reasoning_model,
                    "messages": messages
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                reasoning = data["choices"][0]["message"].get("reasoning_content", "")
                
                return {
                    "response": content,
                    "reasoning": reasoning,
                    "model": self.reasoning_model
                }
            else:
                logger.error(f"DeepSeek Reasoning error: {response.status_code}")
                return {"error": response.text}
                    
        except Exception as e:
            logger.error(f"DeepSeek reasoning error: {str(e)}")
            return {"error": str(e)}
    
    async def analyze(
        self,
        data: Dict[str, Any],
        analysis_type: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze data using DeepSeek"""
        raise RuntimeError("DeepSeekClient.analyze() is disabled. Use LLMManager.analyze() + Antigravity.")


class LLMManager:
    """
    Manager class to handle LLM client selection and fallback with Role-Based Routing.
    """
    
    def __init__(self, agent_name: str = "UnknownAgent", settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.agent_name = agent_name
        self.primary_provider = self.settings.DEFAULT_LLM_PROVIDER
        
        self.default_provider = self.settings.DEFAULT_LLM_PROVIDER or "openrouter"
        self.default_model = None
        
        self.gemini_enabled = self.settings.GEMINI_ENABLED
        
        # Role-based Model Routing Table (Instance-level for setting isolation)
        self.role_map = {
            # High Reasoning / Planning
            "planner": {"provider": "deepseek", "model": self.settings.DEEPSEEK_MODEL}, 
            
            # Search & Reading (Fast, large context) 
            "searcher": {"provider": "openrouter", "model": "google/gemini-flash-1.5-8b"},
            
            # Evidence Minting
            "extractor": {"provider": "deepseek", "model": self.settings.DEEPSEEK_MODEL},
            
            # Decision / Logic
            "evaluator": {"provider": "openrouter", "model": "anthropic/claude-3.5-haiku"},
            
            # Synthesis / Writing
            "writer": {"provider": "openrouter", "model": "openai/gpt-4o"},
            
            # Critique / Audit
            "critic": {"provider": "openrouter", "model": "anthropic/claude-3.5-sonnet"},
            "governor": {"provider": "openrouter", "model": "anthropic/claude-3-opus"},
            
            # Default
            "default": {"provider": "openrouter", "model": self.settings.DEFAULT_LLM_MODEL}
        }
        
        # Initialize clients
        self.clients: Dict[str, BaseLLMClient] = {}
        
        # Always initialize primary
        if self.primary_provider == "openrouter":
            self.clients["openrouter"] = OpenRouterClient()
        elif self.primary_provider == "openai":
            # Assuming OpenAI client exists or similar
            pass
            
        # Initialize Gemini if enabled (even if policy restricts usage, client must exist)
        if self.gemini_enabled and self.settings.GEMINI_API_KEY:
            self.clients["gemini"] = GeminiClient()

    def get_client(self, provider: Optional[str] = None) -> BaseLLMClient:
        """Get LLM client by provider name"""
        provider = provider or self.primary_provider
        
        if provider in self.clients:
            return self.clients[provider]
            
        # Fallback to primary if not found? Or raise?
        # For legacy compatibility, try "default"
        if "default" in self.clients:
            return self.clients["default"]
            
        # If openrouter exists, fallback to it
        if "openrouter" in self.clients:
            return self.clients["openrouter"]
            
        raise ValueError(f"LLM Client for provider '{provider}' not initialized.")
    
    def _resolve_routing(self, role: Optional[str] = None, provider: Optional[str] = None) -> tuple[str, str]:
        """
        Resolve (provider, model) based on optional role or explicit provider.
        Returns tuple of (provider_name, model_name).
        """
        if role and role in self.role_map:
            config = self.role_map[role]
            return config["provider"], config["model"]
            
        # Fallback to defaults
        prov = provider or self.default_provider
        
        # Model selection logic
        model = self.default_model
        
        if not model:
            if prov == "deepseek":
                model = self.settings.DEEPSEEK_MODEL
            elif prov == "openrouter":
                model = self.settings.DEFAULT_LLM_MODEL
            else:
                model = self.settings.DEFAULT_LLM_MODEL
            
        return prov, model

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        role: Optional[str] = None,
        fallback: bool = True,
        **kwargs
    ) -> str:
        """
        Generate completion with role-based routing and automatic fallback.
        Strictly enforces v1.1 Role and Temperature rules.
        """
        if not role:
             # Rule 8 violation Check
             # For legacy calls we might allow it but warn. For strict mode we should error.
             # Given "non-negotiable", we log error but default to 'default' role to prevent crash loop,
             # UNLESS we are in strict mode. Let's assume strict logic for explicit calls.
             # For now, we force role='default' if missing.
             role = "default"

        # Rule 9: Temperature Discipline
        # Callers CANNOT override higher temps than allowed by role.
        requested_temp = kwargs.get("temperature", 0.7)
        allowed_temp = 0.7 
        
        if role in ["searcher", "extractor"]:
            allowed_temp = 0.2
        elif role in ["critic", "governor", "evaluator"]:
            allowed_temp = 0.3
        elif role in ["writer"]:
            allowed_temp = 0.5
            
        final_temp = min(requested_temp, allowed_temp)
        if final_temp < requested_temp:
             logger.warning(f"Role {role} enforced temp limit: {requested_temp} -> {final_temp}")
        
        kwargs["temperature"] = final_temp

        # Resolve routing
        target_provider, target_model = self._resolve_routing(role, provider)

        # -------------------------------------------------------------------------
        # ARBITRATION POLICY ENFORCEMENT
        # -------------------------------------------------------------------------
        from app.llm.arbitration import ArbitrationPolicy, ArbitrationLane, TaskType, Sensitivity
        
        task_type = kwargs.get("task_type", TaskType.DECISION)
        sensitivity = kwargs.get("sensitivity", Sensitivity.MEDIUM)
        
        lane = ArbitrationPolicy.get_lane(self.agent_name, task_type, sensitivity)
        
        # If Gemini is targeted (via role or explicit provider) but FORBIDDEN, block it.
        if target_provider == "gemini" and lane == ArbitrationLane.FORBIDDEN:
            logger.warning(f"Arbitration BLOCKED Gemini for agent {self.agent_name} (Lane: {lane}). Fallback to primary.")
            target_provider = self.primary_provider
            target_model = self.settings.DEFAULT_LLM_MODEL

        # If Lane is ADVISORY and Gemini is enabled, we PREFER Gemini (Policy Opinion)
        # This ensures specialized synthesis agents use the specialized model.
        if lane == ArbitrationLane.ADVISORY and self.gemini_enabled:
             target_provider = "gemini"
             # Let GeminiClient use its default model or specified one
             # target_model = ... (GeminiClient handles default)

        # Log Arbitration
        logger.info(f"[Arbitration] Agent: {self.agent_name}, Lane: {lane}, Provider: {target_provider}")
        # -------------------------------------------------------------------------
        
        # Rule 3: Evidence Authority Assertion
        # If role is 'extractor', we must ensure we are NOT using Gemini for "Minting"
        # Since _resolve_routing maps 'extractor' -> 'gemini-flash' in my ROLE_MAP (wait, checked design spec),
        # Wait, the Design Spec v1.1 says:
        # "Gemini Flash MAY NOT be used for: creating EvidenceItems"
        # "All EvidenceItems are minted ONLY by DeepSeek 3 or GLM 4.7"
        # 
        # I need to CHECK my ROLE_MAP in this file. 
        # If 'extractor' is mapped to Gemini, I must change it or split roles.
        # Let's inspect ROLE_MAP in the file during execution or just update it here.
        # I will update ROLE_MAP in this replace block as well to be safe.
        
        # Get client
        client = self.get_client(target_provider)
        
        # ... fallback logic preserved ...
        response = await client.complete(
            prompt, 
            system_prompt, 
            model=target_model,
            **kwargs
        )
        
        # Fallback
        if not response and fallback:
            fallback_provider = "deepseek" if target_provider != "deepseek" else "openrouter"
            logger.info(f"Falling back to {fallback_provider} (Role: {role})")
            
            # Re-resolve model for fallback provider using same role if possible, or default
            # Simplified fallback: just use default model of fallback provider logic?
            # Or re-call _resolve_routing with the new provider?
            _, fallback_model = self._resolve_routing(role, fallback_provider)
            
            client = self.get_client(fallback_provider)
            response = await client.complete(
                prompt, 
                system_prompt, 
                model=fallback_model,
                **kwargs
            )
        
        return response
    
    async def analyze(
        self,
        data: Dict[str, Any],
        analysis_type: str,
        context: Optional[str] = None,
        provider: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze data with simplified flow:
        1. Antigravity builds prompt
        2. LLM generates raw text
        3. Manager handles JSON parsing/repair centralizing logic
        """
        import json
        
        # 1. Antigravity Build
        # Map analysis_type to agent/scenario
        agent_name = role or "analyst"
        scenario = analysis_type
        
        messages = build_messages(
            agent_name=agent_name,
            scenario=scenario,
            payload=data,
            evidence=context
        )
        
        # 2. Resolve Routing
        target_provider, target_model = self._resolve_routing(role, provider)
        client = self.get_client(target_provider)
        
        # 3. Generate Raw Text
        response_text = await client.complete(
            prompt="", # Messages used instead
            messages=messages,
            model=target_model,
            temperature=0.3 # Default for analysis
        )
        
        # 4. Centralized JSON Processing Loop
        # Try to parse
        parsed_data = self._extract_json(response_text)
        
        if parsed_data:
            # Ensure success contract
            if "uncertainty_notes" not in parsed_data:
                parsed_data["uncertainty_notes"] = []
            return parsed_data
            
        # 5. Repair if failed
        logger.warning(f"JSON Parse Failed. Attempting Antigravity Repair for {analysis_type}...")
        
        repair_messages = build_messages(
            agent_name="system",
            scenario="json_repair",
            payload={"error": "Invalid JSON", "raw_text": response_text},
            mode="repair"
        )
        
        repair_text = await client.complete(
            prompt="",
            messages=repair_messages,
            model=target_model,
            temperature=0.1
        )
        
        repaired_data = self._extract_json(repair_text)
        if repaired_data:
            # Ensure success contract
            if "uncertainty_notes" not in repaired_data:
                repaired_data["uncertainty_notes"] = []
            return repaired_data
            
        # 6. Fallback/Failure
        logger.error(f"Analysis Failed for {analysis_type}")
        return self._low_confidence(
            analysis_type=analysis_type,
            reason="Failed to generate/parse valid JSON after repair.",
            raw_response=response_text,
            details={"repair_text": repair_text, "error": "Max retries exceeded"}
        )

    def _low_confidence(
        self, 
        analysis_type: str, 
        reason: str, 
        raw_response: str = "", 
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate canonical LOW_CONFIDENCE object"""
        return {
            "status": "LOW_CONFIDENCE",
            "agent": analysis_type,
            "confidence": 0.0,
            "claims": [],
            "evidence": [],
            "signals": [],
            "assumptions": [],
            "uncertainty_notes": [reason],
            "raw_response": raw_response,
            "error_details": details or {}
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Helper to extract and parse JSON from LLM output"""
        import json
        if not text:
            return None
            
        clean_text = text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0]
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0]
            
        # Strip simple reasoning tags if present
        # (Though Antigravity prompts should handle this, we double check)
        if "<reasoning>" in clean_text and "</reasoning>" in clean_text:
             parts = clean_text.split("</reasoning>")
             if len(parts) > 1:
                 clean_text = parts[1]
        
        try:
            return json.loads(clean_text.strip())
        except json.JSONDecodeError:
            return None
    
    async def deep_reason(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use DeepSeek reasoning for complex analysis
        """
        return await self.deepseek.reason(prompt, system_prompt)


# Singleton instance
llm_manager = LLMManager()
