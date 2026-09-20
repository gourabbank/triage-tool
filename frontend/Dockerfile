FROM node:20-alpine AS build
WORKDIR /app
COPY package.json tsconfig.json ./
RUN npm install
COPY src ./src
RUN npx tsc

FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY --from=build /app/dist /usr/share/nginx/html/dist
EXPOSE 80