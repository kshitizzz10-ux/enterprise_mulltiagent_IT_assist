import re
import logging
from typing import Any, Tuple, Dict, List
from app.state import AgentState
from app.config import settings

logger = logging.getLogger(__name__)

# IPv4 regex matching standard dotted-quad addresses (e.g. 192.168.1.100, 10.0.0.1)
IPV4_REGEX = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


class SecurityAgent:
    """
    Agent 4: Validation Guardrail (Security Agent)
    Ensures zero leakage of sensitive internal enterprise metadata (such as internal network IPs).
    All outputs from Pipeline 3 and Pipeline 4 must pass through this guardrail before leaving the system.
    """
    def __init__(self, token: str = None):
        self.redaction_token = token or settings.IP_REDACTION_TOKEN

    def sanitize(self, state: AgentState) -> AgentState:
        raw_output = state.draft_response
        sanitized_output, count = self._redact(raw_output)

        state.final_response = sanitized_output
        state.redactions_count = count
        state.redacted = count > 0

        if count > 0:
            state.log_step(
                f"Pipeline 5 (Security Guardrail): Detected {count} sensitive pattern(s). "
                f"Redacted to '{self.redaction_token}'."
            )
            logger.warning(f"SecurityAgent redacted {count} sensitive IP address(es).")
        else:
            state.log_step("Pipeline 5 (Security Guardrail): Verified output - No sensitive patterns detected.")

        return state

    def _redact(self, data: Any) -> Tuple[Any, int]:
        """
        Recursively scans and redacts sensitive patterns in strings, lists, or dictionaries.
        """
        if isinstance(data, str):
            matches = IPV4_REGEX.findall(data)
            count = len(matches)
            redacted_str = IPV4_REGEX.sub(self.redaction_token, data)
            return redacted_str, count

        elif isinstance(data, dict):
            new_dict = {}
            total_count = 0
            for k, v in data.items():
                sanitized_val, count = self._redact(v)
                new_dict[k] = sanitized_val
                total_count += count
            return new_dict, total_count

        elif isinstance(data, list):
            new_list = []
            total_count = 0
            for item in data:
                sanitized_item, count = self._redact(item)
                new_list.append(sanitized_item)
                total_count += count
            return new_list, total_count

        return data, 0
