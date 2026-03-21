from __future__ import annotations

import base64
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def load_sync_module():
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "sync_session_log.py"
    )
    spec = importlib.util.spec_from_file_location("sync_session_log", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load sync_session_log.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SYNC_MODULE = load_sync_module()


class SyncSessionLogTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> dict[str, Path]:
        workspace = root / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        transcript_root = root / "claude-projects" / "project-a"
        transcript_root.mkdir(parents=True, exist_ok=True)

        session_id = "session-123"
        transcript_path = transcript_root / f"{session_id}.jsonl"
        subagent_path = transcript_root / session_id / "subagents" / "agent-helper.jsonl"
        telemetry_dir = root / "telemetry"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        telemetry_path = telemetry_dir / "events.json"

        base_entry = {
            "parentUuid": None,
            "isSidechain": False,
            "userType": "external",
            "cwd": str(workspace),
            "sessionId": session_id,
            "version": "2.1.70",
            "gitBranch": "main",
        }

        main_entries = [
            {
                **base_entry,
                "type": "user",
                "uuid": "user-1",
                "timestamp": "2026-03-12T01:00:00Z",
                "message": {
                    "role": "user",
                    "content": "Please audit the project and keep a detailed running log.",
                },
                "todos": [
                    {
                        "content": "Audit the project",
                        "status": "pending",
                        "activeForm": "Auditing the project",
                    }
                ],
            },
            {
                **base_entry,
                "type": "assistant",
                "uuid": "assistant-1",
                "parentUuid": "user-1",
                "timestamp": "2026-03-12T01:00:10Z",
                "message": {
                    "id": "msg-1",
                    "type": "message",
                    "role": "assistant",
                    "model": "glm-5",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "I should inspect the repository and use tools carefully.",
                        },
                        {
                            "type": "text",
                            "text": "I will inspect the repository and keep track of the findings.",
                        },
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": "Bash",
                            "input": {
                                "command": "rg --files .",
                                "description": "List repository files",
                            },
                        },
                    ],
                    "usage": {
                        "input_tokens": 120,
                        "output_tokens": 45,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 300,
                    },
                },
            },
            {
                **base_entry,
                "type": "user",
                "uuid": "user-2",
                "parentUuid": "assistant-1",
                "timestamp": "2026-03-12T01:00:20Z",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tool-1",
                            "content": "RESULT:\n" + ("A" * 4500),
                            "is_error": False,
                        }
                    ],
                },
                "toolUseResult": "RESULT:\n" + ("A" * 4500),
            },
            {
                **base_entry,
                "type": "user",
                "uuid": "user-3",
                "timestamp": "2026-03-12T01:00:30Z",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(b"fake-png-data").decode("ascii"),
                            },
                        }
                    ],
                },
            },
            {
                **base_entry,
                "type": "progress",
                "uuid": "progress-1",
                "timestamp": "2026-03-12T01:00:40Z",
                "toolUseID": "tool-1",
                "parentToolUseID": "tool-1",
                "data": {
                    "type": "bash_progress",
                    "status": "running",
                    "message": "Executing repository scan",
                },
            },
            {
                **base_entry,
                "type": "system",
                "uuid": "system-1",
                "timestamp": "2026-03-12T01:00:50Z",
                "subtype": "api_error",
                "level": "warning",
                "content": "Transient upstream error",
                "error": "rate_limited",
                "retryInMs": 1200,
                "retryAttempt": 1,
                "maxRetries": 3,
            },
            {
                "type": "file-history-snapshot",
                "messageId": "snapshot-1",
                "snapshot": {
                    "messageId": "snapshot-1",
                    "timestamp": "2026-03-12T01:01:00Z",
                    "trackedFileBackups": {
                        "src/app.py": {"version": 2, "backupPath": "app.py@v2"}
                    },
                },
                "isSnapshotUpdate": False,
            },
            {
                "type": "queue-operation",
                "operation": "remove",
                "timestamp": "2026-03-12T01:01:10Z",
                "sessionId": session_id,
                "content": "Remember to capture the rate limit issue.",
            },
            {
                "type": "last-prompt",
                "sessionId": session_id,
                "lastPrompt": "Return a detailed audit summary and no other text.",
            },
            {
                **base_entry,
                "type": "assistant",
                "uuid": "assistant-2",
                "timestamp": "2026-03-12T01:01:20Z",
                "isApiErrorMessage": True,
                "error": "authentication_failed",
                "message": {
                    "id": "msg-2",
                    "type": "message",
                    "role": "assistant",
                    "model": "<synthetic>",
                    "content": [
                        {
                            "type": "server_tool_use",
                            "name": "web-search",
                            "payload": {"query": "audit logging"},
                        }
                    ],
                    "usage": {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                    },
                },
            },
            {
                "type": "summary",
                "summary": "Audit session summary",
                "leafUuid": "assistant-2",
            },
            {
                "type": "mystery-event",
                "timestamp": "2026-03-12T01:01:30Z",
                "payload": {"flag": True},
            },
        ]

        subagent_entries = [
            {
                **base_entry,
                "type": "user",
                "isSidechain": True,
                "agentId": "agent-helper",
                "uuid": "sub-user-1",
                "timestamp": "2026-03-12T01:00:15Z",
                "message": {
                    "role": "user",
                    "content": "Inspect only the logging layer.",
                },
            },
            {
                **base_entry,
                "type": "assistant",
                "isSidechain": True,
                "agentId": "agent-helper",
                "uuid": "sub-assistant-1",
                "parentUuid": "sub-user-1",
                "timestamp": "2026-03-12T01:00:25Z",
                "message": {
                    "id": "sub-msg-1",
                    "type": "message",
                    "role": "assistant",
                    "model": "glm-4.7",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "Subagent is narrowing the audit to the logging layer.",
                        },
                        {
                            "type": "text",
                            "text": "Subagent inspected the logging layer and found no crash path.",
                        }
                    ],
                    "usage": {
                        "input_tokens": 15,
                        "output_tokens": 9,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 12,
                    },
                },
            },
        ]

        telemetry_records = [
            {
                "event_type": "ClaudeCodeInternalEvent",
                "event_data": {
                    "event_name": "tengu_api_success",
                    "client_timestamp": "2026-03-12T01:00:35Z",
                    "model": "glm-5",
                    "session_id": session_id,
                    "event_id": "telemetry-1",
                    "entrypoint": "sdk-cli",
                    "client_type": "sdk-cli",
                    "user_type": "external",
                    "additional_metadata": json.dumps(
                        {
                            "costUSD": 0.012345,
                            "inputTokens": 111,
                            "outputTokens": 22,
                            "cachedInputTokens": 333,
                            "durationMs": 444,
                            "ttftMs": 55,
                            "stop_reason": "tool_use",
                        },
                        ensure_ascii=False,
                    ),
                },
            },
            {
                "event_type": "ClaudeCodeInternalEvent",
                "event_data": {
                    "event_name": "tengu_api_success",
                    "client_timestamp": "2026-03-12T01:00:35Z",
                    "model": "glm-5",
                    "session_id": session_id,
                    "event_id": "telemetry-1",
                    "entrypoint": "sdk-cli",
                    "client_type": "sdk-cli",
                    "user_type": "external",
                    "additional_metadata": json.dumps(
                        {
                            "costUSD": 0.012345,
                            "inputTokens": 111,
                            "outputTokens": 22,
                            "cachedInputTokens": 333,
                            "durationMs": 444,
                            "ttftMs": 55,
                            "stop_reason": "tool_use",
                        },
                        ensure_ascii=False,
                    ),
                },
            },
            {
                "event_type": "ClaudeCodeInternalEvent",
                "event_data": {
                    "event_name": "tengu_tool_use_success",
                    "client_timestamp": "2026-03-12T01:00:36Z",
                    "model": "glm-5",
                    "session_id": session_id,
                    "event_id": "telemetry-2",
                    "entrypoint": "sdk-cli",
                    "client_type": "sdk-cli",
                    "user_type": "external",
                    "process": json.dumps({"rss": 123456, "cpuPercent": 12.5}),
                    "additional_metadata": json.dumps(
                        {
                            "messageID": "msg-1",
                            "toolName": "Bash",
                            "hugeNote": "B" * 2600,
                        },
                        ensure_ascii=False,
                    ),
                },
            },
            {
                "event_type": "ClaudeCodeInternalEvent",
                "event_data": {
                    "event_name": "tengu_api_success",
                    "client_timestamp": "2026-03-12T01:00:37Z",
                    "model": "glm-4.7",
                    "session_id": "other-session",
                    "event_id": "telemetry-3",
                    "entrypoint": "sdk-cli",
                    "client_type": "sdk-cli",
                    "user_type": "external",
                    "additional_metadata": json.dumps(
                        {
                            "costUSD": 9.9,
                            "inputTokens": 999,
                            "outputTokens": 999,
                            "cachedInputTokens": 999,
                            "durationMs": 999,
                            "ttftMs": 999,
                        },
                        ensure_ascii=False,
                    ),
                },
            },
        ]

        self.write_jsonl(transcript_path, main_entries)
        self.write_jsonl(subagent_path, subagent_entries)
        self.write_jsonl(telemetry_path, telemetry_records)
        return {
            "workspace": workspace,
            "transcript_path": transcript_path,
            "subagent_path": subagent_path,
            "telemetry_dir": telemetry_dir,
        }

    def write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load_jsonl(self, path: Path) -> list[dict]:
        rows: list[dict] = []
        with path.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def normalized_markdown(self, text: str) -> str:
        return "\n".join(
            line for line in text.splitlines() if not line.startswith("- Last synced at:")
        )

    def normalized_usage(self, payload: dict) -> dict:
        normalized = json.loads(json.dumps(payload))
        session = normalized.get("session")
        if isinstance(session, dict):
            session.pop("last_synced_at", None)
        return normalized

    def get_output_paths(self, result) -> dict[str, Path]:
        summary_root = result.summary_path.parent
        meta_session_dir = result.session_markdown_path.parent.parent
        return {
            "summary_root": summary_root,
            "meta_session_dir": meta_session_dir,
            "merged_meta": meta_session_dir / "merged" / "session.md",
            "main_summary": summary_root / "agents" / "main" / "summary.md",
            "main_usage": summary_root / "agents" / "main" / "usage.json",
            "subagent_summary": summary_root / "agents" / "agent-helper" / "summary.md",
            "subagent_usage": summary_root / "agents" / "agent-helper" / "usage.json",
            "meta_index": meta_session_dir / "index.md",
            "main_meta": meta_session_dir / "agents" / "main" / "session.md",
            "subagent_meta": meta_session_dir / "agents" / "agent-helper" / "session.md",
            "shared_rendered": meta_session_dir / "artifacts" / "shared" / "rendered",
            "main_rendered": meta_session_dir / "artifacts" / "main" / "rendered",
            "subagent_rendered": meta_session_dir / "artifacts" / "agent-helper" / "rendered",
        }

    def test_sync_renders_supported_events_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "session-123",
                    "transcript_path": str(fixture["transcript_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "PostToolUse",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            paths = self.get_output_paths(result)
            session_md = result.session_markdown_path.read_text(encoding="utf-8")
            summary_md = result.summary_path.read_text(encoding="utf-8")
            main_summary_md = paths["main_summary"].read_text(encoding="utf-8")
            subagent_summary_md = paths["subagent_summary"].read_text(encoding="utf-8")
            meta_index_md = paths["meta_index"].read_text(encoding="utf-8")
            main_meta_md = paths["main_meta"].read_text(encoding="utf-8")
            subagent_meta_md = paths["subagent_meta"].read_text(encoding="utf-8")
            usage_payload = json.loads(result.usage_path.read_text(encoding="utf-8"))
            main_usage_payload = json.loads(paths["main_usage"].read_text(encoding="utf-8"))
            subagent_usage_payload = json.loads(
                paths["subagent_usage"].read_text(encoding="utf-8")
            )

            self.assertEqual(paths["merged_meta"], result.session_markdown_path)
            self.assertTrue(result.summary_path.exists())
            self.assertTrue(result.usage_path.exists())
            self.assertTrue(paths["main_summary"].exists())
            self.assertTrue(paths["main_usage"].exists())
            self.assertTrue(paths["subagent_summary"].exists())
            self.assertTrue(paths["subagent_usage"].exists())
            self.assertTrue(paths["meta_index"].exists())
            self.assertTrue(paths["main_meta"].exists())
            self.assertTrue(paths["subagent_meta"].exists())

            self.assertIn("# Claude Session: Audit session summary [merged]", session_md)
            self.assertIn("`queue-operation`", session_md)
            self.assertIn("`file-history-snapshot`", session_md)
            self.assertIn("`last-prompt`", session_md)
            self.assertIn("[agent-helper]", session_md)
            self.assertIn("Transient upstream error", session_md)
            self.assertIn("tengu_api_success", session_md)
            self.assertIn("0.012345", session_md)
            self.assertIn("Remember to capture the rate limit issue.", session_md)

            shared_artifact_files = list(paths["shared_rendered"].glob("*"))
            main_artifact_files = list(paths["main_rendered"].glob("*"))
            self.assertTrue(any(path.suffix == ".png" for path in shared_artifact_files))
            self.assertTrue(any(path.suffix == ".json" for path in shared_artifact_files))
            self.assertTrue(any(path.suffix == ".txt" for path in main_artifact_files))

            telemetry_lines = (
                result.telemetry_artifact_path.read_text(encoding="utf-8").strip().splitlines()
            )
            self.assertEqual(2, len(telemetry_lines))

            state = json.loads(result.state_path.read_text(encoding="utf-8"))
            self.assertEqual(2, state["version"])
            self.assertEqual(
                "meta/sessions/2026/03/session-123/index.md",
                state["markdown_relpath"],
            )
            self.assertEqual(
                "meta/sessions/2026/03/session-123/merged/session.md",
                state["merged_markdown_relpath"],
            )
            self.assertEqual("summary/2026-03-12_09-00-00", state["summary_dir_relpath"])
            self.assertEqual(
                "summary/2026-03-12_09-00-00/summary.md",
                state["summary_markdown_relpath"],
            )
            self.assertEqual("summary/2026-03-12_09-00-00/usage.json", state["usage_relpath"])
            self.assertEqual(
                "summary/2026-03-12_09-00-00/agents/main/summary.md",
                state["summary_agents_relpaths"]["main"]["summary_markdown_relpath"],
            )
            self.assertEqual(
                "summary/2026-03-12_09-00-00/agents/agent-helper/summary.md",
                state["summary_agents_relpaths"]["agent-helper"]["summary_markdown_relpath"],
            )
            self.assertEqual(
                "meta/sessions/2026/03/session-123/agents/main/session.md",
                state["meta_agents_relpaths"]["main"]["markdown_relpath"],
            )
            self.assertEqual(
                "meta/sessions/2026/03/session-123/agents/agent-helper/session.md",
                state["meta_agents_relpaths"]["agent-helper"]["markdown_relpath"],
            )
            self.assertEqual(2, len(state["telemetry_event_ids"]))

            index_text = result.index_path.read_text(encoding="utf-8")
            self.assertIn("Claude Session: Audit session summary", index_text)
            self.assertIn("sessions/2026/03/session-123/index.md", index_text)
            self.assertEqual(
                result.log_root / "summary" / "2026-03-12_09-00-00" / "summary.md",
                result.summary_path,
            )
            self.assertEqual(
                result.log_root / "summary" / "2026-03-12_09-00-00" / "usage.json",
                result.usage_path,
            )
            self.assertFalse((result.log_root / "summary.md").exists())
            self.assertFalse((result.log_root / "usage.json").exists())
            self.assertIn("## Aggregate Usage", summary_md)
            self.assertIn("## Agents", summary_md)
            self.assertIn("Open session meta index", summary_md)
            self.assertIn("Open merged detail", summary_md)
            self.assertIn("Open usage JSON", summary_md)
            self.assertIn("Open agent summary", summary_md)
            self.assertIn("Open agent detail", summary_md)
            self.assertIn("`main`", summary_md)
            self.assertIn("`agent-helper`", summary_md)
            self.assertIn("Telemetry cost USD", summary_md)
            self.assertIn("(../../meta/sessions/2026/03/session-123/index.md)", summary_md)
            self.assertIn("(../../meta/sessions/2026/03/session-123/merged/session.md)", summary_md)
            self.assertIn("(usage.json)", summary_md)
            self.assertNotIn("## Conversation", summary_md)
            self.assertNotIn("I should inspect the repository and use tools carefully.", summary_md)
            self.assertNotIn("Subagent is narrowing the audit to the logging layer.", summary_md)
            self.assertNotIn("Progress payload", summary_md)
            self.assertNotIn("Remember to capture the rate limit issue.", summary_md)
            self.assertNotIn("file-history-snapshot", summary_md)
            self.assertNotIn("## Telemetry Events", summary_md)

            self.assertIn("## Conversation", main_summary_md)
            self.assertIn("#### Thinking", main_summary_md)
            self.assertIn("I should inspect the repository and use tools carefully.", main_summary_md)
            self.assertIn("#### Output", main_summary_md)
            self.assertIn(
                "I will inspect the repository and keep track of the findings.",
                main_summary_md,
            )
            self.assertIn("#### Tool Call `Bash`", main_summary_md)
            self.assertIn("#### Tool Result `tool-1`", main_summary_md)
            self.assertIn("(../../../../meta/sessions/2026/03/session-123/agents/main/session.md)", main_summary_md)
            self.assertIn("(usage.json)", main_summary_md)
            self.assertNotIn("[agent-helper]", main_summary_md)
            self.assertNotIn("Subagent inspected the logging layer", main_summary_md)

            self.assertIn("## Conversation", subagent_summary_md)
            self.assertIn("[agent-helper]", subagent_summary_md)
            self.assertIn(
                "Subagent is narrowing the audit to the logging layer.",
                subagent_summary_md,
            )
            self.assertIn(
                "Subagent inspected the logging layer and found no crash path.",
                subagent_summary_md,
            )
            self.assertIn(
                "(../../../../meta/sessions/2026/03/session-123/agents/agent-helper/session.md)",
                subagent_summary_md,
            )
            self.assertNotIn("I should inspect the repository and use tools carefully.", subagent_summary_md)

            self.assertIn("# Claude Session: Audit session summary Meta Index", meta_index_md)
            self.assertIn("Open root summary", meta_index_md)
            self.assertIn("Open root usage JSON", meta_index_md)
            self.assertIn("Open merged detail", meta_index_md)
            self.assertIn("Open summary", meta_index_md)
            self.assertIn("Open detail", meta_index_md)
            self.assertIn("artifacts/shared/rendered", meta_index_md)
            self.assertIn("artifacts/main/rendered", meta_index_md)
            self.assertIn("artifacts/agent-helper/rendered", meta_index_md)

            self.assertIn("# Claude Session: Audit session summary [main]", main_meta_md)
            self.assertIn("I should inspect the repository and use tools carefully.", main_meta_md)
            self.assertIn("Transient upstream error", main_meta_md)
            self.assertNotIn("[agent-helper]", main_meta_md)
            self.assertNotIn("Subagent inspected the logging layer", main_meta_md)

            self.assertIn(
                "# Claude Session: Audit session summary [agent-helper]",
                subagent_meta_md,
            )
            self.assertIn("[agent-helper]", subagent_meta_md)
            self.assertIn(
                "Subagent inspected the logging layer and found no crash path.",
                subagent_meta_md,
            )
            self.assertNotIn("I will inspect the repository and keep track of the findings.", subagent_meta_md)

            self.assertEqual("session-123", usage_payload["session"]["id"])
            self.assertEqual("Claude Session: Audit session summary", usage_payload["session"]["title"])
            self.assertEqual("Audit session summary", usage_payload["session"]["summary"])
            self.assertEqual("PostToolUse", usage_payload["session"]["last_hook_event"])
            self.assertEqual(135, usage_payload["transcript_usage"]["input_tokens"])
            self.assertEqual(54, usage_payload["transcript_usage"]["output_tokens"])
            self.assertEqual(312, usage_payload["transcript_usage"]["cache_read_input_tokens"])
            self.assertEqual(0.012345, usage_payload["telemetry"]["cost_usd"])
            self.assertEqual(111, usage_payload["telemetry"]["input_tokens"])
            self.assertEqual(22, usage_payload["telemetry"]["output_tokens"])
            self.assertEqual(333, usage_payload["telemetry"]["cached_input_tokens"])
            self.assertEqual(444, usage_payload["telemetry"]["duration_ms_total"])
            self.assertEqual(55, usage_payload["telemetry"]["average_ttft_ms"])
            self.assertEqual(2, usage_payload["counts"]["telemetry_events"])
            self.assertIn("glm-4.7", usage_payload["models"])
            self.assertIn("glm-5", usage_payload["models"])
            self.assertTrue(
                usage_payload["paths"]["summary_md"].endswith(
                    "/.claude-log/summary/2026-03-12_09-00-00/summary.md"
                )
            )
            self.assertTrue(
                usage_payload["paths"]["session_md"].endswith(
                    "/meta/sessions/2026/03/session-123/merged/session.md"
                )
            )
            self.assertTrue(
                usage_payload["paths"]["meta_index_md"].endswith(
                    "/meta/sessions/2026/03/session-123/index.md"
                )
            )

            self.assertEqual("main", main_usage_payload["agent"]["id"])
            self.assertEqual("main", main_usage_payload["agent"]["key"])
            self.assertEqual("main", main_usage_payload["agent"]["kind"])
            self.assertEqual(120, main_usage_payload["transcript_usage"]["input_tokens"])
            self.assertEqual(45, main_usage_payload["transcript_usage"]["output_tokens"])
            self.assertEqual(300, main_usage_payload["transcript_usage"]["cache_read_input_tokens"])
            self.assertIsNone(main_usage_payload["telemetry"])
            self.assertEqual("session_only", main_usage_payload["telemetry_scope"])

            self.assertEqual("agent-helper", subagent_usage_payload["agent"]["id"])
            self.assertEqual("agent-helper", subagent_usage_payload["agent"]["key"])
            self.assertEqual("subagent", subagent_usage_payload["agent"]["kind"])
            self.assertEqual(15, subagent_usage_payload["transcript_usage"]["input_tokens"])
            self.assertEqual(9, subagent_usage_payload["transcript_usage"]["output_tokens"])
            self.assertEqual(12, subagent_usage_payload["transcript_usage"]["cache_read_input_tokens"])
            self.assertIsNone(subagent_usage_payload["telemetry"])
            self.assertEqual("session_only", subagent_usage_payload["telemetry_scope"])

    def test_sync_is_idempotent_and_dedupes_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            hook_input = {
                "session_id": "session-123",
                "transcript_path": str(fixture["transcript_path"]),
                "cwd": str(fixture["workspace"]),
                "hook_event_name": "Stop",
            }

            first = SYNC_MODULE.sync_session_log(
                hook_input=hook_input,
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )
            first_markdown = first.session_markdown_path.read_text(encoding="utf-8")
            first_summary = first.summary_path.read_text(encoding="utf-8")
            first_usage = json.loads(first.usage_path.read_text(encoding="utf-8"))

            second = SYNC_MODULE.sync_session_log(
                hook_input=hook_input,
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )
            second_markdown = second.session_markdown_path.read_text(encoding="utf-8")
            second_summary = second.summary_path.read_text(encoding="utf-8")
            second_usage = json.loads(second.usage_path.read_text(encoding="utf-8"))

            self.assertEqual(
                self.normalized_markdown(first_markdown),
                self.normalized_markdown(second_markdown),
            )
            self.assertEqual(
                self.normalized_markdown(first_summary),
                self.normalized_markdown(second_summary),
            )
            self.assertEqual(
                self.normalized_usage(first_usage),
                self.normalized_usage(second_usage),
            )
            self.assertEqual(first.summary_path, second.summary_path)
            self.assertEqual(first.usage_path, second.usage_path)

            telemetry_lines = (
                second.telemetry_artifact_path.read_text(encoding="utf-8").strip().splitlines()
            )
            self.assertEqual(2, len(telemetry_lines))

    def test_legacy_session_id_summary_path_migrates_to_timestamp_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            log_root = fixture["workspace"] / ".claude-log"
            legacy_dir = log_root / "summary" / "session-123"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            (legacy_dir / "summary.md").write_text("legacy summary", encoding="utf-8")
            (legacy_dir / "usage.json").write_text("{}", encoding="utf-8")

            state_dir = log_root / "meta" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_path = state_dir / "session-123.json"
            state_path.write_text(
                json.dumps(
                    {
                        "session_id": "session-123",
                        "markdown_relpath": "meta/sessions/2026/03/session-123.md",
                        "summary_dir_relpath": "summary/session-123",
                        "summary_markdown_relpath": "summary/session-123/summary.md",
                        "usage_relpath": "summary/session-123/usage.json",
                    }
                ),
                encoding="utf-8",
            )

            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "session-123",
                    "transcript_path": str(fixture["transcript_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "Stop",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            self.assertEqual(
                log_root / "summary" / "2026-03-12_09-00-00" / "summary.md",
                result.summary_path,
            )
            self.assertFalse((legacy_dir / "summary.md").exists())
            self.assertFalse((legacy_dir / "usage.json").exists())
            self.assertFalse(legacy_dir.exists())

            migrated_state = json.loads(result.state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "summary/2026-03-12_09-00-00",
                migrated_state["summary_dir_relpath"],
            )

    def test_subagent_transcript_resolves_back_to_main_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "agent-helper",
                    "transcript_path": str(fixture["subagent_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "SubagentStop",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            self.assertEqual("session-123", result.session_id)
            paths = self.get_output_paths(result)
            session_md = result.session_markdown_path.read_text(encoding="utf-8")
            summary_md = result.summary_path.read_text(encoding="utf-8")
            subagent_summary_md = paths["subagent_summary"].read_text(encoding="utf-8")
            self.assertIn("Subagent inspected the logging layer", session_md)
            self.assertIn("## Agents", summary_md)
            self.assertNotIn("Subagent inspected the logging layer", summary_md)
            self.assertIn("Subagent inspected the logging layer", subagent_summary_md)
            self.assertIn("Subagent is narrowing the audit to the logging layer.", subagent_summary_md)
            self.assertIn("[agent-helper]", subagent_summary_md)

    def test_summary_title_ignores_placeholder_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            transcript_rows = self.load_jsonl(fixture["transcript_path"])
            transcript_rows[0]["message"]["content"] = "."
            transcript_rows = [
                row for row in transcript_rows if row.get("type") != "summary"
            ]
            transcript_rows.append(
                {
                    "parentUuid": "assistant-1",
                    "isSidechain": False,
                    "userType": "external",
                    "cwd": str(fixture["workspace"]),
                    "sessionId": "session-123",
                    "version": "2.1.70",
                    "gitBranch": "main",
                    "type": "user",
                    "uuid": "user-4",
                    "timestamp": "2026-03-12T01:01:25Z",
                    "message": {
                        "role": "user",
                        "content": "Real follow-up request after placeholder.",
                    },
                }
            )
            self.write_jsonl(fixture["transcript_path"], transcript_rows)

            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "session-123",
                    "transcript_path": str(fixture["transcript_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "Stop",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            summary_md = result.summary_path.read_text(encoding="utf-8")
            self.assertIn(
                "# Claude Session: Real follow-up request after placeholder.",
                summary_md,
            )
            self.assertNotIn("# Claude Session: .", summary_md)

    def test_long_thinking_moves_to_artifact_in_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            transcript_rows = self.load_jsonl(fixture["transcript_path"])
            transcript_rows[1]["message"]["content"][0]["thinking"] = "T" * 5000
            self.write_jsonl(fixture["transcript_path"], transcript_rows)

            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "session-123",
                    "transcript_path": str(fixture["transcript_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "Stop",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            paths = self.get_output_paths(result)
            root_summary_md = result.summary_path.read_text(encoding="utf-8")
            main_summary_md = paths["main_summary"].read_text(encoding="utf-8")
            artifact_dir = paths["main_rendered"]
            self.assertNotIn("Open full artifact", root_summary_md)
            self.assertIn("Open full artifact", main_summary_md)
            self.assertTrue(any(path.suffix == ".txt" for path in artifact_dir.glob("*")))

    def test_sidechain_without_agent_id_uses_source_label_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = self.make_fixture(Path(tmpdir))
            subagent_rows = self.load_jsonl(fixture["subagent_path"])
            for row in subagent_rows:
                row.pop("agentId", None)
            self.write_jsonl(fixture["subagent_path"], subagent_rows)

            result = SYNC_MODULE.sync_session_log(
                hook_input={
                    "session_id": "session-123",
                    "transcript_path": str(fixture["transcript_path"]),
                    "cwd": str(fixture["workspace"]),
                    "hook_event_name": "Stop",
                },
                project_dir=fixture["workspace"],
                telemetry_dir=fixture["telemetry_dir"],
            )

            paths = self.get_output_paths(result)
            subagent_summary_md = paths["subagent_summary"].read_text(encoding="utf-8")
            subagent_meta_md = paths["subagent_meta"].read_text(encoding="utf-8")
            state = json.loads(result.state_path.read_text(encoding="utf-8"))

            self.assertTrue(paths["subagent_summary"].exists())
            self.assertTrue(paths["subagent_usage"].exists())
            self.assertTrue(paths["subagent_meta"].exists())
            self.assertIn("Subagent inspected the logging layer", subagent_summary_md)
            self.assertIn("Subagent inspected the logging layer", subagent_meta_md)
            self.assertEqual(
                "summary/2026-03-12_09-00-00/agents/agent-helper/summary.md",
                state["summary_agents_relpaths"]["agent-helper"]["summary_markdown_relpath"],
            )
            self.assertEqual(
                "meta/sessions/2026/03/session-123/agents/agent-helper/session.md",
                state["meta_agents_relpaths"]["agent-helper"]["markdown_relpath"],
            )


if __name__ == "__main__":
    unittest.main()
