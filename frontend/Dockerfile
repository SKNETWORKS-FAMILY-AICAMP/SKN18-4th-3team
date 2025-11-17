FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source
COPY frontend/ .

# Build-time environment for CRA
ARG REACT_APP_DJANGO_HOST=localhost
ARG REACT_APP_DJANGO_PORT=8000
ENV REACT_APP_DJANGO_HOST=$REACT_APP_DJANGO_HOST \
    REACT_APP_DJANGO_PORT=$REACT_APP_DJANGO_PORT

RUN npm run build

FROM nginx:stable-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
