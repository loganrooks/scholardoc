# Log Analysis Automation

Reference documentation for automating `/project:analyze-logs` with the Claude Agent SDK and CI/CD.

## Claude Agent SDK Integration

For automated analysis, the Claude Agent SDK can be used in headless mode:

```typescript
// Example: Automated log analysis with SDK
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

async function analyzeSessionLogs(logDir: string) {
  const result = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 8096,
    messages: [
      {
        role: "user",
        content: `Analyze the session logs in ${logDir} and identify:
          1. Recurring error patterns
          2. Workflow inefficiencies
          3. Opportunities for automation
          4. Recommended improvements

          Format as structured JSON.`
      }
    ],
    // For structured output
    // response_format: { type: "json_object" }
  });

  return result;
}
```

See `/docs/self-improvement-protocol.md` for full SDK integration details.

---

## Scheduled Analysis (GitHub Actions)

```yaml
# .github/workflows/log-analysis.yml
name: Weekly Log Analysis
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Claude Analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npx claude-code --print "Run /project:analyze-logs week all"
```

---

## Local Cron

```bash
# Add to crontab for weekly analysis
0 9 * * 1 cd /path/to/project && claude-code -p "Run /project:analyze-logs week all" >> .claude/logs/analysis.log 2>&1
```
