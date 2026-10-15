# Self-RAG frontend

The frontend is a React, TypeScript, and Vite workspace with a conversation
view and a documents view. It currently checks the backend health endpoint;
chat and document APIs are not implemented yet, so the interface does not
display sample content or simulate responses.

## Development

```sh
npm install
npm run dev
```

The Vite development server proxies `/health` to `http://localhost:8000`.
Set `VITE_API_URL` to the backend base URL when it is hosted elsewhere.

## Checks

```sh
npm run build
npm run lint
```
