# syntax=docker/dockerfile:1

# Build-Kit Arguments
#
# See the following links for additional details:
#   - https://docs.docker.com/reference/cli/docker/buildx/build/
#   - https://docs.docker.com/reference/dockerfile/#buildkit-built-in-build-args

# Opt into deterministic output regardless of multi-platform output.
ARG BUILDKIT_MULTI_PLATFORM=1

# Opt into inline build caching.
ARG BUILDKIT_INLINE_CACHE=1

# Disable buildkit git context (default); enablement can be useful for dynamic versioning (e.g., git-tags).
ARG BUILDKIT_CONTEXT_KEEP_GIT_DIR=0

# Install production (ci) dependencies and enable cross-compilation. Leverage
# caching multi-stage builds.
#
# - https://docs.docker.com/build/building/multi-platform/#cross-compilation
# - https://docs.docker.com/build/building/best-practices/#use-multi-stage-builds
FROM --platform=${BUILDPLATFORM} composer:2 AS build

# Establish the working directory.
WORKDIR /opt/share/application

# Copy only the dependency manifests first for efficient layer caching.
COPY composer.json composer.lock ./

# Install production-only dependencies.
RUN composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader --no-scripts

# Copy the full application source.
COPY . .

FROM php:8.2-cli-alpine AS runtime

# Specify SIGKILL as the kernel's syscall unsigned number (9) to forcefully exit the container.
#   - By default, containers are not allocated a STOPSIGNAL.
STOPSIGNAL SIGKILL

# Establish the working directory.
WORKDIR /opt/share/application

# Install PHP extensions commonly required by Laravel.
#
# Ensure multi-lines are sorted.
#   - https://docs.docker.com/build/building/best-practices/#sort-multi-line-arguments
#
# - nproc: prints the number of available processing units.
# - ".dependencies": apk alias for all the installed packages; easier to remove.
RUN apk add --no-cache --virtual ".dependencies" libzip-dev icu-dev $PHPIZE_DEPS \
    && docker-php-ext-install -j$(nproc) \
        intl \
        opcache \
        pdo_mysql \
        zip \
    && pecl install \
        redis \
    && docker-php-ext-enable redis \
        && apk del ".dependencies"

# Install *.so shared C ffi(s).
RUN apk add --no-cache libzip icu

# Copy the application with associated dependencies (vendor) from the build stage.
COPY --from=build /opt/share/application /opt/share/application

# Create the user's group and instance.
# - Prevents shell access: https://docs.docker.com/go/dockerfile-user-best-practices/
RUN addgroup -S -g 1000 laravel
# RUN adduser -H -D -h "/dev/null" -g "" -s "/sbin/nologin" -u 1000 -G "laravel" application-user
RUN adduser -H -D -g "" -s "/sbin/nologin" -u 1000 -G "laravel" application-user
RUN chown -R application-user:laravel /opt/share/application

USER application-user

# Define the default run command.
CMD ["php", "artisan", "slack-me"]

# Optional labels and container metadata.
LABEL owner="segmentational@gmail.com"

#
# Additional Production & Development Considerations:
#
# Best Practices:
#   - https://docs.docker.com/go/dockerfile-user-best-practices/
#
# GH Actions
#   - https://docs.docker.com/build/ci/github-actions/
#
# Laravel:
#   - https://github.com/dockersamples/laravel-docker-examples
#   - https://docs.docker.com/guides/frameworks/laravel/development-setup
#
