# Frontend image: multi-stage — build static assets with Node, serve with
# nginx. nginx also proxies /api/* to the backend container, keeping the
# app same-origin (no CORS configuration needed on the API).

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
