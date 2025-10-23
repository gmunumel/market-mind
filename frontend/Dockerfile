FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
COPY tsconfig*.json ./
COPY vite.config.ts vitest.config.ts vitest.setup.ts tailwind.config.ts postcss.config.cjs ./
RUN npm install

COPY src ./src
COPY index.html ./index.html

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

FROM nginx:alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
