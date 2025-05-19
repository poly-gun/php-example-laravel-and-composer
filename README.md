# `php-example-laravel-and-composer`

## Overview

The following repository originated from an interview's technical challenge where the goal
was to build an automated deployment and container. Additionally, requirements included 
to document usage.

While Laravel nor PHP won't be common in other personal or professional projects, the following
project makes good use of GH Actions and contains a relatively lean `Dockerfile` that should
adhere to best practices.

## Setup

**Prerequisites**

- [Homebrew](https://brew.sh)
- [Node.js](https://nodejs.org/en/download)

###### Install PHP

> [!NOTE]
> Depending on developer preferences, see [Laravel's `php` and
`composer` installation instructions](https://laravel.com/docs/12.x/installation#installing-php).
> - Ensure to carefully consider the application's required `php` and `composer` versions.

1. Install `php@8.2` via `brew`.
    ```bash
    brew install php@8.2
    ```
1. Configure `php` executable & compiler flags.
    ```bash
    # Establish backup of shell-specific rc (zsh)
    cp ~/.zshrc ~/.zshrc.bak.$(date +%Y-%m-%dT%H:%M:%S%z)

    # Verify it created successfully
    # find ~/ -type f -name ".zsh*" -maxdepth 1

    # Check installation path
    brew --prefix php@8.2

    # Update PATH to include php binaries if not already established
    grep -Rq "$(brew --prefix php@8.2)/bin" ~/.zshrc || echo "export PATH=\"$(brew --prefix php@8.2)/bin:\$PATH\"" >> ~/.zshrc
    grep -Rq "$(brew --prefix php@8.2)/sbin" ~/.zshrc || echo "export PATH=\"$(brew --prefix php@8.2)/sbin:\$PATH\"" >> ~/.zshrc

    # Update current shell session
    source ~/.zshrc

    # Verify executable is globally available
    php --version
    # >>> PHP 8.2.28 (cli) (built: Mar 11 2025 17:58:12) (NTS)

    # (Optional) Export compiler flags if and when applicable
    # export LDFLAGS="$(brew --prefix php@8.2)/lib"
    # export CPPFLAGS="$(brew --prefix php@8.2)/include"
    ```

###### Composer

1. [Install `composer`](https://getcomposer.org/download/).
    ```bash
    php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
    # Always verify hash(es) against source
    php -r "if (hash_file('sha384', 'composer-setup.php') === 'dac665fdc30fdd8ec78b38b9800061b4150413ff2e3b6f88543c636f7cd84f6db9189d43a81e5503cda447da73c7e5b6') { echo 'Installer verified'.PHP_EOL; } else { echo 'Installer corrupt'.PHP_EOL; unlink('composer-setup.php'); exit(1); }"
    php composer-setup.php
    php -r "unlink('composer-setup.php');"
    ```
1. (Optional) Add `composer.phar` to `.gitignore`, or move executable to global location.
    ```bash
    mv composer.phar /usr/local/bin/composer

    # Verify composer is now callable
    [[ $(command -v composer) ]] && echo "Successfully installed composer"
    ```
1. Verify `composer` version.
    ```bash
    composer --version
    # >>> Composer version 2.8.9 2025-05-13 14:01:37
    # >>> PHP version 8.2.28 (/opt/homebrew/Cellar/php@8.2/8.2.28_1/bin/php)
    ```

## Getting Started

> [!IMPORTANT]
> Ensure all system requirements - see the [setup](#setup) section for additional information.

1. Install local dependencies.
    ```bash
    # composer install --ignore-platform-reqs
    composer install
    ```
1. Examine laravel package.
    ```bash
    php artisan about
    ```
1. Copy repository's example settings.
    ```bash
    if [[ ! -f "$(git rev-parse --show-toplevel)/.env" ]] && [[ -f "$(git rev-parse --show-toplevel)/.env.example" ]]; then
        echo "Performing First Time Local Development Setup ..."

        echo "Copying .env.example to .env"
        echo " - See https://laravel.com/docs/12.x/configuration#environment-configuration for additional information"

        cd "$(git rev-parse --show-toplevel)"

        cp .env.example .env
    fi
    ```
1. Configure additional _**local development preferences**_. Refer
   to [official documentation](https://laravel.com/docs/12.x/configuration#environment-configuration) for available
   options.

> [!TIP]
> Avoid overwriting `.env.example` with production-related settings.

### Secrets and Configuration

1. Add encryption provider - [official documentation](https://laravel.com/docs/12.x/encryption).
    ```bash
    php artisan key:generate # Establishes the APP_KEY secret value
    ```
1. Set the `TEST_SECRET_1` (which is likely intended to be
   a [signing secret](https://api.slack.com/authentication/verifying-requests-from-slack)).
    ```bash
    # A Slack signing secret is typically a randomly generated string with a length of 32 hexadecimal characters
    python3 -c "import secrets; v = secrets.token_hex(32); print(v)"

    # Shell
    # head -c 32 /dev/urandom | xxd -p -u | head -n 1

    # Establish the value if it doesn't exist - consider adding quotes around environment variable assignments especially relating to secrets
    grep -Rq "TEST_SECRET_1" .env || echo "TEST_SECRET_1=\"$(python3 -c "import secrets; v = secrets.token_hex(32); print(v)")\"" >> .env

    # Replace the TEST_SECRET_1 value for demonstrative purposes if it already exists while creating an archive
    sed -i ".backup" "s/TEST_SECRET_1=.*$/TEST_SECRET_1=\"$(python3 -c "import secrets; v = secrets.token_hex(32); print(v)")\"/" .env
    ```
    - The following section is intended to showcase thought process; these overly complex one-liners are for
      illustrative purposes only.

#### Security Considerations & Discussion

<br>

> [!CAUTION]
> **Never commit secrets to source control.**
>
> Laravel’s built-in [encryption utilities](https://laravel.com/docs/12.x/encryption), and tools like [
`sops`](https://github.com/getsops/sops) claim to add layers of protection; however,
> **they don’t solve the core problem**: secrets living in the repository.

<br>

The only approach that **scales, secures, and keeps complexity low** is to follow the [**12-Factor App
** "Config" principles](https://12factor.net/config):

1. **Store secrets outside the codebase**: in environment variables or a dedicated secret manager (AWS Secrets Manager,
   Vault, etc.).
2. **Inject them at runtime** during local setup, deployment(s), or virtualization (VM, container) start-up.
3. **Version the _names_ of the variables, not their values** (e.g., document required keys in `.env.example`).

Even with services like **_Laravel Cloud_** that auto-decrypt encrypted files, committing secrets still hard-wires
sensitive data to version history and vendor-specific workflows, _creating long-term exposure and lock-in risks._

See [`.pre-commit-config.yaml`](./.pre-commit-config.yaml) for additional local and automated-related security hooks
for preventing secrets from getting leaked.

### Running the Application

#### Local

```bash
php artisan hello
# >>> Successful - Hello World
```

#### Docker

###### Build

- See [the `container-build.bash`](./scripts/container-build.bash) for a shell-script.

```bash
docker build -t "php-hello-world:latest" .
```

###### Run

- See [the `container-run-with-local-environment.bash`](./scripts/container-run-with-local-environment.bash) for a shell-script that will leverage a local `.env` rather than the built one.

```bash
docker run --env-file "$(git rev-parse --show-toplevel)/.env" php-hello-world
```
