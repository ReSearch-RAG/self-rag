# Self-RAG frontend

The React, TypeScript, and Vite workspace connects the documents and chat
pages to the FastAPI backend. Documents are loaded from the backend; uploads
and answers are not simulated.

## Development

Start the FastAPI application on port `8009`, then run:

```sh
npm install
npm run dev
```

Vite proxies `/health`, `/documents`, `/chat`, and `/queries` to
`http://localhost:8009`. Set `VITE_API_URL` to a backend base URL to bypass
the proxy. Cross-origin direct requests require the backend to allow the
frontend origin; the current FastAPI application does not configure CORS.

The upload endpoint requires an existing integer `user_id`. Enter that ID in
the documents page; the backend currently provides no user registration or
user lookup endpoint. Chat is enabled only for documents whose backend status
is `processed`. The chat response does not include citations, and the backend
does not persist conversation history.

## Checks

```sh
npx tsc --noEmit
npm run build
npm run lint
```
