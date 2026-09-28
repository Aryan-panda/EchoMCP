# EchoMCP — Comprehensive Testing Strategy
**Project:** Grok Voice Bridge (EchoMCP)  
**Version:** 1.0.0  
**Phase:** Phase 0 (Architecture & Contracts)  

---

## 1. Testing Philosophy & Phase Gates

The project follows a **strict phased gate process**. No phase is marked complete, and no subsequent phase code is committed, until all mandatory test suites for that phase achieve a 100% pass rate.

Testing Layers:
1. **Unit Tests:** Fast, isolated tests of domain models, regex parsers, emotion tag extractors, and auth validators.
2. **Contract Tests:** Strict verification of MCP JSON-RPC schemas and tool discovery payloads against MCP SDK specifications.
3. **API Tests:** HTTP integration tests using `httpx.AsyncClient` covering all endpoints under `/health`, `/ready`, `/api/v1/speak`, `/api/v1/audio`, and `/api/v1/voices`.
4. **Provider Tests:** Verification of `TTSProvider` contracts using both `MockTTSProvider` and `CosyVoiceProvider`.
5. **Integration & E2E Tests:** Full sequential generation, audio persistence, metadata validation, and replay consistency.

---

## 2. Test Directory Layout

```
mcp-server/tests/
├── conftest.py                       # Global fixtures (test client, auth headers, mock provider)
├── unit/
│   ├── test_emotion_parser.py        # All controlled emotion tags, malformed input, strip verification
│   ├── test_auth.py                  # Bearer token validation, missing token, invalid scheme
│   ├── test_data_models.py           # Pydantic v2 serialization, validation clamps
│   └── test_cleanup.py               # Retention calculation logic
├── contract/
│   ├── test_mcp_handshake.py         # MCP protocol initialization, client-server negotiation
│   └── test_mcp_tools.py             # speak_response tool definition, schema compliance
├── integration/
│   ├── test_api_health.py            # /health, /ready, /version
│   ├── test_api_speech.py            # POST /api/v1/speak (valid, invalid text, speed clamps)
│   ├── test_api_audio.py             # GET /api/v1/audio pagination, file streaming, deletion
│   └── test_api_voices.py            # Reference upload, listing, Voice 1 deletion safety
└── providers/
    ├── test_mock_provider.py         # MockTTSProvider synthesis contract
    └── test_cosyvoice_provider.py    # CosyVoice HTTP client integration
tests/
└── e2e/
    └── test_end_to_end_flow.py       # Sequential generation, replay isolation, audio permanence
```

---

## 3. Test Execution Matrix by Phase

| Phase | Target Scope | Mandatory Test Commands | Passing Gate Criteria |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Architecture & Contracts | Review checklist & contract validation | Complete and internally consistent specs |
| **Phase 1** | Scaffolding & Docker | `docker compose up -d`, health probes | All 3 containers pass health checks |
| **Phase 2** | MCP Server & Auth | `pytest mcp-server/tests/contract/` | MCP discovery & tool invocation succeed |
| **Phase 3** | TTS Abstraction | `pytest mcp-server/tests/providers/` | Mock provider conforms to `TTSProvider` |
| **Phase 4** | Real TTS (CosyVoice-300M-Instruct) | `pytest mcp-server/tests/integration/test_tts_synthesis.py` | Audio output is synthesized and valid WAV |
| **Phase 5** | Voice ID 1 | `pytest mcp-server/tests/integration/test_api_voices.py` | Voice 1 cloning produces targeted speech |
| **Phase 6** | Emotion / Prosody | `pytest mcp-server/tests/unit/test_emotion_parser.py` | 100% of emotion tags parsed and stripped |
| **Phase 7** | Audio Store & Replay | `pytest mcp-server/tests/integration/test_api_audio.py` | Earlier audio remains playable after new calls |
| **Phase 8** | Web Dashboard | Frontend component & API integration tests | Full UI administration and replay functional |
| **Phase 9** | Cloudflare Tunnel | Public ingress test with remote MCP client | Secure invocation over public HTTPS |
| **Phase 10**| Grok Integration | Live chat validation with consumer Grok | Grok tool calls generate durable audio |
| **Phase 11**| Hardening | Full suite: `pytest` + stress tests | Zero regressions or unhandled edge cases |

---

## 4. Standard Pytest Execution Commands

```bash
# Run all unit tests
pytest mcp-server/tests/unit/ -v

# Run MCP contract tests
pytest mcp-server/tests/contract/ -v

# Run full API integration tests
pytest mcp-server/tests/integration/ -v

# Run complete test suite with coverage
pytest --cov=mcp-server/app --cov-report=term-missing
```
