# GPT-Image-2 Reference Repository

## Source

- Repository: `EvoLinkAI/awesome-gpt-image-2-API-and-Prompts`
- GitHub: https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts
- Local copy: `references/awesome-gpt-image-2-API-and-Prompts`
- License: CC0-1.0

## Download Status

The repository text assets have been downloaded and extracted locally. The local network connection to GitHub timed out during full ZIP download, so the image assets may be incomplete.

Available locally:

- `README.md`
- `README_zh-CN.md`
- `README_zh-TW.md`
- Other localized README files
- `cases/*.md`
- `data/ingested_tweets.json`
- Partial `images/`

## Useful Case Files

| Area | Local file |
| --- | --- |
| Portrait photography | `references/awesome-gpt-image-2-API-and-Prompts/cases/portrait_zh-CN.md` |
| Poster and illustration | `references/awesome-gpt-image-2-API-and-Prompts/cases/poster_zh-CN.md` |
| UI and social mockups | `references/awesome-gpt-image-2-API-and-Prompts/cases/ui_zh-CN.md` |
| E-commerce | `references/awesome-gpt-image-2-API-and-Prompts/cases/ecommerce_zh-CN.md` |
| Ad creative | `references/awesome-gpt-image-2-API-and-Prompts/cases/ad-creative_zh-CN.md` |
| Character design | `references/awesome-gpt-image-2-API-and-Prompts/cases/character_zh-CN.md` |
| Comparison experiments | `references/awesome-gpt-image-2-API-and-Prompts/cases/comparison_zh-CN.md` |

## How This Helps This Project

This project can use the reference repository as a prompt-pattern library:

- Extract prompt structures from portrait, poster, product, UI, and character cases.
- Convert stable prompt patterns into local JSON templates.
- Keep our generated templates focused on user portrait preservation, commercial usability, safety constraints, and scenario-specific output quality.
- Use comparison cases to improve A/B test fields later, such as lighting, camera, texture, and layout options.

## Recommended Next Step

Build a local importer that reads selected markdown case files, extracts prompt examples, and writes normalized prompt-pattern records into `src/templates` or a new `data/prompt_patterns.json`.
