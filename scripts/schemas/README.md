# Vendored schemas

Official Agent Plugins 1.0.0 JSON Schemas, used by `scripts/validate.py`.

| File | Source |
|---|---|
| `plugin.schema.json` | <https://agent-plugins.org/schemas/1.0.0/plugin.schema.json> |
| `mcp.schema.json` | <https://agent-plugins.org/schemas/1.0.0/mcp.schema.json> |

They are refreshed by hand. When a new spec version is published at
<https://agent-plugins.org/specification>, update them and the `$schema` value in each plugin's
`plugin.json` (and its `.claude-plugin/plugin.json` copy):

```
curl -fL https://agent-plugins.org/schemas/<version>/plugin.schema.json -o scripts/schemas/plugin.schema.json
curl -fL https://agent-plugins.org/schemas/<version>/mcp.schema.json -o scripts/schemas/mcp.schema.json
```
