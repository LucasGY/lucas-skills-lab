# lucas-skills-lab

Personal skill repository for Codex/OpenClaw-style skills.

## Layout

Each skill lives under `skills/<skill-name>/` and must include a `SKILL.md`.

```text
skills/
  fetch-fedwatch/
    SKILL.md
    package.json
    package-lock.json
    scripts/
```

## Included skills

### `fetch-fedwatch`

Fetches public CME FedWatch data without the paid FedWatch API.

Supported exports:
- `current`: Current target rate table
- `conditional`: Conditional meeting probabilities table

Node usage:

```bash
cd skills/fetch-fedwatch
npm install
npm run fetch -- current fedwatch_current_target_rate.csv
npm run fetch -- conditional fedwatch_conditional_probabilities.csv
```

Python usage:

```bash
cd skills/fetch-fedwatch/scripts
python fetch_fedwatch_conditional.py current fedwatch_current_target_rate.csv
python fetch_fedwatch_conditional.py conditional fedwatch_conditional_probabilities.csv
```
