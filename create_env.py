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
        self.add_line(
            "N8N_VERSION",
            self.safe_prompt("Enter the value for N8N_VERSION: ", default="2.8.3"),
        )
        self.add_line(
            "N8N_TIMEZONE",
            self.safe_prompt(
                "Enter the appropriate timezone: ", default="America/Chicago"
            ),
        )
        self.add_line("N8N_ENCRYPTION_KEY", self.create_32_char_hex_secret())
        self.add_line("N8N_RUNNERS_AUTH_TOKEN", f'"{self.generate_password(16)}"')
        self.nginx_urls["N8N_HOSTNAME"] = self.n8n_hostname.strip("https://").strip("/")
        self.add_line("WEBHOOK_URL", f"https://{self.n8n_hostname}")
        self.add_line("N8N_EDITOR_BASE_URL", f"https://{self.n8n_hostname}")
        self.add_line("N8N_HOST", f'"{self.n8n_hostname}"')


def main():
    env_file_creator = EnvFileCreator(file_name=".env")
    env_file_creator.create_postgres_envs()
    env_file_creator.create_n8n_envs()
    env_file_creator.create_qdrant_envs()
    env_file_creator.write()
    env_file_creator.create_nginx_config()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)
