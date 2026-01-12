import hashlib
import random
import secrets
import string
import sys
import textwrap

import jinja2
import questionary


class EnvFileCreator:
    def __init__(self, file_name: str = ".env") -> None:
        self.file_name = file_name
        self.env_file_lines = []
        self.postgres_password = f'"{self.generate_password()}"'
        self.n8n_hostname = ""
        self.postgres_db_name = "postgres"
        self.nginx_urls = {}

    def create_nginx_config(
        self,
    ) -> None:
        with open("nginx/nginx.conf.j2") as nginx_template_file:
            nginx_template = jinja2.Template(nginx_template_file.read())
            print(self.nginx_urls)
            template_output = nginx_template.render(**self.nginx_urls)
            with open("nginx/nginx.conf", "w") as nginx_config_file:
                nginx_config_file.write(template_output)

    def safe_prompt(self, *args, **kwargs):
        """Creates a safe prompt for Questionary that exits on Ctrl+C.

        Returns:
            str: Answer from the prompt.
        """
        result = questionary.text(*args, **kwargs).ask()
        if result is None:
            print("\nProcess interrupted by user. Exiting...")
            sys.exit(0)
        return result

    def add_line(self, key: str, value: str) -> None:
        """Adds a line to the environment file.

        Args:
            key (str): Environment variable key.
            value (str): Environment variable value.
        """
        self.env_file_lines.append(f"{key}={value}\n")

    def add_text(self, text: str) -> None:
        """Adds a block of text to the environment file.

        Args:
            text (str): Text to add to the environment file.
        """
        self.env_file_lines.append(f"{text}")

    def write(self) -> None:
        """Writes the environment file to disk."""
        with open(self.file_name, "w") as file:
            file.writelines(self.env_file_lines)

    def create_32_char_hex_secret(self) -> str:
        """Creates a 32-character hexadecimal secret.

        Returns:
            str: 32 character hexadecimal secret.
        """
        return secrets.token_hex(16)

    def generate_password(self, length=16):
        """Generates a random password.

        Args:
            length (int, optional): Length of the password to created. Defaults to 16.

        Returns:
            _type_: Randomly generated password.
        """
        alphabet = string.ascii_letters + string.digits + "!-_"
        password = "".join(secrets.choice(alphabet) for _ in range(20))
        return password

    def generate_random_sha_256_hash(self, string_length=32):
        """Generates a random SHA-256 hash from a random alphanumeric string.

        Args:
            string_length (int, optional): Length of the random starting string. Defaults to 32.

        Returns:
            _type_: Random SHA-256 hash.
        """
        # Generate a random alphanumeric string
        random_string = "".join(
            random.choices(string.ascii_letters + string.digits, k=string_length)
        )

        # Create SHA-256 hash
        hash_object = hashlib.sha256(random_string.encode())
        hex_digest = hash_object.hexdigest()

        return hex_digest

    def create_qdrant_envs(self) -> None:
        """
        Creates environment variables specific to Qdrant.
        """
        self.add_text(
            textwrap.dedent(
                """
        ######
        # These are Qdrant specific environment variables.
        ######
        """
            )
        )
        self.add_line("QDRANT__SERVICE__API_KEY", f'"{self.generate_password(16)}"')
        self.qdrant_url = self.safe_prompt(
            "Replace if you plan to use qdrant outside of docker ",
            default="qdrant.local.mydomain.com",
        )
        print(self.qdrant_url)
        self.nginx_urls["QDRANT_HOSTNAME"] = self.qdrant_url
        self.add_line(
            "QDRANT_PUBLIC_URL",
            f"https://{self.qdrant_url}",
        )

    def create_postgres_envs(self) -> None:
        """
        Creates environment variables specific to Postgres DB related to N8N.
        """
        self.add_text(
            textwrap.dedent(
                """
        ######
        # These are Postgres specific environment variables.
        ######
        """
            )
        )

        self.add_line("N8N_POSTGRES_USER", "postgres")
        self.add_line("N8N_POSTGRES_PASSWORD", f'"{self.generate_password(16)}"')
        self.add_line("N8N_POSTGRES_DB", "n8n_db")
        self.add_line("N8N_POSTGRES_NON_ROOT_USER", "n8n_db_user")
        self.add_line(
            "N8N_POSTGRES_NON_ROOT_PASSWORD", f'"{self.generate_password(16)}"'
        )

    def create_n8n_envs(self) -> None:
        """
        Creates environment variables specific to N8N.
        """
        self.add_text(
            textwrap.dedent(
                """
        ######
        # These are N8N specific environment variables.
        ######
        """
            )
        )
        self.n8n_hostname = self.safe_prompt(
            "Enter the value for N8N WEBHOOK_URL: ", default="n8n.local.mydomain.com"
        )
        self.add_line("N8N_ENCRYPTION_KEY", self.create_32_char_hex_secret())
        self.add_line("N8N_RUNNERS_AUTH_TOKEN", f'"{self.generate_password(16)}"')
        self.nginx_urls["N8N_HOSTNAME"] = self.n8n_hostname.strip("https://").strip("/")
        # self.n8n_hostname = f'"{questionary.text().ask()}"'
        self.add_line("WEBHOOK_URL", f"https://{self.n8n_hostname}")
        self.add_line("N8N_EDITOR_BASE_URL", f"https://{self.n8n_hostname}")
        self.add_line("N8N_HOST", f'"{self.n8n_hostname}"')

    def create_supabase_envs(self) -> None:
        """
        Creates environment variables specific to Supabase.
        """
        self.add_text(
            textwrap.dedent(
                """
        ######
        # These are Supabase specific environment variables.
        ######
        """
            )
        )

        self.add_line("DASHBOARD_USERNAME", "supabase")
        self.add_line("DASHBOARD_PASSWORD", f'"{self.generate_password(16)}"')
        self.add_line("SECRET_KEY_BASE", self.create_32_char_hex_secret())
        self.add_line("VAULT_ENC_KEY", self.create_32_char_hex_secret())

        print(
            textwrap.dedent(
                """
                The following environment variables are for setting up Supabase.\n
                You should visit this site to generate the API keys below.
                The defaults are provided for demonstration purposes only and should not be used in production.
                You will need to create a secret, and a service and anon secret using a key.
                https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys
                """
            )
        )
        self.add_line(
            "JWT_SECRET",
            self.safe_prompt(
                "Enter the value for JWT_SECRET: ",
                default="oAh7oLWSlK9mLH1zBWFI2Qa7mXI9Btvc1Ddz9Nbm",
            ),
        )
        self.add_line(
            "ANON_KEY",
            self.safe_prompt(
                "Enter the value for ANON_KEY: ",
                default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU1NzUyNDAwLCJleHAiOjE5MTM1MTg4MDB9.fY6F-eYIXdpPyyVYO7mz9dms4aBHkwWlT5RRy8bzTo0",
            ),
        )
        self.add_line(
            "SERVICE_ROLE_KEY",
            self.safe_prompt(
                "Enter the value for SERVICE_ROLE_KEY: ",
                default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTU3NTI0MDAsImV4cCI6MTkxMzUxODgwMH0.jv3tS1fkhRbPlsiTk1C5PAQGOtng2tr5nLqHbu_-2TQ",
            ),
        )
        self.add_line("POSTGRES_PASSWORD", f'"{self.generate_password(16)}"')
        print(
            textwrap.dedent(
                """
            The following environment variables are for setting up the Postgres DB that Supabase will use.
            If you are not using an external postgres instance, you can leave these as is.
            Supabase docker-compose file will provide a db for you.
            """
            )
        )
        self.add_line("POSTGRES_HOST", "db")
        self.add_line("POSTGRES_DB", "postgres")
        self.add_line("POSTGRES_PORT", "5432")
        self.add_text(
            textwrap.dedent(
                """
            ############
            # Supavisor -- Database pooler
            ############
            # Port Supavisor listens on for transaction pooling connections
            POOLER_PROXY_PORT_TRANSACTION=6543
            # Maximum number of PostgreSQL connections Supavisor opens per pool
            POOLER_DEFAULT_POOL_SIZE=20
            # Maximum number of client connections Supavisor accepts per pool
            POOLER_MAX_CLIENT_CONN=100
            # Unique tenant identifier
            POOLER_TENANT_ID=1000
            # Pool size for internal metadata storage used by Supavisor
            # This is separate from client connections and used only by Supavisor itself
            POOLER_DB_POOL_SIZE=5
            # Docker socket location - this value will differ depending on your OS
            DOCKER_SOCKET_LOCATION=/var/run/docker.sock
                                      """
            )
        )
        self.add_text(
            textwrap.dedent(
                """
            ############
            # API Proxy - Configuration for the Kong Reverse proxy.
            ############
            KONG_HTTP_PORT=8000
            KONG_HTTPS_PORT=8443
                                      """
            )
        )
        self.add_text(
            textwrap.dedent(
                """
            ############
            # API - Configuration for PostgesQL.
            ############
            PGRST_DB_SCHEMAS=public,storage,graphql_public
                                      """
            )
        )
        self.add_text(
            textwrap.dedent(
                """
            ############
            # Studio - Configuration for the Dashboard
            ############

            STUDIO_DEFAULT_ORGANIZATION=Default Organization
            STUDIO_DEFAULT_PROJECT=Default Project

            STUDIO_PORT=3000

            # Enable webp support
            IMGPROXY_ENABLE_WEBP_DETECTION=true

            # Add your OpenAI API key to enable SQL Editor Assistant
            OPENAI_API_KEY=
            ############
            # Functions - Configuration for Functions
            ############
            # NOTE: VERIFY_JWT applies to all functions. Per-function VERIFY_JWT is not supported yet.
            FUNCTIONS_VERIFY_JWT=false

            ############
            # Auth - Configuration for the GoTrue authentication server.
            ############

            ## General
            SITE_URL=http://localhost:3000
            ADDITIONAL_REDIRECT_URLS=
            JWT_EXPIRY=3600
            DISABLE_SIGNUP=false
            API_EXTERNAL_URL=http://localhost:8000

            ## Mailer Config
            MAILER_URLPATHS_CONFIRMATION="/auth/v1/verify"
            MAILER_URLPATHS_INVITE="/auth/v1/verify"
            MAILER_URLPATHS_RECOVERY="/auth/v1/verify"
            MAILER_URLPATHS_EMAIL_CHANGE="/auth/v1/verify"

            ## Email auth
            ENABLE_EMAIL_SIGNUP=true
            ENABLE_EMAIL_AUTOCONFIRM=false
            SMTP_ADMIN_EMAIL=admin@example.com
            SMTP_HOST=supabase-mail
            SMTP_PORT=2500
            SMTP_USER=fake_mail_user
            SMTP_PASS=fake_mail_password
            SMTP_SENDER_NAME=fake_sender
            ENABLE_ANONYMOUS_USERS=false

            ## Phone auth
            ENABLE_PHONE_SIGNUP=true
            ENABLE_PHONE_AUTOCONFIRM=true
                                      """
            )
        )
        self.supabase_url = self.safe_prompt(
            "Replace if you plan to use supabase outside of localhost ",
            default="supabase.local.mydomain.com",
        )
        print(self.supabase_url)
        self.nginx_urls["SUPABASE_HOSTNAME"] = self.supabase_url
        self.add_line(
            "SUPABASE_PUBLIC_URL",
            f"https://{self.supabase_url}",
        )
        self.add_text(
            textwrap.dedent(
                """
            ############
            # Logs - Configuration for Analytics
            # Please refer to https://supabase.com/docs/reference/self-hosting-analytics/introduction
            ############

            # Change vector.toml sinks to reflect this change
            # these cannot be the same value
            """
            )
        )
        self.add_line(
            "LOGFLARE_PUBLIC_ACCESS_TOKEN", self.generate_random_sha_256_hash()
        )
        self.add_line(
            "LOGFLARE_PRIVATE_ACCESS_TOKEN", self.generate_random_sha_256_hash()
        )
        self.add_line("SECRET_KEY_BASE", self.create_32_char_hex_secret())
        self.add_line("VAULT_ENC_KEY", self.create_32_char_hex_secret())


def main():
    env_file_creator = EnvFileCreator(file_name=".env")
    env_file_creator.create_postgres_envs()
    env_file_creator.create_n8n_envs()
    env_file_creator.create_supabase_envs()
    env_file_creator.create_qdrant_envs()
    env_file_creator.write()
    env_file_creator.create_nginx_config()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)
