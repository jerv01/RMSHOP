# Imagen del frontend de RM Shop. Etapas: dev -> build.
# Node 26 no incluye Corepack, por eso pnpm se instala con npm y versión fija.

FROM node:26.13.0-alpine AS dev
RUN npm install -g pnpm@10.34.9
# Store fijo: con node_modules en un volumen aparte, pnpm crearía otro dentro del código montado.
ENV npm_config_store_dir=/pnpm-store
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# Genera el sitio estático en /app/dist (Vercel construye desde el código fuente y no usa esta etapa).
FROM dev AS build
RUN pnpm build
