# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Re-export new module classes (Pasos 33-41)
# NOTE: `app` from agent.py is NOT imported here to avoid google.adk dependency
# at import time. Import it explicitly: `from app.agent import app`
from .a2a.protocol import A2AMessage, A2AMessageType, A2AProtocol, A2AResponse
from .dag.orchestrator import DAGGraph, DAGNode, DAGNodeStatus, DAGOrchestrator
from .disclosure.logger import ProgressiveDisclosure, TrustAdaptiveLevel
from .edge_glow import EdgeGlow, GlowSnapshot, SLOCalibrator, SystemPulse
from .killswitch.detector import RecursionDetector, RecursionRecord
from .otel.injector import _OTEL_AVAILABLE, OtelInjector, otel_traced
from .postmortem.store import IncidentRecord, PostmortemStore, fingerprint_error
from .red_team.simulator import AttackResult, AttackVector, RedTeamSimulator
from .sandbox.runtime import AnomalyRecord, SandboxLevel, SandboxProfile, SandboxRuntime
from .spiffe.manager import SpiffeConfig, SpiffeIdentity, SpiffeManager
from .trust_score.scorer import ScoreFactor, ScoreReport, TrustScorer
from .twin.emitter import DigitalTwinEmitter, TwinSnapshot
from .twin.fidelity import FidelityReport, TwinFidelityValidator
from .vector_memory.store import (
    MemoryVector,
    SearchResult,
    VectorMemoryConfig,
    VectorMemoryStore,
)
from .vibe_diff.dashboard import ReviewDecision, VibeDiffDashboard, VibeDiffRecord
from .watchdog.guardian import IntegrityReport, NeutralizationEvent, WatchdogGuardian

__all__ = [
    "_OTEL_AVAILABLE",
    "A2AMessage",
    "A2AMessageType",
    "A2AProtocol",
    "A2AResponse",
    "AnomalyRecord",
    "AttackResult",
    "AttackVector",
    "DAGGraph",
    "DAGNode",
    "DAGNodeStatus",
    "DAGOrchestrator",
    "DigitalTwinEmitter",
    "EdgeGlow",
    "FidelityReport",
    "GlowSnapshot",
    "IncidentRecord",
    "IntegrityReport",
    "MemoryVector",
    "NeutralizationEvent",
    "OtelInjector",
    "PostmortemStore",
    "ProgressiveDisclosure",
    "RecursionDetector",
    "RecursionRecord",
    "RedTeamSimulator",
    "ReviewDecision",
    "SLOCalibrator",
    "SandboxLevel",
    "SandboxProfile",
    "SandboxRuntime",
    "ScoreFactor",
    "ScoreReport",
    "SearchResult",
    "SpiffeConfig",
    "SpiffeIdentity",
    "SpiffeManager",
    "SystemPulse",
    "TrustAdaptiveLevel",
    "TrustScorer",
    "TwinFidelityValidator",
    "TwinSnapshot",
    "VectorMemoryConfig",
    "VectorMemoryStore",
    "VibeDiffDashboard",
    "VibeDiffRecord",
    "WatchdogGuardian",
    "fingerprint_error",
    "otel_traced",
]
