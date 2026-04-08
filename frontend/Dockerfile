FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package*.json /app/
RUN npm ci

COPY frontend /app
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist /app/dist

EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
