# Connectors (all optional)

A connector is an MCP server: a plug that gives the agent extra tools. The skill works with none of them, using FFmpeg and local Whisper alone. Each one below adds something. Offer them one at a time, say what it costs, and let the user choose.

| Connector | Adds | Cost | Free alternative already in the skill |
|---|---|---|---|
| ElevenLabs | Best word timings (Scribe), voice isolation, music, sound effects, text-to-speech | Paid credits; small free tier | `transcribe_local.py` (Whisper); FFmpeg clean-up in `audio_mix.py`; the user's licensed music |
| vidIQ | YouTube keyword volume, outlier videos, competitor stats, transcripts, monthly review | vidIQ plan credits; plan must include MCP access | Skip research, or the user supplies topics and titles |
| HyperFrames by HeyGen (hosted) | Shareable HeyGen project rendered in the cloud | HeyGen account; may use credits | Local HyperFrames CLI (`npx hyperframes`), free |
| Shell connector (Desktop Commander) | Lets a chat-only agent run commands and edit files on the user's computer | Free, open source | Not needed if the agent already has a shell (Claude Code, Codex, Cursor and similar) |

## Adding them

This skill keeps the definitions in its `connectors/catalog.json` and has a helper that adds the ones the user picks to an MCP config file. It writes no secrets.

```
python <this skill>/connectors/setup_connectors.py --list
python <this skill>/connectors/setup_connectors.py --add elevenlabs,vidiq --target "<video library>/.mcp.json"
```

`.mcp.json` in the project folder is read by Claude Code and several other agents. For agents with their own config (Claude desktop: Settings, Developer, Edit config; Cursor: `.cursor/mcp.json`; Codex: `~/.codex/config.toml`), run with `--print` and paste the entries where that agent keeps its MCP servers. Chat apps with a connector directory: add the connector by name there instead.

Ask before running the helper: it changes the agent's configuration. Restart the agent afterwards, then check that the new tools show up. To take entries out again: `--remove elevenlabs,vidiq --target FILE` (or `--remove all`); other entries are left alone and a `.bak` copy is kept.

### ElevenLabs
1. The user gets an API key at elevenlabs.io (Settings, API keys).
2. Install uv (see `tools-setup.md`).
3. The user sets `ELEVENLABS_API_KEY` in their environment, or pastes the key into their own agent config in place of `${ELEVENLABS_API_KEY}`. Never ask them to paste it into chat.
4. On Windows, if the agent reports `spawn uvx ENOENT`, use the full path to `uvx.exe` (find it with `where uvx`).

Without the connector, `transcribe_elevenlabs.py` still gives ElevenLabs transcripts using the key in `.env.local`.

### vidIQ
Remote server at `https://mcp.vidiq.com/mcp`. The user signs in to vidIQ in the browser when the agent first connects. Read-only on the user's channel.

### HyperFrames by HeyGen (hosted)
Add it by name from the agent's connector directory and sign in to HeyGen. In an agent that has a local filesystem its compose and render tools may be switched off in favour of the local CLI; that is expected. Use the local CLI in that case.

### Shell connector
Only for agents with no shell of their own. On Windows the helper wraps `npx` in `cmd /c` so it starts correctly.

## Rules for paid connectors
- Say what you plan to call and roughly what it costs before the first call in a session. Wait for a yes.
- A yes covers that job only. Ask again for the next file or the next batch.
- Send the least that does the job (audio, not video; a clip, not the whole recording).
- Note which connectors are set up in `edit_rules.md` under Toolkit.
