# Aster daily research feed

The feed runs once per day in GitHub Actions and can also be started manually from the Actions tab. The worker uses Python's standard library, reads Hugging Face Daily Papers without a token, and writes the static JSON feed to `public/data/dailypapers.json`. The workflow copies that same feed to `static/data/dailypapers.json` for Streamlit's client-side dashboard fetch.

## Enable Gemini distillation

1. Push this project to a GitHub repository and make sure `.github/workflows/sync-research.yml` is on its default branch.
2. In the repository's **Settings → Secrets and variables → Actions**, add a repository secret named `GEMINI_API_KEY` (or `LLM_API_KEY`) with a Google AI Studio key. GitHub Actions secrets use one name per secret; a dotted form such as `secrets.llmapi.key` is not a valid nested secret lookup.
3. Open **Actions → Sync daily AI research → Run workflow** to create the first feed. Later runs are scheduled daily at 12:17 UTC.

The workflow makes one schema-constrained Gemini request for the daily batch. It publishes the top eight trending papers (configurable from five to ten), their author and abstract metadata, tags, upvote counts and observed upvote velocity to `public/data/dailypapers.json`, then copies that exact snapshot to `static/data/dailypapers.json` for the Streamlit app. If the key is absent or the request fails or is rate-limited, it still publishes the source abstracts without inventing a summary. The worker does not require Hugging Face credentials or install third-party Python packages. GitHub Actions `contents: write` permission is needed for its bot commit.

## Run the worker manually

From the project root, run `python scripts/sync_daily_papers.py`. Set `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or `LLM_API_KEY` in the environment to enable the distillation request; without one, the worker writes the abstract fallback. This local run requires network access to Hugging Face and Google AI Studio.

Free-tier availability, quotas, and eligibility are controlled by the respective providers and may change. The workflow has no paid cloud service or always-on runner configured.
