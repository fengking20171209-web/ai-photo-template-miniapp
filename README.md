# AI Photo Template Miniapp

> Transform your portrait into stunning AI-generated photos using curated templates.

[中文文档](README.zh-CN.md)

## Features

- 50+ curated photo templates (ancient Chinese, career portraits, fashion, product posters, etc.)
- Template-based prompt generation for consistent, high-quality results
- Mock image generation mode (zero API cost for development)
- HTTP adapter ready for GPT-Image-2 / EvoLinkAI / custom APIs
- Batch generation support
- Gallery with search and filtering
- One-click Docker deployment

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/your-org/ai-photo-template-miniapp.git
cd ai-photo-template-miniapp
docker-compose up
# Open http://localhost:3000
```

### Local Development

```bash
npm install
npm run check
npm run list
npm run api
# Open http://localhost:3000
```

## Template System

Templates are JSON files in `templates/`. Each template defines:

- `prompt_blocks`: 8 structured sections (subject, face, clothing, scene, lighting, camera, quality, commercial_use)
- `options`: generation parameters (ratio, face_strength, etc.)
- `negative_prompt`: excluded content

See [docs/en/template-authoring.md](docs/en/template-authoring.md) for the full guide.

## API

The project provides two API layers:

- **Node.js API** (port 3000): Template listing, prompt generation, mock image generation
- **FastAPI** (port 8000): Image gallery search, analytics, template catalog proxy

See [docs/en/api-reference.md](docs/en/api-reference.md) for endpoints.

## Architecture

```
User Upload → Template Selection → Prompt Builder → Image API → Result Gallery
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Tech Stack

- Frontend: Vanilla JavaScript + CSS
- CLI/Scripts: TypeScript (tsx)
- Backend: Python FastAPI + SQLAlchemy
- Data: JSON templates, SQLite (gallery)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License. See [LICENSE](LICENSE).
