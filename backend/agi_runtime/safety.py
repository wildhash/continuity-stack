"""
Safety Module
Implements safety gates, tool allowlisting, and tripwires
"""
import re
import logging
from typing import List, Dict, Any, Set
from .types import SafetyAssessment, ToolStatus, PlanStep

logger = logging.getLogger(__name__)


# Tool categories
SAFE_TOOLS = {
    "read_file", "list_files", "search_text", "validate_json",
    "parse_data", "format_text", "compute_hash", "analyze_data"
}

RISKY_TOOLS = {
    "write_file", "delete_file", "execute_command", "network_request",
    "modify_database", "send_email", "call_api"
}

BLOCKED_TOOLS = {
    "execute_arbitrary_code", "access_secrets", "modify_system",
    "disable_safety", "bypass_sandbox"
}


# Injection patterns to detect
INJECTION_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # XSS
    r"javascript:",  # JavaScript protocol
    r"on\w+\s*=",  # Event handlers
    r"eval\s*\(",  # eval() calls
    r"exec\s*\(",  # exec() calls
    r"__import__\s*\(",  # Python imports
    r"system\s*\(",  # System calls
    r"\$\(.*?\)",  # Command substitution
    r"`.*?`",  # Backtick execution
    r";\s*(rm|del|DROP|DELETE)\s+",  # Dangerous commands
]

# Secret patterns to detect
SECRET_PATTERNS = [
    r"api[_-]?key",
    r"secret",
    r"password",
    r"token",
    r"credential",
    r"private[_-]?key",
]


class SafetyGate:
    """
    Safety gate that evaluates plans and actions before execution
    """
    
    def __init__(self, environment: str = "production", risky_confidence_threshold: float = 0.7):
        """
        Args:
            environment: "production", "staging", or "development"
            risky_confidence_threshold: Minimum confidence required for risky tools (default: 0.7)
        """
        self.environment = environment
        self.risky_confidence_threshold = risky_confidence_threshold
        self.injection_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self.secret_patterns = [re.compile(p, re.IGNORECASE) for p in SECRET_PATTERNS]
    
    def _get_allowed_tools(self) -> Set[str]:
        """Get allowed tools based on environment"""
        if self.environment == "development":
            return SAFE_TOOLS | RISKY_TOOLS
        elif self.environment == "staging":
            return SAFE_TOOLS | {"write_file", "network_request"}
        else:  # production
            return SAFE_TOOLS
    
    def _check_injection(self, text: str) -> List[str]:
        """Check for injection patterns in text"""
        violations = []
        for pattern in self.injection_patterns:
            if pattern.search(text):
                violations.append(f"Injection pattern detected: {pattern.pattern}")
        return violations
    
    def _check_secrets(self, data: Any) -> List[str]:
        """Check if data contains secret-like patterns"""
        violations = []
        text = str(data).lower()
        
        for pattern in self.secret_patterns:
            if pattern.search(text):
                violations.append(f"Potential secret detected: {pattern.pattern}")
        
        return violations
    
    def assess_plan(self, plan: List[PlanStep], confidence: float = 0.5) -> SafetyAssessment:
        """
        Assess safety of a plan before execution
        Returns SafetyAssessment with allowed/blocked status
        """
        allowed_tools = self._get_allowed_tools()
        blocked_tools_found = []
        reasons = []
        risk_flags = []
        sandbox_required = False
        
        for step in plan:
            tool = step.tool
            
            # Check if tool is blocked
            if tool in BLOCKED_TOOLS:
                blocked_tools_found.append(tool)
                reasons.append(f"Tool '{tool}' is in blocked list")
                continue
            
            # Check if tool is unknown
            if tool not in (SAFE_TOOLS | RISKY_TOOLS):
                blocked_tools_found.append(tool)
                reasons.append(f"Unknown tool '{tool}' - not in allowlist")
                continue
            
            # Check if tool is allowed in this environment
            if tool not in allowed_tools:
                blocked_tools_found.append(tool)
                reasons.append(f"Tool '{tool}' not allowed in {self.environment} environment")
                continue
            
            # Check for injection in args
            injection_violations = self._check_injection(str(step.args))
            if injection_violations:
                blocked_tools_found.append(tool)
                reasons.extend(injection_violations)
                risk_flags.append("injection_detected")
                continue
            
            # Check for secrets in args
            secret_violations = self._check_secrets(step.args)
            if secret_violations:
                blocked_tools_found.append(tool)
                reasons.extend(secret_violations)
                risk_flags.append("secret_detected")
                continue
            
            # Check if risky tool with low confidence
            if tool in RISKY_TOOLS and confidence < self.risky_confidence_threshold:
                sandbox_required = True
                reasons.append(f"Risky tool '{tool}' requires sandbox rehearsal (confidence {confidence:.2f} < {self.risky_confidence_threshold})")
        
        # Determine overall status
        if blocked_tools_found:
            status = ToolStatus.BLOCKED
        elif sandbox_required:
            status = ToolStatus.SANDBOXED
        else:
            status = ToolStatus.ALLOWED
        
        return SafetyAssessment(
            status=status,
            allowed_tools=list(allowed_tools),
            blocked_tools=blocked_tools_found,
            reasons=reasons,
            risk_flags=risk_flags,
            sandbox_required=sandbox_required
        )
    
    def assess_tool_output(self, output: Any) -> List[str]:
        """
        Check tool output for safety violations
        Returns list of violation messages (empty if safe)
        """
        violations = []
        
        # Check for injection patterns in output
        injection_violations = self._check_injection(str(output))
        violations.extend(injection_violations)
        
        # Check for secrets in output
        secret_violations = self._check_secrets(output)
        violations.extend(secret_violations)
        
        if violations:
            logger.warning(f"Safety violations in tool output: {violations}")
        
        return violations
    
    def redact_secrets(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact potential secrets from data
        Returns redacted copy
        """
        redacted = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key looks like a secret
            is_secret = any(pattern.search(key_lower) for pattern in self.secret_patterns)
            
            if is_secret:
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self.redact_secrets(value)
            elif isinstance(value, list):
                redacted[key] = [self.redact_secrets(item) if isinstance(item, dict) else item for item in value]
            else:
                redacted[key] = value
        
        return redacted


def create_sandbox_rehearsal(step: PlanStep) -> Dict[str, Any]:
    """
    Create a dry-run/rehearsal version of a tool execution
    Returns simulated result
    """
    return {
        "tool": step.tool,
        "args": step.args,
        "simulated": True,
        "expected_outcome": step.expected_outcome,
        "status": "rehearsal_completed",
        "notes": "This is a sandbox rehearsal - no actual execution occurred"
    }
